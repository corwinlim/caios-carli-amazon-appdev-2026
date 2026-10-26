import contextlib
import hashlib
import io
import json
import unittest
from types import SimpleNamespace
from vision_cloud import handler, make_request, validate_result


def evidence(motion=0, brightness=100, sharpness=100):
    return {'schema':'carli-vision-local-proposal/1','opencv_version':'5.0.0',
            'video_sha256':'a'*64,
            'motion':{'frame_count':3,'motion_frames':motion},
            'quality':{'samples':[{'time_s':i,'brightness':brightness,'sharpness':sharpness} for i in range(3)]}}


class CloudReviewTests(unittest.TestCase):
    def call(self, ev):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result=handler(make_request(ev),SimpleNamespace(aws_request_id='test-request'))
        return result,output.getvalue()
    def test_real_measurements_change_cloud_routing(self):
        cases=[(evidence(2),'request_owner_review'),(evidence(),'continue_observation'),
               (evidence(brightness=0),'request_better_video')]
        for ev,action in cases:
            with self.subTest(action=action):
                result,logs=self.call(ev)
                self.assertEqual(result['action'],action)
                self.assertEqual(result['lambda_request_id'],'test-request')
                self.assertFalse(result['feeding_confirmed'])
                self.assertFalse(result['mutating_tool_invoked'])
                self.assertEqual(json.loads(logs)['evidence_sha256'],result['evidence_sha256'])
                validate_result(ev,result)
    def test_client_claims_do_not_override_measurements(self):
        ev=evidence(brightness=0)
        ev['quality']['quality_ok']=True
        ev['decision']={'next_action':'feeding_confirmed'}
        self.assertEqual(self.call(ev)[0]['action'],'request_better_video')
    def test_nonfinite_or_nonchronological_samples_rejected(self):
        for value in [float('nan'),float('inf')]:
            ev=evidence();ev['quality']['samples'][0]['brightness']=value
            with self.assertRaises(ValueError):self.call(ev)
        ev=evidence();ev['quality']['samples'][1]['time_s']=0
        with self.assertRaises(ValueError):self.call(ev)
    def test_runtime_counts_and_digest_validated(self):
        for change in [{'opencv_version':'4.14.0'},{'video_sha256':'invalid'},
                       {'motion':{'frame_count':3,'motion_frames':3}}]:
            ev=evidence();ev.update(change)
            with self.assertRaises(ValueError):self.call(ev)
    def test_tampered_request_digest_rejected(self):
        request=make_request(evidence());request['evidence']['video_sha256']='b'*64
        with self.assertRaises(ValueError):handler(request,None)
    def test_response_cannot_claim_feeding_or_swap_evidence(self):
        ev=evidence(2);result,_=self.call(ev)
        for field,value in [('feeding_confirmed',True),('evidence_sha256','b'*64),
                            ('action','continue_observation')]:
            altered=dict(result);altered[field]=value
            with self.assertRaises(ValueError):validate_result(ev,altered)


if __name__=='__main__':unittest.main()
