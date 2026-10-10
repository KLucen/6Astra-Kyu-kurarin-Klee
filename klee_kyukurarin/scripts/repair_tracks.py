import cv2,json,numpy as np
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());D=json.loads((R/'analysis/scene_tracks.json').read_text());sift=cv2.SIFT_create(2000);bf=cv2.BFMatcher()
def align(a,b):
    a=cv2.resize(a,(960,540));b=cv2.resize(b,(960,540));ka,da=sift.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None);kb,db=sift.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None);good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<.7*n.distance];aa=np.float32([ka[m.queryIdx].pt for m in good]);bb=np.float32([kb[m.trainIdx].pt for m in good]);A,ins=cv2.estimateAffinePartial2D(aa,bb,method=cv2.RANSAC,ransacReprojThreshold=1.5)
    A[:,2]*=2;return A
reg={}
for name,a,b in [('open',1408,3555),('covered',1408,3748),('rest',1408,1632),('hug_closed',5784,6039)]:
    A=align(cv2.imread(str(R/'refs'/f'source-f{a:05d}.png')),cv2.imread(str(R/'refs'/f'source-f{b:05d}.png')));reg[name]=A.tolist();print(name,A.tolist(),flush=True)
(R/'analysis/expression_reference_registration.json').write_text(json.dumps(reg,indent=2))
def green(im):
    rgb=cv2.resize(im,(480,270))[:,:,::-1].astype(int);g=(rgb[:,:,1]>rgb[:,:,0]+5)&(rgb[:,:,1]>=rgb[:,:,2]-7)&(rgb[:,:,0]<205);g[:,:4]=False;g[:,-4:]=False;return g
refs={k:cv2.imread(str(R/'refs'/f'source-f{n:05d}.png')) for k,n in D['references'].items()}
cap=cv2.VideoCapture(M['source']);changes=[];missing=[]
for i,row in enumerate(D['rows']):
    ok,im=cap.read()
    if not ok:raise RuntimeError(i)
    fam=row['family']
    if fam in ['blank','body','clock','flowers']:continue
    g=green(im)
    if g.sum()<80:
        if row.get('present'):changes.append(i)
        row['present']=False;row.pop('status',None);continue
    if 'affine' not in row and fam not in ['sleep','sleep_late']:
        base=green(refs[fam]);yy,xx=np.where(g);yb,xb=np.where(base)
        # Fit only the observed source silhouette. No invented motion or interpolation.
        x0,x1=np.percentile(xx,[2,98]);y0,y1=np.percentile(yy,[2,98]);a0,a1=np.percentile(xb,[2,98]);b0,b1=np.percentile(yb,[2,98]);scale=(y1-y0)/(b1-b0)
        dx=((x0+x1)/2-scale*(a0+a1)/2)*4;dy=((y0+y1)/2-scale*(b0+b1)/2)*4
        row.update(affine=[[float(scale),0,float(dx)],[0,float(scale),float(dy)]],scale=float(scale),status='source_silhouette_registration_needs_review');missing.append((i,fam,round(float(scale),3),round(float(dx),1),round(float(dy),1)))
        if len(missing)%5==1:cv2.imwrite(str(R/'refs'/f'source-f{i:05d}.png'),im)
cap.release();(R/'analysis/scene_tracks.json').write_text(json.dumps(D,indent=2));(R/'analysis/track-repairs.json').write_text(json.dumps({'border_false_positives_removed':changes,'silhouette_fallbacks':missing},indent=2));print('removed border-only false positives',len(changes));print('source silhouette fallbacks',missing)
