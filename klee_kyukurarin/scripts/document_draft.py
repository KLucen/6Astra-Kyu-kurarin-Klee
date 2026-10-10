"""Record actual draft asset usage and reconcile reference metadata without erasing history."""
import json,hashlib,cv2,re
from pathlib import Path
from collections import defaultdict
from PIL import Image
import composite_core as C
cv2.setNumThreads(1);C.init_tracks();R=C.R
registry=json.loads((R/'assets.json').read_text());by_path={x['path']:x for x in registry['assets']}
changes=[]
paths=set(by_path)
for jobfile in (R/'jobs').glob('*.json'):
    job=json.loads(jobfile.read_text(encoding='utf-8-sig'))
    paths.update(x['path'] for x in job.get('references',[]) if 'path' in x)
for path in sorted(paths):
    f=R/path
    if not f.is_file():continue
    digest=hashlib.sha256(f.read_bytes()).hexdigest()
    try:
        with Image.open(f) as im:size=list(im.size);mode=im.mode
    except Exception:continue
    item=by_path.get(path)
    if item is None:
        item={'path':path,'role':'source_reference' if re.search(r'source-f\d+',path) else 'derived_reference','status':'reference_only'}
        match=re.search(r'source-f(\d+)',path)
        if match:item['source_frame']=int(match[1])
        registry['assets'].append(item);by_path[path]=item
    if item.get('sha256') and (item['sha256']!=digest or item.get('size')!=size):
        old={k:item.get(k) for k in ['sha256','size','mode']}
        item.setdefault('metadata_history',[]).append({'superseded_metadata':old,'reason':'Reconciled current full-resolution source reference after earlier extraction replaced overview-sized file.'})
        changes.append({'path':path,'previous':old,'current_size':size,'current_sha256':digest})
    item.update(sha256=digest,size=size,mode=mode)

uses=defaultdict(list);frames=[];cap=cv2.VideoCapture(C.M['source'])
names={**C.ASSETS,'upside':'upside-cry-upright-f05304-v2','mouth_o':'cheeks-mouth-o-f01504-v1','mouth_tiny':'cheeks-mouth-tiny-f01496-v1','mouth_teeth':'cheeks-mouth-teeth-f01432-v1'}
for i,row in enumerate(C.SC):
    ok,bgr=cap.read()
    if not ok:raise RuntimeError(i)
    fam=row['family'];layers=[]
    if fam=='body':layers=[(C.BODY[pid-1],A.tolist()) for pid,A in C.body_layers(i)]
    elif fam!='blank' and row.get('present'):
        if fam in ['sleep','sleep_late']:
            if row.get('hair_bbox'):layers=[(names['sleep'],{'source_hair_bbox':row['hair_bbox']})]
        elif fam in ['sit','clock']:layers=[(names[fam],C.get_A(row).tolist())]
        else:layers=[(names[name],A.tolist()) for name,A in C.scene_layers(row,cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))]
    frames.append({'frame':i,'pts_tick':C.M['pts_ticks'][i],'family':fam,'layers':[{'asset':name,'source_registration':A} for name,A in layers]})
    for name in set(n for n,a in layers):uses[name].append(i)
cap.release()
rejected={'pose02-f00138-v1':'Wrong standing-leg direction; superseded by v2.','pose04-f00154-v1':'Wrong standing-leg direction; superseded by v2.','pose05-f00162-v1':'Extra shoe; superseded by v2.','upside-cry-upright-f05304-v1':'Right hat brim cropped at canvas edge; superseded by v2.'}
def intervals(ns):
    out=[]
    for n in ns:
        if out and out[-1][1]==n:out[-1][1]=n+1
        else:out.append([n,n+1])
    return out
for item in registry['assets']:
    if not item['path'].startswith('generated/'):continue
    name=Path(item['path']).stem
    if name in uses:
        item.update(status='used_in_draft_static_review_only',used_intervals=intervals(uses[name]),review={'static':'selected cels and source/composite contact sheets inspected','native_detail':'selected mouth, clock, flower props and upside boundary inspected','dynamic_original_speed':'not_performed','artistic_acceptance':'pending'})
    elif name in rejected:item.update(status='rejected_superseded',reason=rejected[name],used_intervals=[])
    jobfile=R/'jobs'/f'{name}.json'
    if jobfile.exists():
        job=json.loads(jobfile.read_text(encoding='utf-8-sig'));job['selection_status']=item['status'];job['used_intervals']=item.get('used_intervals',[]);jobfile.write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
registry['draft_review']={'version':'DRAFT_v2','generated_files':28,'used_cels':len(uses),'rejected_superseded':len(rejected),'artistic_acceptance':'pending','actual_speed_viewing':'not_performed','source_exposure':'analysis/source_meta.json','final_exposure':'analysis/draft-v2-exposures.json'}
(R/'assets.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'analysis/draft-v2-exposures.json').write_text(json.dumps({'source_sha256':C.M['sha256'],'intervals':'zero-based, end-exclusive','frames':frames},indent=2))
if changes:
    log=R/'analysis/reference-metadata-reconciliation.json';history=json.loads(log.read_text()) if log.exists() else [];log.write_text(json.dumps(history+changes,indent=2))
print(json.dumps({'used_cels':len(uses),'reconciled_source_references':len(changes),'exposure_frames':len(frames)}))
