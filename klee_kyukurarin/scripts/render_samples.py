import cv2,json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
import composite_core as C
C.init_tracks();R=C.R;targets=set([120,130,138,178,185,2980,3080,3390,1173,1270,1408,1424,1456,1500,1536,1632,1664,1800,2100,2390,2493,2850,3500,3555,3748,3940,4000,4096,4208,4256,4384,4544,4700,4712,4736,4760,4850,5024,5133,5304,5336,5384,5480,5556,5573,5700,5784,5900,6039,6200,6272]);cap=cv2.VideoCapture(C.M['source']);rows=[];out=R/'output/scene-draft-stills';out.mkdir(exist_ok=True)
for i in range(C.M['frames']):
    ok,bgr=cap.read()
    if not ok:raise RuntimeError(i)
    if i not in targets:continue
    src=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB);dst=C.render(src,i);im=Image.fromarray(dst);im.save(out/f'f{i:05d}.png');rows.append((i,Image.fromarray(src),im))
cap.release()
for pg in range((len(rows)+7)//8):
    sheet=Image.new('RGB',(1600,2000),'white');d=ImageDraw.Draw(sheet)
    for k,(i,src,dst) in enumerate(rows[pg*8:(pg+1)*8]):
        y=k*250;d.text((5,y+3),f'f{i}  SOURCE | KLEE COMPOSITE DRAFT',fill='black')
        for col,im in enumerate([src,dst]):
            im=im.copy();im.thumbnail((796,224));sheet.paste(im,(col*800,y+25))
    sheet.save(R/'analysis'/f'composite-review-{pg+1}.jpg',quality=94)
(R/'analysis/sample-issues.json').write_text(json.dumps(C.ISSUES,indent=2));print('samples',len(rows),'issues',len(C.ISSUES))
