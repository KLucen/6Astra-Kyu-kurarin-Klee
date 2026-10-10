import json,cv2,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
C=json.loads((R/'analysis/candidates.json').read_text());F=np.load(R/'analysis/candidate_features.npz')['features']
reps=[];groups=[];mappings=[]
for k,sm in enumerate(F):
    fg=np.max(np.abs(sm.astype(int)-np.array([248,192,215])),axis=2)>32
    n,lab,stats,cents=cv2.connectedComponentsWithStats(fg.astype('uint8'))
    fg=np.isin(lab, np.where(stats[:,cv2.CC_STAT_AREA]>30)[0][1:]).astype('uint8')
    ys,xs=np.where(fg)
    if len(xs)==0: box=[0,0,480,270]
    else: box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    x0,y0,x1,y1=box;crop=sm[y0:y1,x0:x1].copy()
    z=cv2.resize(crop,(128,128),interpolation=cv2.INTER_AREA).astype(float)
    if len(reps):
        dist=np.mean(np.abs(np.array(reps)-z),axis=(1,2,3));gid=int(np.argmin(dist));dd=float(dist[gid])
    else:gid=0;dd=1e9
    if dd>5:
        gid=len(reps);reps.append(z);groups.append({'id':gid,'representative':k,'members':[],'status':'visual_cluster_proposal_not_verified'})
    groups[gid]['members'].append(k)
    mappings.append({'candidate':k,'group':gid,'bbox_small':box,'distance':dd})
(R/'analysis/cluster_proposals.json').write_text(json.dumps({'groups':groups,'mappings':mappings},indent=2))
for page in range((len(groups)+29)//30):
    sheet=Image.new('RGB',(1600,1140),'#eeeeee');d=ImageDraw.Draw(sheet)
    for slot,g in enumerate(groups[page*30:(page+1)*30]):
        c=C[g['representative']];im=Image.open(R/c['file']);im.thumbnail((316,170));x=slot%5*320;y=slot//5*190;sheet.paste(im,(x,y+20));d.text((x+4,y+3),f"g{g['id']} f{c['frame']} n{len(g['members'])}",fill='black')
    sheet.save(R/'analysis'/f'groups-{page+1:02d}.jpg',quality=93)
print(json.dumps({'groups':len(groups),'candidates':len(C),'note':'Not semantic deduplication; full resolution validation still required'}))
