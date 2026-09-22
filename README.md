# Cambridge Storefront Opportunity

为 Cambridge Community Development Department 提供可追溯、隐私安全的数据决策网站，帮助有限的招商与小型商户扶持资源优先投向更需要调查的商业区与空间类型。

## 网站内容

- `docs/index.html`：决策摘要、核心图表、发现、建议和商业区排序
- `docs/explore.html`：商业区、面积、空置时间和年份筛选
- `docs/map.html`：Boston 餐饮执照的区域背景地图
- `docs/methodology.html`：一页数据与方法说明
- `docs/data.html`：数据字典、缺失率和 CSV 下载
- `docs/reflection.html`：数据能支持什么、不能证明什么

| 数据源 | 获取地址 | 访问日期 |
|---|---|---|
| Boston 餐饮营业执照 | https://data.boston.gov/dataset/5e4182e3-ba1e-4511-88f8-08a70383e1b6/resource/f1e13724-284d-478c-b8bc-ef042aa5b70b/download/tmp3aemwqxo.csv | 2026-09-21 |
| Cambridge 空置店面、家庭食品作坊许可 | https://data.cambridgema.gov/resource/swpv-8j3w.json / https://data.cambridgema.gov/resource/q9yz-5w2v.json | 2026-09-21 |
| Census CBP 2022 | https://www2.census.gov/programs-surveys/cbp/datasets/2022/cbp22co.zip | 2026-09-21 |
| BLS QCEW 2024 Q1 | https://data.bls.gov/cew/data/api/2024/1/area/25017.csv / https://data.bls.gov/cew/data/api/2024/1/area/25025.csv | 2026-09-21 |

## 复现

在仓库根目录执行；依赖 pandas、requests、pytest。

```sh
/opt/anaconda3/bin/python3 pipeline/fetch_boston_licenses.py
/opt/anaconda3/bin/python3 pipeline/fetch_cambridge.py
/opt/anaconda3/bin/python3 pipeline/fetch_cbp_qcew.py
/opt/anaconda3/bin/python3 pipeline/build_site_data.py
/opt/anaconda3/bin/python3 pipeline/verify_pipeline.py
/opt/anaconda3/bin/python3 -m pytest pipeline/tests -q
/opt/anaconda3/bin/python3 scripts/verify_site.py
```

原始数据不入 git。Boston 电话字段在写盘前删除；家庭食品许可中的姓名、联系方式、家庭地址和坐标不落盘；店面表的业主和租赁联系人字段也被删除。

本地预览：

```sh
/opt/anaconda3/bin/python3 -m http.server 8765 --directory docs
```

然后打开 `http://localhost:8765/`。

## 发布

发布目标是 GitHub Pages，来源为 `main` 分支的 `/docs`。仓库已准备完成，但本地实现过程不登录、不推送、不修改远端；具体命令见 `HANDOFF.md`。

## Codex 使用记录

每完成一个 Phase，追加一行，注明工作范围与验证状态；详细命令、实际结果和异常保存在 LOG.md。

- Phase 0：初始化 Git、目录、README 与工作日志。
- Phase 1：抓取四类公共数据，删除敏感字段，完成质量断言与单元测试。
- Phase 2：生成九个站点 JSON、五个可下载 CSV、发现和建议。
- Phase 3：完成六页响应式网站、交互筛选、地图、演示稿与自动验收。
