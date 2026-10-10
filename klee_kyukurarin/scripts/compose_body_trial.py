import cv2,numpy as np,json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());tracks=json.loads((R/'analysis/body_tracks_proposal.json').read_text())['frames'];T={x['frame']:x['layers'] for x in tracks}
names=['anchor-f01027-v1','pose02-f00138-v2','pose03-f00146-v1','pose04-f00154-v2','pose05-f00162-v2','pose06-f00170-v1','pose07-f00178-v1'];layers=[]
for j,n in enumerate(names):
    im=Image.open(R/'generated'/f'{n}.png').convert('RGBA');a=np.array(im)
    if j==0:
        rgb=a[:,:,:3].astype(int);bg=(rgb[:,:,0]>210)&(rgb[:,:,1]>125)&(rgb[:,:,1]<220)&(rgb[:,:,2]>rgb[:,:,1]+6)&(rgb[:,:,0]>rgb[:,:,2]+10)
        ncomp,lab,stats,_=cv2.connectedComponentsWithStats(bg.astype('uint8'))
        ids=np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]]));ids=ids[ids>0];a[:,:,3][np.isin(lab,ids)]=0;a[:,:600,3]=0;a[:,1200:,3]=0
    layers.append(cv2.resize(a,(1920,1080),interpolation=cv2.INTER_LANCZOS4))
out=R/'output/body-loop-trial-frames';out.mkdir(exist_ok=True);cap=cv2.VideoCapture(M['source']);rows=[];issues=[]
for i in range(192):
    ok,bgr=cap.read()
    if not ok:raise RuntimeError(i)
    if i<128:continue
    src=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB);result=src.copy();phase=i-128;active=0 if phase>=60 else min(7,phase//8+1)
    use=[l for l in T[i] if l['pose']<=active]
    if phase<56 and phase%8==0:
        for z in use:
            if z['pose']==active and (abs(z['translation'][0])>20 or z['translation'][1]>-450):
                issues.append({'frame':i,'pose':active,'status':'entry_transform_pending_source_pixel_confirmation','measured_pattern_donor':128})
                z['translation']=[0,-578.2]
    for pid in range(1,active+1):
        if any(l['pose']==pid for l in use):continue
        # Only same cycle phase is eligible; no adjacent-pose filling.
        aliases=[(k,z) for k,ls in T.items() if 128<=k<1152 and (k-128)%64==phase for z in ls if z['pose']==pid]
        if aliases:
            donor,z=max(aliases,key=lambda q:q[1]['inliers']);use.append(z);issues.append({'frame':i,'pose':pid,'same_phase_donor':donor,'status':'needs_full_resolution_alias_review'})
        else:issues.append({'frame':i,'pose':pid,'status':'missing'});continue
    if active:
        bg=np.median(src[:,1800:1890],axis=1).astype('uint8')
        # This trial uses the original pink scene. Protect the right lyric/credit area.
        dist=np.max(abs(src.astype(float)-bg[:,None,:]),axis=2)
        fg=(dist>20).astype('uint8');fg[:,1390:]=0;fg[:,:8]=0
        nc,lab,stats,_=cv2.connectedComponentsWithStats(fg)
        ids=[k for k in range(1,nc) if stats[k,cv2.CC_STAT_AREA]>2500]
        old=cv2.dilate(np.isin(lab,ids).astype('uint8'),np.ones((7,7),np.uint8)).astype(bool)
        result[old]=np.broadcast_to(bg[:,None,:],src.shape)[old]
        for z in sorted(use,key=lambda z:z['pose']):
            dx,dy=z['translation'];rgba=cv2.warpAffine(layers[z['pose']-1],np.float32([[1,0,dx],[0,1,dy]]),(1920,1080),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
            alpha=rgba[:,:,3:4].astype(float)/255;result=np.round(result*(1-alpha)+rgba[:,:,:3]*alpha).astype('uint8')
    Image.fromarray(result).save(out/f'f{i:05d}.png')
    if phase in [0,1,2,8,9,10,16,18,24,26,32,34,40,42,48,50,56,57,58,59,60,63]:rows.append((i,src,result.copy()))
cap.release();(R/'analysis/body-loop-trial-issues.json').write_text(json.dumps(issues,indent=2))
for pg in range((len(rows)+5)//6):
    s=Image.new('RGB',(1600,1510),'white');d=ImageDraw.Draw(s)
    for k,(i,src,res) in enumerate(rows[pg*6:(pg+1)*6]):
        y=k*250;d.text((5,y+2),f'f{i} source / replacement TRIAL',fill='black')
        for col,arr in enumerate([src,res]):
            im=Image.fromarray(arr);im.thumbnail((796,224));s.paste(im,(col*800,y+23))
    s.save(R/'analysis'/f'body-trial-{pg+1}.jpg',quality=94)
print('Rendered 64 trial frames; unresolved',len(issues))
