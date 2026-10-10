import argparse,json,hashlib,shutil
from pathlib import Path
from PIL import Image
a=argparse.ArgumentParser();a.add_argument('job');a.add_argument('original');args=a.parse_args()
R=Path(__file__).resolve().parents[1];j=R/'jobs'/f'{args.job}.json';job=json.loads(j.read_text(encoding='utf-8'));p=R/'generated'/f'{args.job}.png'
if p.exists():raise FileExistsError(p)
shutil.copy2(args.original,p);im=Image.open(p)
record={'path':p.relative_to(R).as_posix(),'role':'generated_candidate','job':args.job,'original':args.original,'size':list(im.size),'mode':im.mode,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'generated_not_reviewed'}
job.update(status='generated',output=record);j.write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
m=R/'assets.json';data=json.loads(m.read_text(encoding='utf-8'));data['assets'].append(record);data['jobs'].append({'id':args.job,'path':j.relative_to(R).as_posix(),'status':'generated'});temp=m.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(m)
print(json.dumps(record,ensure_ascii=False))
