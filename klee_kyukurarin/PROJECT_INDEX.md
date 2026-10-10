# 可莉「琪花星烛」— Kyu-kurarin 角色替换工程

制作范围：工作区原片全长，替换原人物，保留原背景、道具、字幕、特效、音轨和真实时间戳。

- `analysis/source_meta.json`：源 SHA、6338 个逐帧 PTS、视频/音频规格。
- `analysis/overview-*.jpg`：镜头定位接触页，仅作分析，不能作为独立绘稿判重依据。
- `refs/`：从同一源片顺序解码的原尺寸参考和身份参考。
- `jobs/`：调用前保存的任务、完整 prompt、参考角色及后续结果。
- `generated/`：生成绘稿的工程副本。
- `assets.json`：素材登记与采用状态的唯一入口。
- `scripts/`：本工程分析与合成工具；不程序绘制替代人物。
- `output/`：经过标记的试制/成片与对照视频。
- `STATUS.md`：当前状态与恢复入口。
- `PRODUCTION_REVIEW.md`：本次制作流程、局部返修证据、未达终版的部分及通用 SKILL 提炼；仅为本工程复盘。

策略：strict_source，质量优先。只用实际变化的人物稿映射曝光；不使用光流、变形、交叉淡化冒充重绘。

当前交付入口：`DELIVERY.md`。最新全长草稿是 `output/Klee_Kyu-kurarin_ALICE_v4.mp4`，曝光表为 `analysis/alice-v4-exposures.json`。睁眼与闭眼两段拥抱对象均为艾莉丝；v4 仅补改前段睁眼拥抱，其他片段保持 v3。当前状态是技术通过、静帧已审、原速美术验收待完成。
