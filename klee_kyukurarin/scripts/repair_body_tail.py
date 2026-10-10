"""Reject matches onto the center phone cel when tracking the upper row of source cels."""
import cv2,numpy as np,json
from pathlib import Path
cv2.setNumThreads(1)
R=Path(__file__).resolve().parents[1]
# Reuse the exact source-derived feature definitions from the initial tracker.
prefix=(R/'scripts/track_body.py').read_text().split('cap=cv2.VideoCapture')[0]
exec(compile(prefix,str(R/'scripts/track_body.py'),'exec'))
p=R/'analysis/body_tracks_proposal.json';D=json.loads(p.read_text());BC={x['frame']:x for x in D['frames']}
cap=cv2.VideoCapture(M['source']);changed=[];missing=[]
for i in range(3424):
    ok,src=cap.read()
    if i<2912:continue
    phase=(i-2912)%64;active=min(7,phase//8+1)
    row=BC.setdefault(i,{'frame':i,'layers':[]})
    targets=[pid for pid in range(1,active+1) if pid!=2 and (phase>=60 or any(z['pose']==pid and z['translation'][1]>-350 for z in row['layers']))]
    if not targets:continue
    gray=cv2.cvtColor(cv2.resize(src,(960,540)),cv2.COLOR_BGR2GRAY);kp,des=sift.detectAndCompute(gray,None)
    if des is None:continue
    for pid in targets:
        pts,td=templates[pid-1];good=[]
        for arr in bf.knnMatch(td,des,k=min(6,len(des))):
            valid=[q for q in arr if -580<(kp[q.trainIdx].pt[1]-pts[q.queryIdx][1])*2<-400 and q.distance<170]
            if valid:good.append(valid[0])
        if len(good)<4:missing.append([i,pid]);continue
        aa=np.float32([pts[q.queryIdx] for q in good]);bb=np.float32([kp[q.trainIdx].pt for q in good]);delta=(bb-aa)*2
        best=max(delta,key=lambda d:np.count_nonzero(np.linalg.norm(delta-d,axis=1)<2.5));inliers=np.linalg.norm(delta-best,axis=1)<2.5
        if inliers.sum()<4:missing.append([i,pid]);continue
        med=np.median(delta[inliers],axis=0);z={'pose':pid,'translation':med.tolist(),'inliers':int(inliers.sum()),'median_error_px':float(np.median(np.linalg.norm(delta[inliers]-med,axis=1))),'repair':'source_matching_restricted_to_observed_upper_row'}
        row['layers']=[q for q in row['layers'] if q['pose']!=pid]+[z];changed.append([i,pid])
cap.release();D['frames']=sorted(BC.values(),key=lambda q:q['frame']);p.write_text(json.dumps(D,indent=2));(R/'analysis/body-tail-registration-repair.json').write_text(json.dumps({'changed':changed,'not_matched':missing},indent=2));print('source matched repairs',len(changed),'unmatched',missing,flush=True)
