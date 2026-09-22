# Cambridge Small-Business Opportunity

为 Cambridge 社区发展部提供可追溯的数据，支持商业区招商与小型商户扶持资源的优先级判断。

| 数据源 | 获取地址 | 访问日期 |
|---|---|---|
| Boston 餐饮营业执照 | https://data.boston.gov/dataset/5e4182e3-ba1e-4511-88f8-08a70383e1b6/resource/f1e13724-284d-478c-b8bc-ef042aa5b70b/download/tmp3aemwqxo.csv | 2026-09-21（计划；实际抓取见 LOG） |
| Cambridge 空置店面、家庭食品作坊许可 | https://data.cambridgema.gov/resource/swpv-8j3w.json / https://data.cambridgema.gov/resource/q9yz-5w2v.json | 2026-09-21（计划；实际抓取见 LOG） |
| Census CBP 2022 | https://www2.census.gov/programs-surveys/cbp/datasets/2022/cbp22co.zip | 2026-09-21（计划；实际抓取见 LOG） |
| BLS QCEW | https://data.bls.gov/cew/data/api/2024/1/area/25017.csv / https://data.bls.gov/cew/data/api/2024/1/area/25025.csv / https://data.bls.gov/cew/data/api/2024/1/industry/722.csv | 2026-09-21（计划；实际抓取见 LOG） |

## 复现

在仓库根目录执行；本环境 python3 指 `/opt/anaconda3/bin/python3`。依赖 pandas、requests、pytest（测试可用 unittest 替代）。

```sh
/opt/anaconda3/bin/python3 pipeline/fetch_boston_licenses.py
/opt/anaconda3/bin/python3 pipeline/fetch_cambridge.py
/opt/anaconda3/bin/python3 pipeline/fetch_cbp_qcew.py
/opt/anaconda3/bin/python3 pipeline/verify_pipeline.py
/opt/anaconda3/bin/python3 -m pytest pipeline/tests -q
```

原始数据不入 git；Boston 电话字段在写盘前删除。数据层之外的聚合与网站属于后续 Phase。

## 发布

由 Hermes 发布至 GitHub Pages，来源为 `main` 分支的 `/docs`。本次仅本地开发与提交，不登录、不推送、不修改远端。网站完成后可用 `python3 -m http.server 8765 --directory docs` 本地预览。

## Codex 使用记录

每完成一个 Phase，追加一行，注明工作范围与验证状态；详细命令、实际结果和异常保存在 LOG.md。

- Phase 0：初始化目录与日志，保留 MBTA 备选数据，完成 README 骨架；本地提交按 Task 分开。
