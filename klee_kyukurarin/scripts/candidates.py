import cv2,json,numpy as np,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());cap=cv2.VideoCapture(M['source'])
out=R/'analysis/candidates';out.mkdir(exist_ok=True)
last=None; candidates=[];features=[];metrics=[]
for i in range(M['frames']):
    ok,bgr=cap.read()
    if not ok: raise RuntimeError(i)
    rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
    sm=cv2.resize(rgb,(480,270),interpolation=cv2.INTER_AREA)
    sm=cv2.GaussianBlur(sm,(3,3),0)
    # Suppress near-white independent lyrics and constant pink background in difference proposals.
    fg=(sm[:,:,1].astype(int)-sm[:,:,0].astype(int)>-45)&(sm.min(axis=2)<200)
    sm[~fg]=[248,192,215]
    delta=0 if last is None else np.abs(sm.astype(float)-last).mean()
    changed=1 if last is None else float((np.abs(sm.astype(float)-last).max(axis=2)>25).mean())
    if last is None or (delta>0.55 and changed>0.003):
        p=out/f'f{i:05d}.png';Image.fromarray(rgb).save(p)
        candidates.append({'frame':i,'pts_tick':M['pts_ticks'][i],'seconds':M['pts_ticks'][i]/16000,'file':p.relative_to(R).as_posix(),'difference_mean':delta,'changed_fraction':changed,'status':'candidate_not_semantically_verified'})
        features.append(sm);last=sm.astype(float)
    metrics.append([i,delta,changed])
cap.release()
for j,c in enumerate(candidates):c['end_frame']=candidates[j+1]['frame'] if j+1<len(candidates) else M['frames']
(R/'analysis/candidates.json').write_text(json.dumps(candidates,indent=2))
np.savez_compressed(R/'analysis/candidate_features.npz',features=np.array(features));np.save(R/'analysis/candidate_metrics.npy',metrics)
for page in range((len(candidates)+39)//40):
    sheet=Image.new('RGB',(1600,1040),'#eeeeee');d=ImageDraw.Draw(sheet)
    for k,c in enumerate(candidates[page*40:(page+1)*40]):
        x=k%5*320;y=k//5*130;im=Image.open(R/c['file']);im.thumbnail((316,108));sheet.paste(im,(x,y+20));d.text((x+4,y+3),f"#{page*40+k} f{c['frame']} {c['seconds']:.2f}s",fill='black')
    sheet.save(R/'analysis'/f'candidates-{page+1:02d}.jpg',quality=92)
print(json.dumps({'candidates':len(candidates),'note':'Proposals only, not independent cel count'}))
