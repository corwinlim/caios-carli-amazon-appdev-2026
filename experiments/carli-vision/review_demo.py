"""Loopback-only, bearer-protected judge demo. One local demo parent, no production identity."""
import base64
from contextlib import contextmanager
from datetime import datetime,timezone
from http.server import HTTPServer,BaseHTTPRequestHandler
import hmac
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
from urllib.parse import urlparse,parse_qs
import uuid
import cv2
from run_video import run
from vision_cloud import canonical
import hashlib


@contextmanager
def database(path):
    db=sqlite3.connect(path,timeout=10)
    try:
        with db:yield db
    finally:db.close()


def create_server(address,root,token,aws_executor=None):
    if address[0]!='127.0.0.1' or not isinstance(token,str) or len(token)<12:
        raise ValueError('Loopback address and explicit demo token required')
    root=Path(root);root.mkdir(parents=True,exist_ok=True);db_path=root/'reviews.sqlite'
    with database(db_path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,event TEXT NOT NULL,record TEXT,cloud TEXT)')
    def load(event_id):
        try:
            if str(uuid.UUID(event_id))!=event_id:raise ValueError()
        except (ValueError,TypeError,AttributeError):raise ValueError('Invalid event ID') from None
        with database(db_path) as db:
            row=db.execute('SELECT event,record,cloud FROM events WHERE id=?',(event_id,)).fetchone()
        if row is None:raise ValueError('Event unavailable')
        return row
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,data,kind='application/json'):
            raw=json.dumps(data,allow_nan=False).encode() if kind=='application/json' else data
            self.send_response(status);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
        def authorized(self):
            host=self.headers.get('Host','')
            valid_hosts={'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)}
            if host not in valid_hosts:
                self.send(403,{'error':'Local host required'});return False
            if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+token):
                self.send(401,{'error':'Demo access token required'});return False
            origin=self.headers.get('Origin')
            if origin and origin not in {'http://'+host for host in valid_hosts}:
                self.send(403,{'error':'Local origin required'});return False
            return True
        def do_GET(self):
            path=urlparse(self.path).path
            if path=='/':return self.send(200,Path(__file__).with_name('review_demo.html').read_bytes(),'text/html; charset=utf-8')
            if not self.authorized():return
            if path=='/api/records':
                with database(db_path) as db:rows=db.execute('SELECT record FROM events WHERE record IS NOT NULL ORDER BY rowid').fetchall()
                return self.send(200,[json.loads(row[0]) for row in rows])
            if path=='/api/status':return self.send(200,{'mode':'local_demo','aws_configured':aws_executor is not None,'aws_verified':False,'opencv_version':cv2.__version__})
            return self.send(404,{'error':'Unknown endpoint'})
        def do_POST(self):
            if not self.authorized():return
            try:
                path=urlparse(self.path)
                size=int(self.headers.get('Content-Length','0'))
                limit=50*1024*1024 if path.path=='/api/analyse' else 4096
                if not 0<size<=limit:raise ValueError('Invalid body size')
                self.connection.settimeout(30);raw=self.rfile.read(size)
                if len(raw)!=size:raise ValueError('Incomplete body')
                if path.path=='/api/analyse':
                    query=parse_qs(path.query)
                    roi=tuple(int(v) for v in query['roi'][0].split(','))
                    event_id=str(uuid.uuid4());work=root/event_id;work.mkdir()
                    try:
                        video=work/'clip';video.write_bytes(raw);evidence=run(video,roi)
                        frames=[];capture=cv2.VideoCapture(str(video))
                        try:
                            samples=evidence['quality']['samples']
                            for i in sorted({0,len(samples)//2,len(samples)-1}):
                                capture.set(cv2.CAP_PROP_POS_FRAMES,i);ok,image=capture.read()
                                if not ok:continue
                                ratio=min(1,360/image.shape[1]);image=cv2.resize(image,(round(image.shape[1]*ratio),round(image.shape[0]*ratio)))
                                ok,jpeg=cv2.imencode('.jpg',image)
                                if ok:frames.append({'time_s':samples[i]['time_s'],'image':'data:image/jpeg;base64,'+base64.b64encode(jpeg).decode()})
                        finally:capture.release()
                        event={'event_id':event_id,'created_at':datetime.now(timezone.utc).isoformat(),
                               'evidence':evidence,'frames':frames,'scope':'uploaded_clip_only','aws_verified':False}
                        with database(db_path) as db:db.execute('INSERT INTO events VALUES(?,?,NULL,NULL)',(event_id,json.dumps(event)))
                    except Exception:
                        shutil.rmtree(work,ignore_errors=True);raise
                    return self.send(201,event)
                data=json.loads(raw)
                row=load(data['event_id']);event=json.loads(row[0])
                if path.path=='/api/aws':
                    if row[2] is not None:return self.send(200,json.loads(row[2]))
                    if aws_executor is None:return self.send(503,{'error':'AWS verification is not configured','aws_verified':False})
                    try:receipt=aws_executor(event['evidence'])
                    except Exception:return self.send(503,{'error':'AWS verification blocked; inspect account, role and deployment','aws_verified':False})
                    from vision_cloud import validate_result,make_request
                    validate_result(event['evidence'],receipt.get('result'))
                    if receipt.get('status')!='PASS' or not receipt.get('aws_request_id') or receipt.get('evidence_sha256')!=make_request(event['evidence'])['evidence_sha256']:
                        raise ValueError('Unverified AWS receipt')
                    with database(db_path) as db:db.execute('UPDATE events SET cloud=? WHERE id=?',(json.dumps(receipt),data['event_id']))
                    return self.send(200,receipt)
                if path.path=='/api/confirm':
                    decision=data['decision'];note=data.get('note','')
                    if decision not in ['reviewed','uncertain','rejected'] or not isinstance(note,str) or len(note)>500:
                        raise ValueError('Invalid review')
                    if event['evidence']['decision']['next_action']!='request_owner_review':
                        raise ValueError('This clip does not contain reviewable motion evidence')
                    with database(db_path) as db:
                        db.execute('BEGIN IMMEDIATE')
                        current=db.execute('SELECT record,cloud FROM events WHERE id=?',(data['event_id'],)).fetchone()
                        if current[0]:
                            record=json.loads(current[0])
                            if record['decision']!=decision or record['parent_note']!=note:
                                return self.send(409,{'error':'Review already recorded; an audited correction is required'})
                        else:
                            record={'schema':'carli-local-parent-review/1','event_id':data['event_id'],
                                    'source':'demo_parent_review','decision':decision,'parent_note':note,
                                    'reviewed_at':datetime.now(timezone.utc).isoformat(),
                                    'video_sha256':event['evidence']['video_sha256'],
                                    'evidence_sha256':hashlib.sha256(canonical(event['evidence'])).hexdigest(),
                                    'aws_receipt_available':current[1] is not None,'feeding_confirmed':False,
                                    'caios_written':False,'scope':'one_local_demo_parent'}
                            db.execute('UPDATE events SET record=? WHERE id=?',(json.dumps(record),data['event_id']))
                    return self.send(200,record)
                return self.send(404,{'error':'Unknown endpoint'})
            except (ValueError,KeyError,TypeError):return self.send(400,{'error':'Invalid video, region or review request','feeding_confirmed':False})
            except Exception:return self.send(500,{'error':'Processing failed; no feeding conclusion generated','feeding_confirmed':False})
    return HTTPServer(address,Handler)


def main():
    token=os.getenv('CARLI_DEMO_TOKEN') or secrets.token_urlsafe(32)
    executor=None
    config=[os.getenv(key) for key in ['CARLI_AWS_PROFILE','CARLI_AWS_ACCOUNT','CARLI_AWS_FUNCTION_ARN','CARLI_AWS_CODE_SHA256']]
    if any(config) and not all(config):raise ValueError('Complete all four AWS settings, or omit all for local-only mode')
    if all(config):
        def executor(evidence):
            import boto3
            from botocore.config import Config
            from aws_vision_proof import collect
            region=config[2].split(':')[3]
            session=boto3.Session(profile_name=config[0],region_name=region)
            bounds=Config(connect_timeout=5,read_timeout=20,retries={'max_attempts':0})
            with session.client('sts',config=bounds) as sts,session.client('lambda',config=bounds) as lam:
                return collect(evidence,config[1],config[2],config[3],sts,lam)
    server=create_server(('127.0.0.1',int(os.getenv('PORT','8080'))),os.getenv('CARLI_DEMO_DATA','evidence/review-demo'),token,executor)
    print('Open http://127.0.0.1:'+str(server.server_port),flush=True)
    print('Local demo access token: '+token,flush=True)
    print('Local prototype only. AWS is verified per clip, never by configuration alone.',flush=True)
    server.serve_forever()

if __name__=='__main__':main()
