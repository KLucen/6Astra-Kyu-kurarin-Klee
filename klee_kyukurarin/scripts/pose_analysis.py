import cv2,numpy as np,json
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];C=json.loads((R/'analysis/candidates.json').read_text());by={c['frame']:R/c['file'] for c in C}
ids=[130,138,146,154,162,170,178,185]
S=Image.new('RGB',(1920,2320),'white');D=ImageDraw.Draw(S)
for j,i in enumerate(ids):
    im=Image.open(by[i]);im.thumbnail((960,540));x=j%2*960;y=j//2*580;S.paste(im,(x,y+30));D.text((x+8,y+8),f'frame {i}',fill='black')
S.save(R/'analysis/pose-atlas.jpg',quality=95)
print(ids)
