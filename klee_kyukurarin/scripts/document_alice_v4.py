"""Commit v4 delivery records only after all requested exports pass verification."""
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
reports = ['alice-v4-technical.json', 'alice-v4-comparison-technical.json', 'alice-v4-full-hug-preview-technical.json']
checks = {name: json.loads((R / 'analysis' / name).read_text())['technical_pass'] for name in reports}
assert all(checks.values()), checks
scope = json.loads((R / 'analysis/alice-v4-change-scope.json').read_text())
assert scope['outside_interval_video_payloads_unchanged']
assert scope['outside_interval_video_packets'] == 6083

new, old = 'hug-open-alice-f05784-v1', 'hug-open-f05784-v1'
registry = json.loads((R / 'assets.json').read_text())
for item in registry['assets']:
    if item['path'] == f'generated/{old}.png':
        item['previous_v3_intervals'] = item.get('used_intervals', [])
        item.update(status='superseded_by_user_requested_Alice', used_intervals=[])
    if item['path'] == f'generated/{new}.png':
        item.update(status='used_in_draft_static_review_only', used_intervals=[[5784, 6039]], review={
            'static': 'generated cel, first exposure, echo copies, final open-eye exposure, transition into existing closed-eye Alice inspected',
            'registration': 'analysis/alice-open-cel-registration.json',
            'dynamic_original_speed': 'not_performed', 'artistic_acceptance': 'pending'})

exp = json.loads((R / 'analysis/alice-v3-exposures.json').read_text())
for row in exp['frames']:
    if 5784 <= row['frame'] < 6039:
        for layer in row['layers']:
            if layer['asset'] == old:
                layer.update(asset=new, cel_alignment='analysis/alice-open-cel-registration.json')
exp.update(baseline='analysis/alice-v3-exposures.json', changed_interval=[5784, 6039], alice_intervals=[[5784, 6039], [6039, 6264]])
(R / 'analysis/alice-v4-exposures.json').write_text(json.dumps(exp, indent=2))
used = {layer['asset'] for row in exp['frames'] for layer in row['layers']}
registry['draft_review'].update(
    version='ALICE_v4', generated_files=len(list((R / 'generated').glob('*.png'))),
    used_cels=len(used), final_exposure='analysis/alice-v4-exposures.json',
    user_scope='Fill omitted open-eye hug partner with Alice in [5784,6039). Existing closed-eye Alice and all other v3 video packets retained.',
    change_scope_report='analysis/alice-v4-change-scope.json', technical_checks=checks,
    technical_status='passed', historical_partner_cels=2)
