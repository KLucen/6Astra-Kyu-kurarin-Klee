# 当前状态

更新时间：2026-10-09。全长 ALICE_v4 草稿已导出并通过技术检查；原速美术验收尚未完成。

当前交付：output/Klee_Kyu-kurarin_ALICE_v4.mp4。本次补上用户指出的前段睁眼拥抱：[5784,6039) 帧，197.184–205.877 秒。拥抱对象已换为艾莉丝，可莉保留睁眼表情。后续 [6039,6264) 闭眼艾莉丝拥抱直接沿用 v3，整个拥抱区间为 197.184–213.548 秒。其余 6083 个视频包与 v3 字节完全一致，详见 analysis/alice-v4-change-scope.json。

源片 6338 帧、1920×1080、视频时长 216.0700625 秒；精确 PTS 和 SHA 位于 analysis/source_meta.json。原片末尾两个 AAC 包始于画面结束后；交付只保留覆盖画面区间的完整原始音频包，不重编码音乐。显示参数保持 BT.709、有限范围和 1:1 像素比例。

已保存 30 张生成图片，当前采用 24 张；4 张质量修订历史稿、2 张旧拥抱对象稿保留。assets.json 是素材唯一登记入口；analysis/alice-v4-exposures.json 是当前全片素材曝光表。生成 prompt、参考职责及采用区间位于 jobs。旧 v1/v2/v3、脚本、登记表及技术证据均保留。

scripts/hug_alice_v4.py 在原有合成器中加入睁眼艾莉丝绘稿；analysis/alice-open-cel-registration.json 记录与闭眼艾莉丝及旧绘稿的配准链。scripts/finish_alice_v4.py 只重新编码 255 帧，在新段开头插入独立关键帧，在原有闭眼段关键帧恢复复制。scripts/compare_alice_v4.py 输出原片左、v4 右的完整对照。

全长、对照和 480 帧拥抱预览均通过技术检查：analysis/alice-v4-technical.json、analysis/alice-v4-comparison-technical.json、analysis/alice-v4-full-hug-preview-technical.json。检查包含帧数、精确 PTS、结束边界、AAC 内容及时间戳、完整解码。交付文件校验值见 analysis/delivery-manifest.json。

已静态检查新绘稿、首帧、回声重复、睁眼末帧、闭眼首帧与编码后边界。此前的主要场景、口型、手、花形道具、时钟与倒置帽沿静帧检查继续有效。尚未实际观看原速带声音完整播放；静帧和技术检查不能替代动态美术验收。

已知限制：绘稿比原 PV 更精细；少数入场姿势采用同曝光配准备用值；原片部分手绘轮廓变化未逐张重绘。此前绿色残留检测只在 224 帧原有花形道具边线触发，属于保留道具。旧 64 帧 body-loop-TRIAL.mp4 仅为早期试片。
