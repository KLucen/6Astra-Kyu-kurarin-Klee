import cv2,json
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());cap=cv2.VideoCapture(M['source'])
targets=set(range(1632,1889,16))|set(range(3984,4513,16))|set(range(4712,4777,8))|set(range(5272,5569,16))|set(range(6256,6297,8));rows=[]
for i in range(M['frames']):
    ok,bgr=cap.read()
    if not ok:raise RuntimeError(i)
    if i not in targets:continue
    im=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB));p=R/'refs'/f'source-f{i:05d}.png'
    if not p.exists():im.save(p)
    rows.append((i,im))
cap.release()
for pg in range((len(rows)+23)//24):
    s=Image.new('RGB',(1600,1512),'white');d=ImageDraw.Draw(s)
    for k,(i,im) in enumerate(rows[pg*24:(pg+1)*24]):
        im=im.copy();im.thumbnail((398,224));x=k%4*400;y=k//4*252;s.paste(im,(x,y+25));d.text((x+5,y+4),str(i),fill='black')
    s.save(R/'analysis'/f'uncertain-{pg+1}.jpg',quality=94)
print('saved',len(rows))
