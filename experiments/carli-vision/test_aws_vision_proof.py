"""SDK-boundary unit tests with botocore Stubber; never AWS execution evidence."""
import base64
import io
import json
import unittest
import boto3
from botocore.stub import Stubber
from aws_vision_proof import collect
from test_vision_cloud import evidence
from vision_cloud import make_request

ACCOUNT='123456789012'
ARN='arn:aws:lambda:ap-southeast-1:'+ACCOUNT+':function:carli-opencv-review-staging:1'
CODE=base64.b64encode(b'x'*32).decode()


class AwsProofTests(unittest.TestCase):
    def setUp(self):
        session=boto3.Session(aws_access_key_id='test',aws_secret_access_key='test',region_name='ap-southeast-1')
        self.sts=session.client('sts');self.lam=session.client('lambda')
        self.addCleanup(self.sts.close);self.addCleanup(self.lam.close)
        self.s=Stubber(self.sts);self.l=Stubber(self.lam)
        self.s.activate();self.l.activate()
        self.addCleanup(self.s.deactivate);self.addCleanup(self.l.deactivate)
    def identity(self,account=ACCOUNT,root=False):
        arn='arn:aws:iam::'+account+':root' if root else 'arn:aws:sts::'+account+':assumed-role/CarliDev/test'
        self.s.add_response('get_caller_identity',{'Account':account,'Arn':arn,'UserId':'fixture'}, {})
    def config(self,code=CODE):
        self.l.add_response('get_function_configuration',{'FunctionArn':ARN,'Version':'1','Runtime':'python3.12',
            'Handler':'vision_cloud.handler','State':'Active','LastUpdateStatus':'Successful','CodeSha256':code}, {'FunctionName':ARN})
    def call(self):return collect(evidence(2),ACCOUNT,ARN,CODE,self.sts,self.lam)
    def test_root_identity_denied_before_any_lambda_call(self):
        self.identity(root=True)
        with self.assertRaises(PermissionError):self.call()
    def test_wrong_account_denied_before_any_lambda_call(self):
        self.identity(account='111111111111')
        with self.assertRaises(PermissionError):self.call()
    def test_changed_deployment_code_denied(self):
        self.identity();self.config(base64.b64encode(b'y'*32).decode())
        with self.assertRaises(ValueError):self.call()
    def invocation(self,include_log=True):
        ev=evidence(2);request=make_request(ev)
        result={'schema':'carli-vision-cloud-result/1','evidence_sha256':request['evidence_sha256'],
                'video_sha256':'a'*64,'lambda_request_id':'lambda-fixture-id','action':'request_owner_review',
                'usable_fraction':1.0,'review_state':'unconfirmed','feeding_confirmed':False,'mutating_tool_invoked':False}
        logs=json.dumps({'event':'carli_vision_routed','request_id':'lambda-fixture-id',
                         'evidence_sha256':request['evidence_sha256'],'action':'request_owner_review'}) if include_log else 'START only'
        self.l.add_response('invoke',{'StatusCode':200,'ExecutedVersion':'1',
            'Payload':io.BytesIO(json.dumps(result).encode()),'LogResult':base64.b64encode(logs.encode()).decode(),
            'ResponseMetadata':{'RequestId':'aws-transport-fixture-id'}},
            {'FunctionName':ARN,'InvocationType':'RequestResponse','LogType':'Tail','Payload':json.dumps(request).encode()})
    def test_valid_linked_sdk_response_is_accepted(self):
        self.identity();self.config();self.invocation()
        receipt=self.call()
        self.assertEqual(receipt['status'],'PASS')
        self.assertEqual(receipt['aws_request_id'],'aws-transport-fixture-id')
        self.assertEqual(receipt['result']['action'],'request_owner_review')
    def test_missing_correlated_log_denied(self):
        self.identity();self.config();self.invocation(False)
        with self.assertRaises(ValueError):self.call()
    def test_unversioned_function_denied_without_cloud_calls(self):
        with self.assertRaises(ValueError):collect(evidence(),ACCOUNT,ARN.rsplit(':',1)[0],CODE,self.sts,self.lam)


if __name__=='__main__':unittest.main()
