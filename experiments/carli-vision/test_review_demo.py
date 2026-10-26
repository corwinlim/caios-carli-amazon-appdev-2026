"""Real HTTP + encoded synthetic video + SQLite tests. No AWS or pet footage."""
import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from review_demo import create_server
import test_video_quality_routing as clip_fixtures


class ReviewDemoTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.clips=clip_fixtures.VideoQualityRoutingTests();self.clips.setUp();self.addCleanup(self.clips.doCleanups)
        self.server=create_server(('127.0.0.1',0),self.root,'test-demo-token')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stop)
        self.url='http://127.0.0.1:'+str(self.server.server_port)
    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
    def request(self,path,body=None,token='test-demo-token',raw=False,origin=None):
        headers={'Authorization':'Bearer '+token}
        if origin:headers['Origin']=origin
        if body is not None:
            headers['Content-Type']='application/octet-stream' if raw else 'application/json'
            body=body if raw else json.dumps(body).encode()
        req=urllib.request.Request(self.url+path,data=body,headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as r:return r.code,json.load(r)
    def upload(self,mode):
        status,event=self.request('/api/analyse?roi=0,0,160,120',self.clips.clip(mode).read_bytes(),raw=True)
        self.assertEqual(status,201);return event
    def test_unauthenticated_export_denied(self):
        self.assertEqual(self.request('/api/records',token='wrong')[0],401)
    def test_video_review_confirm_export_and_idempotency(self):
        event=self.upload('moving')
        self.assertEqual(event['evidence']['decision']['next_action'],'request_owner_review')
        self.assertEqual(self.request('/api/records')[1],[])
        body={'event_id':event['event_id'],'decision':'reviewed','note':'Synthetic movement reviewed; feeding unknown.'}
        code,record=self.request('/api/confirm',body)
        self.assertEqual(code,200);self.assertFalse(record['feeding_confirmed'])
        self.assertEqual(record['source'],'demo_parent_review')
        self.assertEqual(self.request('/api/confirm',body)[1],record)
        self.assertEqual(len(self.request('/api/records')[1]),1)
        self.assertEqual(self.request('/api/confirm',dict(body,decision='uncertain'))[0],409)
    def test_dark_video_cannot_be_approved(self):
        event=self.upload('dark')
        self.assertEqual(self.request('/api/confirm',{'event_id':event['event_id'],'decision':'reviewed','note':'x'})[0],400)
        self.assertEqual(self.request('/api/records')[1],[])
    def test_unconfigured_aws_is_explicitly_blocked(self):
        event=self.upload('moving')
        code,result=self.request('/api/aws',{'event_id':event['event_id']})
        self.assertEqual(code,503);self.assertFalse(result['aws_verified'])
    def test_cross_origin_mutation_denied(self):
        code,_=self.request('/api/confirm',{},origin='https://untrusted.example')
        self.assertEqual(code,403)
    def test_invalid_upload_and_missing_event_do_not_create_records(self):
        self.assertEqual(self.request('/api/analyse?roi=0,0,160,120',b'not a video',raw=True)[0],400)
        self.assertEqual(self.request('/api/confirm',{'event_id':'../other','decision':'reviewed','note':'x'})[0],400)
        self.assertEqual(self.request('/api/records')[1],[])


if __name__=='__main__':unittest.main()
