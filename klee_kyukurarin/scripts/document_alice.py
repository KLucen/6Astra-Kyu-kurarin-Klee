import json,hashlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
registry=json.loads((R/'assets.json').read_text());new='hug-closed-alice-f06039-v1';old='hug-closed-f06039-v1'
for item in registry['assets']:
    if item['path']==f'generated/{old}.png':
        item['previous_v2_intervals']=item.get('used_intervals',[]);item.update(status='superseded_by_user_requested_Alice',used_intervals=[])
    if item['path']==f'generated/{new}.png':
        item.update(status='used_in_draft_static_review_only',used_intervals=[[6039,6264]],review={'static':'Alice game reference, generated cel, aligned 1080p composite inspected','registration':'analysis/alice-cel-registration.json','dynamic_original_speed':'not_performed','artistic_acceptance':'pending'})
p=R/'refs/alice-game-model-three-view.jpg'
if not any(x['path']=='refs/alice-game-model-three-view.jpg' for x in registry['assets']):
    registry['assets'].append({'path':'refs/alice-game-model-three-view.jpg','role':'Alice_game_design_reference_reposted_model_views','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(Image.open(p).size),'source':'https://news.17173.com/content/12012025/165930969.shtml','official_reveal':'https://www.hoyolab.com/article/40132321','reference_only':True})
exp=json.loads((R/'analysis/draft-v2-exposures.json').read_text())
for row in exp['frames']:
    if 6039<=row['frame']<6264:
        for layer in row['layers']:
            if layer['asset']==old:layer['asset']=new;layer['cel_alignment']='analysis/alice-cel-registration.json'
exp['baseline']='analysis/draft-v2-exposures.json';exp['changed_interval']=[6039,6264]
(R/'analysis/alice-v3-exposures.json').write_text(json.dumps(exp,indent=2))
registry['draft_review'].update(version='ALICE_v3',generated_files=len(list((R/'generated').glob('*.png'))),used_cels=24,final_exposure='analysis/alice-v3-exposures.json',user_scope='Only hug_closed partner replaced with Alice. All other v2 video packets retained.',change_scope_report='analysis/alice-v3-change-scope.json')
(R/'assets.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2),encoding='utf-8')
j=R/'jobs'/f'{new}.json';job=json.loads(j.read_text());job.update(selection_status='used_in_draft_static_review_only',used_intervals=[[6039,6264]],registration='analysis/alice-cel-registration.json');j.write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
print('Alice v3 selection and full exposure ledger saved')
