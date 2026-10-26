"""Generate labelled geometric fixtures, never pet footage or cloud proof."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=Path('demo-fixtures'))
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    y,x=np.indices((120,160));base=np.where((x//4+y//4)%2,190,70).astype(np.uint8)
    for mode in ['moving','static','dark','blurred']:
        path=args.out/('SYNTHETIC-'+mode+'.avi')
        writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(160,120))
        if not writer.isOpened():raise RuntimeError('Synthetic fixture codec unavailable')
        try:
            for i in range(20):
                frame=base.copy()
                if mode=='moving':frame[30:60,10+i*3:40+i*3]=250
                elif mode=='dark':frame[:]=0
                elif mode=='blurred':frame=cv2.GaussianBlur(frame,(31,31),12)
                writer.write(cv2.cvtColor(frame,cv2.COLOR_GRAY2BGR))
        finally:writer.release()
    (args.out/'README.txt').write_text('SYNTHETIC GEOMETRIC FIXTURES ONLY. Not animal footage, behaviour validation or AWS evidence.\n',encoding='utf-8')
    print(json.dumps({'synthetic':True,'directory':str(args.out),'opencv_version':cv2.__version__}))

if __name__=='__main__':main()
