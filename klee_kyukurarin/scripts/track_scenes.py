"""Source-only registration. No synthetic inbetweens or pose substitution."""
import cv2,json,numpy as np
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text())
S=.5;sift=cv2.SIFT_create(nfeatures=2200,contrastThreshold=.022);bf=cv2.BFMatcher()
refs={'profile':1173,'cheeks':1408,'rest':1632,'open':3555,'covered':3748,'sleep':2493,'sleep_late':4096,'sit':4544,'down':4712,'flowers':4760,'upside':5304,'cry':5573,'hug':5784,'hug_closed':6039,'clock':120}
rois={'clock':(580,320,1320,1080),'sleep':(1170,480,1430,670),'sleep_late':(1160,540,1430,740),'sit':(1000,240,1400,780),'hug':(690,10,1340,1080),'hug_closed':(590,10,1340,1080)}
bank={}
for name,n in refs.items():
    im=cv2.imread(str(R/'refs'/f'source-f{n:05d}.png'));g=cv2.cvtColor(cv2.resize(im,(960,540)),cv2.COLOR_BGR2GRAY);mask=np.zeros(g.shape,np.uint8)
    x0,y0,x1,y1=rois.get(name,(10,5,1380,1080))
    if name=='upside':x1=1710
    mask[y0//2:y1//2,x0//2:x1//2]=255;kp,d=sift.detectAndCompute(g,mask);bank[name]={'pts':np.float32([k.pt for k in kp]),'des':d,'gray':g}
def family(i):
    if 128<=i<1152 or 2912<=i<3424:return 'body'
    if 1152<=i<1408 or 4984<=i<5296:return 'profile'
    if 1408<=i<1888 or 3488<=i<3544:return 'cheeks'
    if 3544<=i<3736:return 'open'
    if 3736<=i<3992:return 'covered'
    if 2400<=i<2912:return 'sleep'
    if 3992<=i<4504:return 'sleep_late'
    if 4504<=i<4712:return 'sit'
    if 4712<=i<4760:return 'down'
    if 4760<=i<4984:return 'flowers'
    if 5296<=i<5552:return 'upside'
    if 5552<=i<5784:return 'cry'
    if 5784<=i<6039:return 'hug'
    if 6039<=i<6264:return 'hug_closed'
    if 64<=i<128 or 1888<=i<2400 or 6264<=i<6280:return 'clock'
    return 'blank'
def match(name,kp,d):
    td=bank[name]['des'];pts=bank[name]['pts']
    if d is None or td is None or len(d)<2:return None
    pairs=bf.knnMatch(td,d,k=2);good=[m for m,n in pairs if m.distance<.74*n.distance and m.distance<240]
    if len(good)<5:return None
    aa=np.float32([pts[m.queryIdx] for m in good]);bb=np.float32([kp[m.trainIdx].pt for m in good]);A,ins=cv2.estimateAffinePartial2D(aa,bb,method=cv2.RANSAC,ransacReprojThreshold=1.1,maxIters=1500)
    if A is None or int(ins.sum())<5:return None
    scale=float(np.hypot(A[0,0],A[1,0]));angle=float(np.degrees(np.arctan2(A[1,0],A[0,0])))
    if not .15<scale<4 or abs(angle)>12:return None
    A[:,2]*=2;err=float(np.median(np.linalg.norm((aa@A[:,:2].T+A[:,2]/2)-bb,axis=1)[ins.ravel()>0])*2)
    return {'affine':A.tolist(),'inliers':int(ins.sum()),'scale':scale,'angle':angle,'error':err}
cap=cv2.VideoCapture(M['source']);rows=[]
for i in range(M['frames']):
    ok,im=cap.read()
    if not ok:raise RuntimeError(i)
    name=family(i);row={'frame':i,'family':name}
    if name in ['blank','body']:rows.append(row);continue
    small=cv2.resize(im,(960,540));rgb=small[:,:,::-1].astype(np.int16)
    green=(rgb[:,:,1]>rgb[:,:,0]+5)&(rgb[:,:,1]>=rgb[:,:,2]-7)&(rgb[:,:,0]<205)
    if name in ['flowers']:
        fg=(np.max(abs(rgb-np.median(rgb[:50,:200],axis=(0,1))),axis=2)>20);present=int(fg.sum())>10000
    elif name=='clock':
        arm=(abs(rgb[:,:,0]-247)<18)&(abs(rgb[:,:,1]-176)<15)&(abs(rgb[:,:,2]-203)<18);arm[:350]=False;arm[:,:400]=False;present=int(arm.sum())>600
    else:present=int(green.sum())>300
    row['present']=present
    if not present:rows.append(row);continue
    kp,d=sift.detectAndCompute(cv2.cvtColor(small,cv2.COLOR_BGR2GRAY),None);m=match(name,kp,d)
    if m:row.update(m)
    else:row['status']='registration_missing'
    # The sleep family exposes only the dark hair crown; locate it directly.
    if name in ['sleep','sleep_late']:
        g=green.astype('uint8');g[:,:450]=0;g[:180]=0;nc,lab,stats,_=cv2.connectedComponentsWithStats(g)
        ids=[k for k in range(1,nc) if stats[k,4]>250]
        if ids:
            k=max(ids,key=lambda k:stats[k,4]);x,y,w,h,a=stats[k];row['hair_bbox']=[int(v*2) for v in [x,y,w,h]]
    # Discover repeated copies using one-to-many descriptors and translation voting.
    if name in ['profile','cheeks','open','covered','upside'] and m and .98<m['scale']<1.02:
        pts=bank[name]['pts'];td=bank[name]['des'];votes=[]
        for arr in bf.knnMatch(td,d,k=min(12,len(d))):
            for q in arr:
                if q.distance>110:continue
                delta=(np.array(kp[q.trainIdx].pt)-pts[q.queryIdx])*2
                if abs(delta[1]-m['affine'][1][2])<4:votes.append((float(delta[0]),float(delta[1]),q.queryIdx))
        hist=Counter(round(v[0]/4)*4 for v in votes);peaks=[]
        for x,n in hist.most_common():
            if n<6 or any(abs(x-p['translation'][0])<20 for p in peaks):continue
            vv=[v for v in votes if abs(v[0]-x)<4]
            if len(set(v[2] for v in vv))<6:continue
            dx,dy=np.median(np.array(vv)[:,:2],axis=0);peaks.append({'translation':[float(dx),float(dy)],'votes':len(vv)})
        row['copy_votes']=sorted(peaks,key=lambda q:q['translation'][0])
    rows.append(row)
    if i%500==0:print('source tracks',i,flush=True)
cap.release();out={'status':'source_registration_proposal','references':refs,'rows':rows};(R/'analysis/scene_tracks.json').write_text(json.dumps(out,indent=2));print(Counter(x['family'] for x in rows));print('missing',sum(x.get('status')=='registration_missing' for x in rows),flush=True)
