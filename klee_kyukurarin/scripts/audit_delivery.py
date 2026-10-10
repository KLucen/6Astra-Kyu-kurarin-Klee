"""Supplemental encoded-pixel review aids; these do not grant artistic acceptance."""
import cv2,json,subprocess,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());SC=json.loads((R/'analysis/scene_tracks.json').read_text())['rows']
cv2.setNumThreads(1);video=R/'output/Klee_Kyu-kurarin_DRAFT_v2.mp4';cap=cv2.VideoCapture(str(video));src=cv2.VideoCapture(M['source'])
suspects=[];color_samples=[];rows=[];total=0
selected={120,130,178,1144,1145,1173,1432,1464,1496,1536,1632,1664,2493,2928,2933,2972,2975,3420,3423,3504,3520,3555,3748,4544,4760,5304,5556,5573,5784,5900,6039,6272}
for i in range(M['frames']):
    ok,im=cap.read();ok2,original=src.read()
    if not(ok and ok2):raise RuntimeError(i)
    fam=SC[i]['family'];rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB).astype(np.int16)
    if fam not in ['clock','sleep','sleep_late','sit']:
        green=(rgb[:,:,1]>rgb[:,:,0]+10)&(rgb[:,:,1]>rgb[:,:,2]+3)&(rgb[:,:,0]<205);green[:,:12]=False;green[:,-12:]=False;count=int(green.sum())
        if count>300:
            _,_,stats,_=cv2.connectedComponentsWithStats(green.astype('uint8'));largest=int(stats[1:,4].max()) if len(stats)>1 else 0
            if largest>100:suspects.append({'frame':i,'family':fam,'green_pixels':count,'largest_component':largest})
    if i%120==0:
        # The top-right source background patch is outside actors/lyrics in these sampled shots.
        a=im[20:80,1820:1880].astype(int);b=original[20:80,1820:1880].astype(int);color_samples.append({'frame':i,'mean_abs_rgb':float(np.mean(abs(a-b))),'p99_abs_rgb':float(np.percentile(abs(a-b),99))})
    if i in selected:
        rows.append((i,Image.fromarray(cv2.cvtColor(original,cv2.COLOR_BGR2RGB)),Image.fromarray(rgb.astype('uint8'))))
    total+=1
cap.release();src.release()
for pg in range((len(rows)+7)//8):
    sheet=Image.new('RGB',(1600,2000),'white');d=ImageDraw.Draw(sheet)
    for j,(i,a,b) in enumerate(rows[pg*8:(pg+1)*8]):
        y=j*250;d.text((5,y),f'f{i} SOURCE | ENCODED KLEE v2',fill='black')
        for k,im in enumerate([a,b]):im=im.copy();im.thumbnail((795,224));sheet.paste(im,(k*800,y+24))
    sheet.save(R/'analysis'/f'encoded-v2-review-{pg+1}.jpg',quality=95)
v=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',str(video)]))['streams'][0]
attrs=['sample_aspect_ratio','display_aspect_ratio','color_range','color_space','color_transfer','color_primaries','pix_fmt'];source_video=next(s for s in M['streams'] if s['codec_type']=='video')
report={'decoded_frames':total,'display_attributes':{k:{'source':source_video.get(k),'output':v.get(k),'equal':source_video.get(k)==v.get(k)} for k in attrs},'possible_original_character_residue':suspects,'sampled_background_color_error':color_samples,'contact_sheets':(len(rows)+7)//8,'artistic_review':'Static frames and timing tables inspected; full original-speed playback not viewed.'}
(R/'analysis/delivery-pixel-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({'frames':total,'green_residue_suspects':len(suspects),'display_attributes_match':all(q['equal'] for q in report['display_attributes'].values())}),flush=True)
