import cv2,json,numpy as np
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());D=json.loads((R/'analysis/scene_tracks.json').read_text());sift=cv2.SIFT_create(nfeatures=2500,contrastThreshold=.02);bf=cv2.BFMatcher();bank={}
for name,n in [('hug',5784),('hug_closed',6039),('upside',5304),('clock_bg',90)]:
    im=cv2.imread(str(R/'refs'/f'source-f{n:05d}.png'));g=cv2.cvtColor(cv2.resize(im,(960,540)),cv2.COLOR_BGR2GRAY);mask=np.zeros(g.shape,np.uint8);mask[:,:680 if name!='upside' else 880]=255;kp,d=sift.detectAndCompute(g,mask);bank[name]=(np.float32([p.pt for p in kp]),d)
cap=cv2.VideoCapture(M['source'])
for i,row in enumerate(D['rows']):
    ok,im=cap.read()
    if not ok:raise RuntimeError(i)
    if 5552<=i<5560:row['family']='upside';row.pop('status',None)
    fam=row['family']
    if not ((fam in ['hug','hug_closed'] and row.get('present')) or (fam=='clock' and row.get('present')) or 5552<=i<5560):continue
    name='clock_bg' if fam=='clock' else fam;pts,td=bank[name];g=cv2.cvtColor(cv2.resize(im,(960,540)),cv2.COLOR_BGR2GRAY);kp,d=sift.detectAndCompute(g,None)
    good=[m for m,n in bf.knnMatch(td,d,k=2) if m.distance<.72*n.distance and m.distance<235];aa=np.float32([pts[m.queryIdx] for m in good]);bb=np.float32([kp[m.trainIdx].pt for m in good]);A,ins=cv2.estimateAffinePartial2D(aa,bb,method=cv2.RANSAC,ransacReprojThreshold=1.1)
    if A is None:continue
    A[:,2]*=2
    if fam=='clock':row['clock_background_affine']=A.tolist();continue
    row['affine']=A.tolist();row['inliers']=int(ins.sum());votes=[]
    for arr in bf.knnMatch(td,d,k=min(12,len(d))):
        for q in arr:
            if q.distance>115:continue
            delta=(np.array(kp[q.trainIdx].pt)-pts[q.queryIdx])*2
            if abs(delta[1]-A[1,2])<5:votes.append((float(delta[0]),float(delta[1]),q.queryIdx))
    hist=Counter(round(v[0]/4)*4 for v in votes);peaks=[]
    for x,n in hist.most_common():
        if n<6 or any(abs(x-p['translation'][0])<20 for p in peaks):continue
        vv=[v for v in votes if abs(v[0]-x)<4]
        if len(set(v[2] for v in vv))<6:continue
        dx,dy=np.median(np.array(vv)[:,:2],axis=0);peaks.append({'translation':[float(dx),float(dy)],'votes':len(vv)})
    row['copy_votes']=sorted(peaks,key=lambda q:q['translation'][0])
cap.release();(R/'analysis/scene_tracks.json').write_text(json.dumps(D,indent=2));print('hug echo, upside boundary and clock background registrations saved')
