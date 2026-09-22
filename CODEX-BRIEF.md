# CODEX-BRIEF.md — PS1 数据网站项目常驻指令

> **每次会话开始，先完整读这份文件，再读 `TASKS.md`。**
> 说明：本文件原打算命名为 `AGENTS.md`（Codex 会自动加载），但该文件名在用户的 Hermes 环境里是写保护的，
> 因此改名为 `CODEX-BRIEF.md`，由启动 prompt 显式要求你读取。作用完全相同。
>
> 你在本项目里是**唯一实现者**（1.125 Agentic Computing 的 "apprentice"）。
> Hermes 是控制面，负责验收与发布；用户是 MIT 学生，只做需要人拍板的事。

---

## 1. 任务本质

做一个**网站**，帮 **Cambridge Community Development Department（社区发展部）** 决定一件事：

> 有限的招商与扶持资源，应该先投向**哪个商业区、哪类业态**？

这不是"做一堆图表"。评分表（按此排序注意力）：

| 项 | 权重 |
|---|---|
| 目的与实用性 | 20% |
| 数据质量与文档 | 20% |
| 分析与推理 | 20% |
| 网站功能与可用性 | 20% |
| 视觉表达 | 10% |
| 建议与局限 | 10% |

**截止 2026-09-22 17:00 EDT。** 当"更花哨"和"跑得起来、数字可追溯"冲突时，永远选后者。

## 2. 环境事实（已核实，**不要**再花时间探测）

- 联网：美国网络，**无代理**。不要设置 `http_proxy` / `https_proxy`；npm/PyPI 走官方源。
- Python：`/opt/anaconda3/bin/python3`，已装 `pandas 2.3.3`、`pyarrow 21.0.0`、`requests`。
- Node `v22.16.0`，git `2.39.5`。
- `gh` 已登录 `Wuhubing` —— **但你不要用**（见 §7）。
- 工作根目录（本仓库）：`/Users/ww/Desktop/26f/software/hw1`。所有相对路径都相对这里。
- `data/raw/` 与 `*.parquet` **不入 git**（已在 `.gitignore`）。

## 3. 数据源白名单（精确 URL，全部实测可用）

| # | 源 | 精确取法 | 实测事实 |
|---|---|---|---|
| 1 | 波士顿餐饮营业执照 | `curl -L -o data/raw/boston_food_licenses.csv "https://data.boston.gov/dataset/5e4182e3-ba1e-4511-88f8-08a70383e1b6/resource/f1e13724-284d-478c-b8bc-ef042aa5b70b/download/tmp3aemwqxo.csv"` | **必须 `-L`**（302 跳转）。约 3,345 行；列含 `businessname,dbaname,address,city,state,zip,licstatus,licensecat,descript,license_add_dt_tm,dayphn_cleaned,property_id,latitude,longitude`；发证日期 2014-06→2026-08；93.8% 有经纬度；`licensecat` 只有 `FS`/`FT` 两类 |
| 2 | 剑桥零售空置店面 | `https://data.cambridgema.gov/resource/swpv-8j3w.json?$limit=50000` | 字段 `dataset_year,dataset_month,commercial_district,address,city,state,zip_code,square_footage,vacancy_date` |
| 3 | 剑桥家庭食品作坊许可 | `https://data.cambridgema.gov/resource/q9yz-5w2v.json?$limit=50000` | 字段 `id,full_address,latitude,longitude,status,applicant_submit_date,issue_date` |
| 4 | Census CBP 2022（县级） | `https://www2.census.gov/programs-surveys/cbp/datasets/2022/cbp22co.zip` → `cbp22co.txt` | 13.7 MB。字段 `fipstate,fipscty,naics,emp_nf,emp,qp1_nf,qp1,ap_nf,ap,est,n<5,n5_9,n10_19,n20_49,n50_99,n100_249,n250_499,n500_999,n1000`。`naics` 是**字符串**（如 `44----`、`722511`），**不要**读成数字 |
| 5 | BLS QCEW（辅助，季度趋势） | `https://data.bls.gov/cew/data/api/2024/1/area/25017.csv`、`.../area/25025.csv`、`.../industry/722.csv` | 415 KB / 767 KB，免 key |

Socrata 必须显式分页并用 UA（默认上限 1000 行会**静默截断**）：

```python
import requests, pandas as pd
BASE = "https://data.cambridgema.gov/resource"
def soda(dataset_id: str, limit: int = 50000) -> pd.DataFrame:
    r = requests.get(f"{BASE}/{dataset_id}.json",
                     params={"$limit": limit, "$order": ":id"},
                     headers={"User-Agent": "MIT-1.125-PS1-research/1.0"}, timeout=120)
    r.raise_for_status()
    return pd.DataFrame(r.json())
```

**禁止使用**（均已实测不可用或需人工审核）：
OSM Overpass API（406，镜像连不上）、`api.us.socrata.com` 全球目录（连接失败）、`download.bls.gov`（403）、`data.mass.gov`（403）、SBA 旧 CKAN API（404）、Yelp Open Dataset（需审核）、Google Places / Yelp Fusion（需付费 key）。
→ 因此**不要**做"竞争者 POI 数量"类结论，改用餐照/许可密度做代理指标，并写进局限。

## 4. 硬性规则（违反即返工）

