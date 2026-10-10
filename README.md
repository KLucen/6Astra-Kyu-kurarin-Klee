# 可莉「琪花星烛」Kyu-kurarin 工程归档

本仓库保存这次角色替换 PV 的工程文件、素材、分析记录和各版成片。当前交付是 **ALICE_v4 草稿**：两段拥抱对象均已替换为艾莉丝。1920×1080，6338 帧，画面时长 216.0700625 秒，保留原歌曲音轨。

全长、对照和拥抱预览已通过精确时序、原 AAC 及完整解码检查，并完成所记录范围的静帧检查；**尚未完成全片原速美术验收**。详细限制见 [当前状态](klee_kyukurarin/STATUS.md)。

## 观看与工程入口

- [完整 ALICE_v4 视频](klee_kyukurarin/output/Klee_Kyu-kurarin_ALICE_v4.mp4)
- [原片左 / 新版右完整对照](klee_kyukurarin/output/Klee_Kyu-kurarin_ALICE_v4_COMPARE.mp4)
- [16.364 秒完整拥抱预览](klee_kyukurarin/output/Klee_Alice_Full_Hug_v4_Preview.mp4)
- [交付说明](klee_kyukurarin/DELIVERY.md)、[工程索引](klee_kyukurarin/PROJECT_INDEX.md)、[制作复盘](klee_kyukurarin/PRODUCTION_REVIEW.md)

## 归档内容

| 路径 | 内容 |
| --- | --- |
| 仓库根目录原 MP4 | 本次分析和合成使用的同一份源视频 |
| `klee_kyukurarin/scripts/` | 项目专用分析、配准、合成、编码及登记脚本 |
| `klee_kyukurarin/generated/` | 30 张生成候选，含当前采用稿与历史替换稿 |
| `klee_kyukurarin/jobs/`、`assets.json` | 生图提示词、参考职责、来源、尺寸/SHA与选稿关系 |
| `klee_kyukurarin/refs/` | 源帧、角色设计与局部参考 |
| `klee_kyukurarin/analysis/` | 真实 PTS、曝光映射、跟踪、候选帧和验证证据 |
| `klee_kyukurarin/output/` | 最新交付、历史版本、试片及合成检查图 |
| `ARCHIVE_MANIFEST.json` | 逐文件尺寸、SHA-256、Git blob 指纹及排除范围 |
| `tools/` | 本归档的完整性检查与源路径重定位工具 |

按上传要求，**不包含 Skill**：Skill 修改记录、Skill 发布副本以及 Python 字节码缓存均排除。制作复盘保留工程方法记录，其中提到的 Skill 修改备份不在本归档中。当前素材和报告中的原机器绝对路径是历史来源记录；可运行的项目副本已保存在上述目录。

## 校验与恢复工作目录

先使用 Python 3.11+ 检查整个归档，确认文件与原始工程一致：

```sh
python tools/verify_archive.py
```

项目原制作环境为 Python 3.14.6；已记录的 Python 库版本见 `requirements.txt`。复制作业环境时还需将 FFmpeg、FFprobe 放入 PATH：

```sh
python -m pip install -r requirements.txt
ffmpeg -version
ffprobe -version
python tools/prepare_workspace.py
python tools/prepare_workspace.py --apply
```

路径工具先验证源视频 SHA，再只修改 `analysis/source_meta.json` 中的 `source`，原文件备份为 `source_meta.archive.json`；不重写曝光或历史报告。路径修改后，原始归档校验会正确报告该元数据文件与归档不同，因此应先校验再准备工作目录。

脚本的职责和依赖见工程索引。可从 `scripts/hug_alice_v4.py` 的合成静帧检查开始；`scripts/finish_alice_v4.py` 基于归档中的 v3 无声视频增量生成 v4。项目脚本采用本片特定帧区间与规格，运行导出/登记脚本可能覆盖同名结果，应先在工作副本中运行。

技术检查报告是当时产出的证据。归档完整性检查不替代视频技术验证或美术验收，也不保证在不同编码器版本中重导得到相同的视频字节。
