import cv2,json
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());cap=cv2.VideoCapture(M['source']);targets=set(range(3408,4801,32));targets.update([1408,1413,3544,3555,3736,3748,3968,4000,4096,4480,4544,4712,4728,4760,5784,6039]);rows=[]
for i in range(M['frames']):
    ok,bgr=cap.read()
    if not ok:raise RuntimeError(i)
    if i not in targets:continue
    im=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB));p=R/'refs'/f'source-f{i:05d}.png'
    if not p.exists():im.save(p)
    rows.append((i,im))
cap.release()
for pg in range((len(rows)+29)//30):
    s=Image.new('RGB',(1600,1140),'white');d=ImageDraw.Draw(s)
    for k,(i,im) in enumerate(rows[pg*30:(pg+1)*30]):
        im=im.copy();im.thumbnail((316,170));x=k%5*320;y=k//5*190;s.paste(im,(x,y+20));d.text((x+4,y+3),f'{i} {M["pts_ticks"][i]/16000:.2f}s',fill='black')
    s.save(R/'analysis'/f'scene-detail-{pg+1}.jpg',quality=93)
print('scene detail complete')