- **R1 禁止编造数字。** 页面上每个数字都必须由管线脚本从原始数据算出，并能在 `docs/data/*.json` 找到同源。禁止手写、估算、"大致是"。
- **R2 禁止任何个人联系方式数据。** 抓完波士顿执照**立刻 `drop(columns=['dayphn_cleaned'])`**（代码里注释写明原因）。地图/表格不显示电话。
- **R3 禁止登录任何账号、输入任何凭据、提交任何课程表单。**
- **R4 禁止 `git push`、禁止 `gh repo create`、禁止改远端配置。** 发布由 Hermes 做（见 §7）。
- **R5 每个 Task 的节奏固定**：实现 → 跑该 Task 的验证命令 → 通过 → `git add` 相关文件 → commit。commit message 用 conventional commits 前缀（`feat:`/`fix:`/`docs:`/`chore:`/`test:`），一次 commit 对应一个 Task。
- **R6 失败不要用假数据绕过。** 数据与预期不符或命令失败时，把原始报错写进 `LOG.md` 的 `## Blockers`，继续下一个不依赖它的任务；整条路被堵死才写 `QUESTIONS.md` 并停下。
- **R7 每个 HTML 必须有** `<meta name="viewport" content="width=device-width, initial-scale=1">`；每个图表正下方必须有一行 `Source: …; accessed 2026-09-22; unit: …`。
- **R8 禁止引入构建工具、框架、后端、数据库、打包器。** 只用原生 HTML/CSS/JS + CDN：`vega@5`/`vega-lite@5`/`vega-embed@6`（jsdelivr）、Leaflet 1.9 + Carto light 底图（免 key）。GitHub Pages 从 `main` 分支 `/docs` 目录发布。
- **R9 不留烂尾。** 停下前 `git status` 必须干净，或把未完成部分写进 `LOG.md` 说明原因。

## 5. 目录结构（最终形态，严格照此）

```
/Users/ww/Desktop/26f/software/hw1/
├─ CODEX-BRIEF.md TASKS.md RUN.md PLAN.md   ← 指令与计划
├─ README.md LOG.md QUESTIONS.md HANDOFF.md
├─ .gitignore
├─ pipeline/
│  ├─ fetch_boston_licenses.py
│  ├─ fetch_cambridge.py
│  ├─ fetch_cbp_qcew.py
│  ├─ build_site_data.py     ← 唯一 join/聚合入口
│  ├─ verify_pipeline.py     ← 数据质量断言（失败即非零退出）
│  └─ tests/test_pipeline.py
├─ data/raw/（不入 git）  data/processed/（交付数据集）
├─ docs/                     ← GitHub Pages 根
│  ├─ index.html explore.html map.html methodology.html data.html reflection.html
│  ├─ assets/style.css app.js
│  ├─ data/*.json            ← 站点读的紧凑数据
│  ├─ downloads/*.csv        ← 数据集下载
│  └─ .nojekyll
├─ scripts/verify_site.py    ← 逐条核对作业要求
├─ presentation/PS1-demo-5min.md
└─ fallback-mbta/            ← 备选方案（只搬移，不改内容）
```

## 6. 作业要求 → 落地位置（验收基线，一条都不能少）

| 作业要求 | 落在哪 |
|---|---|
| 问题陈述 + 目标用户 | `docs/index.html` 首屏 |
| 数据如何收集 | `docs/methodology.html` |
| ≥3 图表/地图/表格/指标 | `index.html` 3 个 + `explore.html` 4 个交互图 + `map.html` 1 张地图 = 8 个 |
| 筛选/对比控件 | `explore.html`：商业区（多选）、面积区间、最小空置月数、年份区间、视图切换 |
| 最重要发现总结 | `index.html` "Key findings"，数字全部来自 `docs/data/findings.json` |
| ≥2 条实用建议 | `index.html` "Recommendations"，每条注明支撑它的数据 |
| 来源 URL / 日期 / 单位 / 定义 | `docs/data.html` 数据字典表 + 每图下方来源行 |
| 缺失 / 偏差 / 不确定性 / 局限 | `docs/reflection.html`（同时就是 short reflection） |
| 电脑 + 手机都能用 | CSS Grid + `@media (max-width: 720px)` + viewport meta |
| 数据集 CSV | `data/processed/*.csv` + `docs/downloads/*.csv` |
| 一页方法论 | `docs/methodology.html` |
| 5 分钟演示 | `presentation/PS1-demo-5min.md` |

## 7. 边界：这些不归你做

- **发布**（`gh repo create` / `push` / 打开 Pages）：Hermes 做。你的职责是把仓库准备到"一条命令就能发布"，并在 `HANDOFF.md` 写清发布步骤与预期 URL。
- **手机视口实检**（390×844）：Hermes 做。你只需保证 CSS 在窄屏不溢出。
- **课程提交**（填 PS1 Column、挂到 StudentProjects_1125_2026）：用户做。

## 8. 日志纪律（这三份文件是别人读你的唯一途径）

- `LOG.md`：每完成一个 Task 追加一行 —— `[YYYY-MM-DD HH:MM] Task X.Y 完成 | 验证: <命令> → <关键输出> | commit: <短 sha>`。有问题另开 `## Blockers` 写原始报错。
- `QUESTIONS.md`：需要用户拍板的事，编号 + 选项 + 你的默认建议。小事不要停，只有影响方向的事才写。
- `HANDOFF.md`（Phase 3 结束时写）：本地预览命令、页面清单、已知问题、发布步骤、`docs/data/*.json` 里的关键数字清单（供验收对账）。

## 9. 情绪提醒

你写的东西会被一个 24 小时后要交作业的学生看到。**清楚、能跑、数字可追溯**，比惊艳更重要。
