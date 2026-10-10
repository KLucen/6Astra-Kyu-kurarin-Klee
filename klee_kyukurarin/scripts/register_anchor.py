from pathlib import Path
from PIL import Image
import json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
p=R/'generated/anchor-f01027-v1.png'
j=R/'jobs/anchor-f01027-v1.json';job=json.loads(j.read_text(encoding='utf-8'))
job.update(status='generated',output=p.relative_to(R).as_posix(),original='C:/Users/KLucen/.codex/generated_images/01a11bf6-c022-7263-a449-3c992ecd9fe7/exec-efba40e6-3e95-4160-9d48-caca96343a47.png',actual_dimensions=list(Image.open(p).size),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),review={'status':'selected_draft','scope':'generated PNG full-frame visual inspection','findings':['Character costume and toast pose recognizable','Generated background and lyrics must not be used; preserve source layers','Hat extends beyond original head footprint; occlusion requires per-shot review','Slight shading more elaborate than source; simplify for following cels'],'not_checked':['composite','continuity','original_speed','encoded']})
j.write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
a=json.loads((R/'assets.json').read_text(encoding='utf-8'));a['jobs'].append({'id':job['id'],'path':j.relative_to(R).as_posix(),'status':job['status']});a['assets'].append({'path':job['output'],'role':'generated_character_style_anchor','source_frame':1027,'size':job['actual_dimensions'],'sha256':job['sha256'],'status':'selected_draft','job':job['id']});a['selections']['anchor-f01027']=job['output']
ref=R/'refs/klee-official-outfit.jpg';a['assets'].append({'path':ref.relative_to(R).as_posix(),'role':'official_costume_reference','url':'https://webstatic.hoyoverse.com/upload/op-public/2023/06/21/3aae49573a525b69ba832883a822f64e_8488129397694502949.jpg','source_page':'https://genshin.hoyoverse.com/zh-tw/news/detail/111981','size':list(Image.open(ref).size),'sha256':hashlib.sha256(ref.read_bytes()).hexdigest()})
(R/'assets.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
print(job['actual_dimensions'],job['sha256'])
