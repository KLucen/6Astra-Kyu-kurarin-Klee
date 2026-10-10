import cv2,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());sift=cv2.SIFT_create(nfeatures=1200,contrastThreshold=.028);bf=cv2.BFMatcher()
refs={'profile':1173,'cheeks_closed':1408,'cheeks_open':3555,'face_covered':3748,'bed_sleep':2493,'bed_sleep_late':4096,'bed_sit':4544,'head_down':4712,'flower_hands':4760,'hug_open':5784,'hug_closed':6039,'crying':5573,'clock_hand':120}
bank={}
for name,i in refs.items():
    p=R/'refs'/f'source-f{i:05d}.png';im=cv2.imread(str(p));g=cv2.cvtColor(cv2.resize(im,(640,360)),cv2.COLOR_BGR2GRAY);mask=np.zeros(g.shape,np.uint8);mask[:,:460]=255;kp,d=sift.detectAndCompute(g,mask);bank[name]=(np.float32([k.pt for k in kp]),d)
cap=cv2.VideoCapture(M['source']);rows=[]
for i in range(M['frames']):
    ok,im=cap.read()
    if not ok:raise RuntimeError(i)
    if 128<=i<1152 or 2912<=i<3424:rows.append({'frame':i,'family':'body','status':'known_interval'});continue
    gray=cv2.cvtColor(cv2.resize(im,(640,360)),cv2.COLOR_BGR2GRAY)
    # Horizontal/vertical inversion here is solely an analysis of the source's actual upside-down scene.
    upside=5290<=i<5550
    if upside:gray=cv2.flip(gray,-1)
    kp,d=sift.detectAndCompute(gray,None);best=None
    if d is not None and len(kp)>15:
        for name,(pts,td) in bank.items():
            good=[m for m,n in bf.knnMatch(td,d,k=2) if m.distance<.7*n.distance and m.distance<230]
            if len(good)<8:continue
            a=np.float32([pts[m.queryIdx] for m in good]);b=np.float32([kp[m.trainIdx].pt for m in good]);A,ins=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=1.1,maxIters=500)
            if A is None:continue
            count=int(ins.sum());scale=float(np.hypot(A[0,0],A[1,0]));angle=float(np.degrees(np.arctan2(A[1,0],A[0,0])))
            if count<8 or not .2<scale<3:continue
            if best is None or count>best['inliers']:
                AA=A.copy();AA[:,2]*=3;best={'frame':i,'family':name,'inliers':count,'affine':AA.tolist(),'scale':scale,'angle':angle,'upside_analysis':upside}
    rows.append(best or {'frame':i,'family':'unclassified','status':'needs_review'})
    if i%500==0:print('classified',i,flush=True)
cap.release();(R/'analysis/scene_classification_proposal.json').write_text(json.dumps({'references':refs,'rows':rows},indent=2));print('done')
