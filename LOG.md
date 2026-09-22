# LOG

- [2026-09-21] Task 0.1 完成 | 验证: `git log --oneline` → 初始化提交存在；`docs/`、`pipeline/`、`data/processed/` 均存在 | commit: `d7966d1`
- [2026-09-21] Task 0.2 检查完成 | 未发现需要迁移的 MBTA 文件；保留空的 `fallback-mbta/` 作为应急目录
- [2026-09-21] Phase 1 完成 | 验证: `pipeline/verify_pipeline.py` → `ALL_CHECKS_PASS`; `pytest` → `3 passed` | commits: `fc31ed4`–`f7d4137`
- [2026-09-21] Phase 2 完成 | 最新快照 96 行/10 区；9 个站点 JSON；5 个下载 CSV；findings/recommendations = 3/3 | commit: `0b20187`
- [2026-09-21] Phase 3 网站完成 | 验证: 6 页、9 JSON、5 CSV、交互筛选与地图浏览器实检通过；`scripts/verify_site.py` → `SITE_CHECKS_PASS` | commit: `b8f0a46`

## Blockers

- Boston 源的最早 `license_add_dt_tm` 为 2006-12-07，而初始文档预期为 2014；图表按项目定义仅展示 2014–2026，原记录未删除。
- 历史空置记录的 `vacancy_date` 缺失 73.8%，不满足初始 95% 假设；当前决策改用 vacancy-year 完整的 2025-09 最新快照，并在反思页披露。
- CARTO 无密钥底图实测显示 API key 要求；切换为 OpenStreetMap 标准瓦片并完成浏览器复核。
