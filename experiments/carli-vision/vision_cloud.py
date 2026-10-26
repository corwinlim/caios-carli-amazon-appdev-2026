"""Lambda-ready review router for measured OpenCV evidence. No pet-state mutation."""
import hashlib
import json
import math
import re


def canonical(value):
    try:
        return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    except (TypeError,ValueError):
        raise ValueError('Invalid JSON evidence') from None


def route(evidence):
    try:
        if evidence['schema']!='carli-vision-local-proposal/1' or not re.fullmatch(r'5\.\d+\.\d+(?:\..*)?',evidence['opencv_version']):
            raise ValueError('OpenCV 5 evidence required')
        if not re.fullmatch('[0-9a-f]{64}',evidence['video_sha256']):
            raise ValueError('Invalid video digest')
        counts=evidence['motion']; total=counts['frame_count']; moving=counts['motion_frames']
        if type(total) is not int or type(moving) is not int or not 2<=total<=7200 or not 0<=moving<total:
            raise ValueError('Invalid frame counts')
        samples=evidence['quality']['samples']
        if not isinstance(samples,list) or len(samples)!=total:
            raise ValueError('Missing measured quality samples')
        usable=0; previous=-1
        for sample in samples:
            t,b,s=(sample[k] for k in ['time_s','brightness','sharpness'])
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in [t,b,s]):
                raise ValueError('Invalid measurements')
            if not previous<t<60 or not 0<=b<=255 or s<0:
                raise ValueError('Invalid measurement bounds')
            previous=t
            usable+=35<=b<=240 and s>=25
        fraction=usable/total
        action='request_better_video' if fraction<.8 else ('request_owner_review' if moving else 'continue_observation')
        return action,fraction
    except (KeyError,TypeError,AttributeError):
        raise ValueError('Malformed measured evidence') from None


def make_request(evidence):
    route(evidence)
    return {'schema':'carli-vision-cloud-request/1','evidence':evidence,
            'evidence_sha256':hashlib.sha256(canonical(evidence)).hexdigest()}


def handler(event, context):
    if not isinstance(event,dict) or event.get('schema')!='carli-vision-cloud-request/1':
        raise ValueError('Invalid request schema')
    evidence=event.get('evidence')
    expected=make_request(evidence)
    if event.get('evidence_sha256')!=expected['evidence_sha256']:
        raise ValueError('Evidence digest mismatch')
    action,fraction=route(evidence)
    request_id=getattr(context,'aws_request_id',None)
    if not isinstance(request_id,str) or not request_id:
        raise ValueError('Invocation context required')
    result={'schema':'carli-vision-cloud-result/1','evidence_sha256':expected['evidence_sha256'],
            'video_sha256':evidence['video_sha256'],'lambda_request_id':request_id,
            'action':action,'usable_fraction':fraction,'review_state':'unconfirmed',
            'feeding_confirmed':False,'mutating_tool_invoked':False}
    print(json.dumps({'event':'carli_vision_routed','request_id':request_id,
                      'evidence_sha256':expected['evidence_sha256'],'action':action}))
    return result


def validate_result(evidence,result):
    expected=make_request(evidence);action,fraction=route(evidence)
    if not isinstance(result,dict) or result.get('schema')!='carli-vision-cloud-result/1':
        raise ValueError('Invalid result schema')
    if (result.get('evidence_sha256')!=expected['evidence_sha256'] or
        result.get('video_sha256')!=evidence['video_sha256'] or result.get('action')!=action or
        result.get('feeding_confirmed') is not False or result.get('mutating_tool_invoked') is not False or
        result.get('usable_fraction')!=fraction or result.get('review_state')!='unconfirmed' or
        not isinstance(result.get('lambda_request_id'),str) or not result['lambda_request_id']):
        raise ValueError('Cloud result does not match measured evidence')
