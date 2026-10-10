import cv2,numpy as np,json
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];C=json.loads((R/'analysis/candidates.json').read_text());M=json.loads((R/'analysis/source_meta.json').read_text());ids=[130,138,146,154,162,170,178]
srcs=[cv2.imread(str(R/'analysis/candidates'/f'f{i:05d}.png')) for i in ids]
sift=cv2.SIFT_create(nfeatures=2000,contrastThreshold=.025);bf=cv2.BFMatcher();templates=[];diag=[]
for k,src in enumerate(srcs):
    gray=cv2.cvtColor(src,cv2.COLOR_BGR2GRAY)
    if k==0:
        bg=np.median(src[:150,:600],axis=(0,1));diff=np.max(abs(src.astype(float)-bg),axis=2)>25
    else:
        a=cv2.cvtColor(srcs[k-1],cv2.COLOR_BGR2GRAY);ka,da=sift.detectAndCompute(a,None);kb,db=sift.detectAndCompute(gray,None)
        good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<.65*n.distance]
        aff,ins=cv2.estimateAffinePartial2D(np.float32([ka[m.queryIdx].pt for m in good]),np.float32([kb[m.trainIdx].pt for m in good]),method=cv2.RANSAC,ransacReprojThreshold=2)
        prev=cv2.warpAffine(srcs[k-1],aff,(1920,1080),borderMode=cv2.BORDER_REPLICATE)
        diff=np.max(abs(src.astype(float)-prev),axis=2)>35
        diag.append({'from':ids[k-1],'to':ids[k],'affine':aff.tolist(),'matches':len(good),'inliers':int(ins.sum())})
    mask=(diff*255).astype('uint8');mask[:,:650]=0;mask[:,1320:]=0;mask[:10]=0;mask[-10:]=0
    mask=cv2.dilate(mask,np.ones((7,7),np.uint8));
    small=cv2.resize(gray,(960,540));ms=cv2.resize(mask,(960,540),interpolation=cv2.INTER_NEAREST)
    kp,des=sift.detectAndCompute(small,ms);pts=np.float32([p.pt for p in kp])
    if k:
        prevsmall=cv2.resize(cv2.cvtColor(srcs[k-1],cv2.COLOR_BGR2GRAY),(960,540))
        oldkp,olddes=sift.detectAndCompute(prevsmall,None)
        matches=bf.match(des,olddes)
        keep=np.array([m.distance>135 for m in matches])
        pts=pts[keep];des=des[keep]
    templates.append((pts,des))
    cv2.imwrite(str(R/'analysis'/f'pose{k+1}-feature-mask.png'),mask)
    cv2.imwrite(str(R/'analysis'/f'pose{k+1}-features.jpg'),cv2.drawKeypoints(src,[cv2.KeyPoint(float(p[0]*2),float(p[1]*2),4) for p in pts],None,color=(0,0,255)))
(R/'analysis/source-layer-registration.json').write_text(json.dumps(diag,indent=2))
cap=cv2.VideoCapture(M['source']);tracks=[]
for i in range(M['frames']):
    ok,src=cap.read()
    if not ok:raise RuntimeError(i)
    if not(128<=i<1152 or 2912<=i<3420):continue
    gray=cv2.cvtColor(cv2.resize(src,(960,540)),cv2.COLOR_BGR2GRAY);kp,des=sift.detectAndCompute(gray,None)
    row={'frame':i,'layers':[]}
    if des is not None:
        for n,(pts,td) in enumerate(templates):
            good=[m for m,q in bf.knnMatch(td,des,k=2) if m.distance<.62*q.distance and m.distance<180]
            if len(good)<6:continue
            aa=np.float32([pts[m.queryIdx] for m in good]);bb=np.float32([kp[m.trainIdx].pt for m in good])
            aff,ins=cv2.estimateAffinePartial2D(aa,bb,method=cv2.RANSAC,ransacReprojThreshold=1.5,maxIters=1000)
            if aff is None or int(ins.sum())<6:continue
            scale=float(np.hypot(aff[0,0],aff[1,0]));rot=float(np.arctan2(aff[1,0],aff[0,0])*180/np.pi)
            if abs(scale-1)>.02 or abs(rot)>1:continue
            gooddelta=(bb-aa)[ins.ravel()>0];med=np.median(gooddelta,axis=0)*2;res=float(np.median(np.linalg.norm(gooddelta-med/2,axis=1))*2)
            if res>1.5:continue
            row['layers'].append({'pose':n+1,'translation':[float(x) for x in med],'inliers':int(ins.sum()),'median_error_px':res})
    tracks.append(row)
    if i%300==0:print(f'tracked through {i}',flush=True)
cap.release();(R/'analysis/body_tracks_proposal.json').write_text(json.dumps({'status':'source_feature_registration_proposal_requires_visual_verification','frames':tracks},indent=2));print('done',len(tracks),flush=True)