(R / 'assets.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding='utf-8')
j = R / 'jobs' / f'{new}.json'
job = json.loads(j.read_text())
job.update(selection_status='used_in_draft_static_review_only', used_intervals=[[5784, 6039]], registration='analysis/alice-open-cel-registration.json')
j.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')

files = []
for name in ['Klee_Kyu-kurarin_ALICE_v4.mp4', 'Klee_Kyu-kurarin_ALICE_v4_COMPARE.mp4', 'Klee_Alice_Full_Hug_v4_Preview.mp4']:
    p = R / 'output' / name
    files.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
manifest_path = R / 'analysis/delivery-manifest.json'
old_manifest = R / 'analysis/delivery-manifest-v3.json'
if not old_manifest.exists():
    old_manifest.write_bytes(manifest_path.read_bytes())
manifest = {'version': 'ALICE_v4', 'date': '2026-10-09', 'files': files, 'checks': checks,
    'scope': 'Only frames 5784 through 6038 changed from v3; all 6083 other video packet payloads are identical. Original AAC retained.',
    'artistic_status': 'draft_static_reviewed_not_viewed_at_original_speed'}
manifest_path.write_text(json.dumps(manifest, indent=2))
(R / 'analysis/export-progress.json').write_text(json.dumps({
    'stage': 'delivered_draft_technical_pass', 'version': 'ALICE_v4',
    'changed_frames': [5784, 6039], 'alice_frames_total': [5784, 6264],
    'output': files[0]['path'], 'technical_checks': checks,
    'artistic_status': 'static_review_only_original_speed_pending'}, indent=2))

status = '''# 当前状态

更新时间：2026-10-09。全长 ALICE_v4 草稿已导出并通过技术检查；原速美术验收尚未完成。

当前交付：output/Klee_Kyu-kurarin_ALICE_v4.mp4。本次补上用户指出的前段睁眼拥抱：[5784,6039) 帧，197.184–205.877 秒。拥抱对象已换为艾莉丝，可莉保留睁眼表情。后续 [6039,6264) 闭眼艾莉丝拥抱直接沿用 v3，整个拥抱区间为 197.184–213.548 秒。其余 6083 个视频包与 v3 字节完全一致，详见 analysis/alice-v4-change-scope.json。

源片 6338 帧、1920×1080、视频时长 216.0700625 秒；精确 PTS 和 SHA 位于 analysis/source_meta.json。原片末尾两个 AAC 包始于画面结束后；交付只保留覆盖画面区间的完整原始音频包，不重编码音乐。显示参数保持 BT.709、有限范围和 1:1 像素比例。

已保存 30 张生成图片，当前采用 24 张；4 张质量修订历史稿、2 张旧拥抱对象稿保留。assets.json 是素材唯一登记入口；analysis/alice-v4-exposures.json 是当前全片素材曝光表。生成 prompt、参考职责及采用区间位于 jobs。旧 v1/v2/v3、脚本、登记表及技术证据均保留。

scripts/hug_alice_v4.py 在原有合成器中加入睁眼艾莉丝绘稿；analysis/alice-open-cel-registration.json 记录与闭眼艾莉丝及旧绘稿的配准链。scripts/finish_alice_v4.py 只重新编码 255 帧，在新段开头插入独立关键帧，在原有闭眼段关键帧恢复复制。scripts/compare_alice_v4.py 输出原片左、v4 右的完整对照。

全长、对照和 480 帧拥抱预览均通过技术检查：analysis/alice-v4-technical.json、analysis/alice-v4-comparison-technical.json、analysis/alice-v4-full-hug-preview-technical.json。检查包含帧数、精确 PTS、结束边界、AAC 内容及时间戳、完整解码。交付文件校验值见 analysis/delivery-manifest.json。

已静态检查新绘稿、首帧、回声重复、睁眼末帧、闭眼首帧与编码后边界。此前的主要场景、口型、手、花形道具、时钟与倒置帽沿静帧检查继续有效。尚未实际观看原速带声音完整播放；静帧和技术检查不能替代动态美术验收。

已知限制：绘稿比原 PV 更精细；少数入场姿势采用同曝光配准备用值；原片部分手绘轮廓变化未逐张重绘。此前绿色残留检测只在 224 帧原有花形道具边线触发，属于保留道具。旧 64 帧 body-loop-TRIAL.mp4 仅为早期试片。
'''
(R / 'STATUS.md').write_text(status, encoding='utf-8')
delivery = '''# 可莉「琪花星烛」Kyu-kurarin · 艾莉丝拥抱版

当前全长草稿：`output/Klee_Kyu-kurarin_ALICE_v4.mp4`。

本次补齐先前漏改的睁眼拥抱镜头，拥抱对象改为艾莉丝，可莉保留睁眼表情。实际修改区间为 3:17.184–3:25.877；紧接的闭眼艾莉丝拥抱保留至 3:33.548。相比 v3，区间外 6083 个视频包字节完全一致，原音轨直接复制。

全片 1920×1080、6338 帧、画面长 3 分 36.070 秒。带原音乐的完整左右对比：`output/Klee_Kyu-kurarin_ALICE_v4_COMPARE.mp4`，左侧原 PV，右侧 v4 草稿。

完整拥抱预览：`output/Klee_Alice_Full_Hug_v4_Preview.mp4`，480 帧、16.364 秒，包含睁眼与闭眼两段及原片音乐。三个交付视频均通过严格时序、音频包和完整解码检查，校验值见 `analysis/delivery-manifest.json`。

新绘稿、回声重复、表情转换与编码后边界已做静帧检查。尚未实际观看原速完整播放，因此仍标为草稿；绘稿细节比原 PV 更密，部分原有线条抖动未逐张重绘。

工程索引见 `PROJECT_INDEX.md`；素材及使用区间见 `assets.json` 和 `analysis/alice-v4-exposures.json`。旧 v3 全片与只含闭眼段的预览保留为历史文件。

艾莉丝造型依据[原神官方角色公开](https://www.hoyolab.com/article/40132321)，具体背面服饰使用[转载的游戏模型三视图](https://news.17173.com/content/12012025/165930969.shtml)作参考。参考仅用于角色设计核对，画面由本工程重新生成与合成。
'''
(R / 'DELIVERY.md').write_text(delivery, encoding='utf-8')
p = R / 'PROJECT_INDEX.md'
index = p.read_text(encoding='utf-8').replace('ALICE_v3.mp4', 'ALICE_v4.mp4').replace('alice-v3-exposures.json', 'alice-v4-exposures.json')
index = index.replace('艾莉丝仅用于闭眼拥抱；睁眼拥抱及其他片段保持 v2。', '睁眼与闭眼两段拥抱对象均为艾莉丝；v4 仅补改前段睁眼拥抱，其他片段保持 v3。')
p.write_text(index, encoding='utf-8')
print(json.dumps({'version': 'ALICE_v4', 'generated': 30, 'used_cels': len(used), 'checks': checks, 'files': files}, ensure_ascii=False), flush=True)
