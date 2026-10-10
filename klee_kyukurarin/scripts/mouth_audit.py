import cv2,json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());T=json.loads((R/'analysis/scene_tracks.json').read_text())['rows'];cap=cv2.VideoCapture(M['source']);rows=[]
for i in range(1888):
    ok,im=cap.read()
    if i<1408 or i%8:continue
    row=T[i]
    if not row.get('present') or 'affine' not in row:continue
    A=np.float32(row['affine']);inv=cv2.invertAffineTransform(A);im2=cv2.warpAffine(im,inv,(1920,1080));crop=im2[300:650,550:1150];rows.append((i,Image.fromarray(cv2.cvtColor(crop,cv2.COLOR_BGR2RGB))))
    if i in [1496,1504,1536,1568,1664]:cv2.imwrite(str(R/'refs'/f'source-f{i:05d}.png'),im)
cap.release()
for pg in range((len(rows)+23)//24):
    s=Image.new('RGB',(1600,1550),'white');d=ImageDraw.Draw(s)
    for k,(i,im) in enumerate(rows[pg*24:(pg+1)*24]):
        im=im.copy();im.thumbnail((398,226));x=k%4*400;y=k//4*255;s.paste(im,(x,y+25));d.text((x+5,y+4),str(i),fill='black')
    s.save(R/'analysis'/f'mouth-audit-{pg+1}.jpg')
print('mouth audit',len(rows))
