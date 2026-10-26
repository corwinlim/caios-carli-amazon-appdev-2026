"""Invoke an existing, versioned staging Lambda and collect correlated proof.

No deployment, IAM change, pet-state write or automatic login. SDK unit stubs are
not live receipts. CLI writes a fresh run directory and preserves failed runs.
"""
import argparse
import base64
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import uuid
from vision_cloud import make_request,validate_result


def collect(evidence,expected_account,function_arn,expected_code_sha256,sts,lam):
    match=re.fullmatch(r'arn:aws:lambda:([a-z0-9-]+):(\d{12}):function:carli-opencv-review-staging:([1-9]\d*)',function_arn)
    if not match or match[2]!=expected_account:
        raise ValueError('Use the exact versioned CARLi staging function ARN in the approved account')
    if not re.fullmatch(r'[A-Za-z0-9+/]{43}=',expected_code_sha256):
        raise ValueError('Expected Lambda deployment CodeSha256 required')
    request=make_request(evidence)
    identity=sts.get_caller_identity()
    principal=identity.get('Arn','')
    if identity.get('Account')!=expected_account or not principal.startswith('arn:aws:sts::'+expected_account+':assumed-role/'):
        raise PermissionError('Approved account and assumed-role credentials required; no Root or IAM-user fallback')
    config=lam.get_function_configuration(FunctionName=function_arn)
    if (config.get('CodeSha256')!=expected_code_sha256 or config.get('Version')!=match[3] or
        config.get('FunctionArn')!=function_arn or config.get('State')!='Active' or
        config.get('LastUpdateStatus')!='Successful' or config.get('Runtime')!='python3.12' or
        config.get('Handler')!='vision_cloud.handler'):
        raise ValueError('Deployment configuration or code digest mismatch')
    response=lam.invoke(FunctionName=function_arn,InvocationType='RequestResponse',LogType='Tail',Payload=json.dumps(request).encode())
    payload=response.get('Payload')
    try:
        raw=payload.read() if payload is not None else b''
    finally:
        if payload is not None:payload.close()
    if response.get('StatusCode')!=200 or response.get('FunctionError') or response.get('ExecutedVersion')!=match[3]:
        raise ValueError('Lambda invocation failed or version mismatch')
    result=json.loads(raw);validate_result(evidence,result)
    logs=base64.b64decode(response.get('LogResult',''),validate=True).decode('utf-8')
    correlated=[]
    for line in logs.splitlines():
        try:item=json.loads(line)
        except ValueError:continue
        if (item.get('event')=='carli_vision_routed' and item.get('request_id')==result['lambda_request_id'] and
            item.get('evidence_sha256')==request['evidence_sha256'] and item.get('action')==result['action']):
            correlated.append(item)
    request_id=response.get('ResponseMetadata',{}).get('RequestId')
    if not correlated or not request_id:raise ValueError('Missing correlated AWS invocation/log evidence')
    return {'schema':'carli-opencv-aws-proof/1','status':'PASS','captured_at':datetime.now(timezone.utc).isoformat(),
            'account':expected_account,'caller_arn':principal,'function_arn':function_arn,
            'code_sha256':config['CodeSha256'],'aws_request_id':request_id,
            'evidence_sha256':request['evidence_sha256'],'result':result,'correlated_log_events':correlated,
            'feeding_confirmed':False,'pet_state_mutated':False,
            'scope':'AWS routing of submitted measurements, not independent image authentication or owner approval'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--function-arn',required=True)
    parser.add_argument('--code-sha256',required=True)
    parser.add_argument('--expected-account',required=True)
    parser.add_argument('--profile',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    # A new directory prevents stale PASS receipts from being mistaken for this run.
    directory=args.out/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    directory.mkdir(parents=True,exist_ok=False)
    try:
        import boto3
        from botocore.config import Config
        arn_match=re.fullmatch(r'arn:aws:lambda:([a-z0-9-]+):\d{12}:function:carli-opencv-review-staging:[1-9]\d*',args.function_arn)
        if not arn_match:raise ValueError('Versioned staging ARN required')
        session=boto3.Session(profile_name=args.profile,region_name=arn_match[1])
        config=Config(connect_timeout=5,read_timeout=20,retries={'max_attempts':0})
        with session.client('sts',config=config) as sts,session.client('lambda',config=config) as lam:
            evidence=json.loads(args.evidence.read_text(encoding='utf-8-sig'))
            receipt=collect(evidence,args.expected_account,args.function_arn,args.code_sha256,sts,lam)
        receipt['evidence_file_sha256']=hashlib.sha256(args.evidence.read_bytes()).hexdigest()
        (directory/'aws-proof.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        print(json.dumps({'status':'PASS','receipt':str(directory/'aws-proof.json')}))
        return 0
    except Exception as error:
        blocked={'status':'BLOCKED','aws_gate_passed':False,'error_type':type(error).__name__,
                 'deployment_performed':False,'instruction':'Inspect credentials, function availability and exact deployment digest; do not bypass account/role checks.'}
        (directory/'aws-proof.json').write_text(json.dumps(blocked,indent=2),encoding='utf-8')
        print(json.dumps(blocked));return 2

if __name__=='__main__':raise SystemExit(main())
