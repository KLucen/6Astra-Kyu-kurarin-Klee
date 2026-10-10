import cv2, json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'analysis/source_meta.json').read_text(encoding='utf-8'))
ticks=meta['pts_ticks']
targets={min(range(len(ticks)),key=lambda i:abs(ticks[i]/16000-t)) for t in range(0,216,5)}
targets.update([0,10,30,60,90,120])
cap=cv2.VideoCapture(meta['source'])
rows=[]
for i in range(len(ticks)):
    ok,fr=cap.read()
    if not ok: raise RuntimeError(i)
    if i in targets:
        p=ROOT/'refs'/f'source-f{i:05d}.png'
        im=Image.fromarray(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB));im.save(p)
        rows.append((i,ticks[i]/16000,im.copy(),p))
cap.release()
for page in range((len(rows)+19)//20):
    sheet=Image.new('RGB',(1600,1020),'#eeeeee');d=ImageDraw.Draw(sheet)
    for k,(i,t,im,p) in enumerate(rows[page*20:(page+1)*20]):
        x=k%4*400;y=k//4*204
        im.thumbnail((396,176));sheet.paste(im,(x,y+24));d.text((x+6,y+5),f'f{i} | {t:.3f}s',fill='black')
    sheet.save(ROOT/'analysis'/f'overview-{page+1}.jpg',quality=93)
assets=json.loads((ROOT/'assets.json').read_text())
for i,t,im,p in rows:
    assets['assets'].append({'path':p.relative_to(ROOT).as_posix(),'role':'source_reference','source_frame':i,'pts_tick':ticks[i],'size':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'review':'not_recorded'})
(ROOT/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(rows)} full-resolution references, {(len(rows)+19)//20} overview sheets')
