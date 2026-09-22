# TASKS.md — 执行清单

> 规则见 `CODEX-BRIEF.md`。**一次只做一个 Task**：实现 → 跑该 Task 的"验证"命令 → 通过后 commit（一个 Task 一个 commit）。
> 验证失败时按 R6 处理，不要用假数据绕过。
> 命令一律在仓库根 `/Users/ww/Desktop/26f/software/hw1` 下执行，`python3` = `/opt/anaconda3/bin/python3`。

---

## Phase 0 — 起步

### [x] Task 0.1 初始化仓库与目录

**Files:** Create `.gitignore`

```bash
cd /Users/ww/Desktop/26f/software/hw1
mkdir -p docs/data docs/downloads docs/assets data/raw data/processed pipeline/tests scripts presentation
printf 'data/raw/\n__pycache__/\n.DS_Store\n*.parquet\n.codex-*\n' > .gitignore
git init -b main 2>/dev/null || true
git add .gitignore && git commit -m "chore: init PS1 small-business site repo"
```

**验证:** `git log --oneline` 至少 1 行；`ls docs pipeline data/processed` 均存在。
**注意:** 仓库可能已存在（用户已 init）。若 `git status` 显示已有提交，不要重做，只补 `.gitignore`。

### [x] Task 0.2 把 MBTA 备选方案移出主目录

**Files:** Move `data/fetch.py` → `fallback-mbta/fetch.py`；把 `data/data/*.csv` → `fallback-mbta/`。
**不要**搬 `.parquet`（体积大，已 ignore）。

**验证:** `ls fallback-mbta/` 含 `fetch.py`；`git status --short` 里不出现 parquet。

### [x] Task 0.3 初始化三份日志文件

**Files:** Create `LOG.md`、`QUESTIONS.md`、`HANDOFF.md`（后者先只写标题，Phase 3 再填）。

`LOG.md` 首行格式示例：
```markdown
# LOG
- [2026-09-21 22:40] Task 0.1 完成 | 验证: git log --oneline → 1 行 | commit: a1b2c3d
## Blockers
```

**验证:** `git add LOG.md QUESTIONS.md HANDOFF.md README.md && git commit -m "docs: add README and working logs"`。

### [x] Task 0.4 README 骨架

**Files:** Create `README.md` —— 一句话项目说明、数据源表（4 源 + 访问日期 2026-09-21）、复现命令、发布说明（GitHub Pages / `docs`）、`## Codex 使用记录` 小节（每完成一个 Phase 追加一行记录的纪律）。

**验证:** `grep -c "Codex 使用记录" README.md` → 1。

---

## Phase 1 — 数据层

### [x] Task 1.1 波士顿执照抓取

**Files:** Create `pipeline/fetch_boston_licenses.py`（输出 `data/raw/boston_food_licenses.csv`）

**Step 1** 实现脚本。**必须**：
- `curl -L` 语义（`requests.get(url, allow_redirects=True)`），因为原 URL 是 302。
- 落地后**立刻** `df = df.drop(columns=["dayphn_cleaned"], errors="ignore")`，并在代码注释写明：*作业禁止收集联系方式，原始数据含商户电话，故删除该列且不写入任何交付物*。
- 打印 `len(df)`、列名列表。

**Step 2 验证**
```bash
python3 pipeline/fetch_boston_licenses.py
python3 -c "import pandas as pd;d=pd.read_csv('data/raw/boston_food_licenses.csv');print(len(d),'dayphn_cleaned' in d.columns,'%.1f%%'%(d.latitude.notna().mean()*100),d.license_add_dt_tm.dropna().min()[:10],d.license_add_dt_tm.dropna().max()[:10])"
```
**Expected:** `3345 false 93.8% 2014-06-12 2026-08-31`（数值容差：行数 3000–4000，坐标覆盖率 ≥ 90%）。
**不符处理:** 行数 < 3000 → 检查是否漏了 `-L`；记录到 `LOG.md ## Blockers`。

**Commit:** `feat(pipeline): fetch Boston food establishment licenses (drop phone column)`

### [x] Task 1.2 剑桥空置店面 + 家庭食品作坊

**Files:** Create `pipeline/fetch_cambridge.py`（输出 `data/raw/cambridge_vacant_storefronts.csv`、`data/raw/cambridge_cottage_food_permits.csv`）

**Step 1** 用 `CODEX-BRIEF.md §3` 的 `soda()` 模板；两个数据集都先 `?$select=count(*)` 取真实行数，再按 `$limit=50000` 拉取，**打印真实行数与拉取行数并断言相等**（防 1000 行静默截断）。
**Step 2** 打印空置店面的 `dataset_year/dataset_month` 的 min/max 与唯一值个数。

**验证**
```bash
python3 pipeline/fetch_cambridge.py
head -1 data/raw/cambridge_vacant_storefronts.csv
```
**Expected:** 脚本自身断言通过并打印行数；表头含 `commercial_district,square_footage,vacancy_date`。
**分支处理:** 若覆盖月份 < 12 → 把"长期空置"指标改为**仅基于 `vacancy_date` 计算空置月数**（不依赖快照序列），并在 `LOG.md` 记一行说明。

**Commit:** `feat(pipeline): fetch Cambridge vacant storefronts and cottage food permits`

### [x] Task 1.3 CBP + QCEW 抓取

**Files:** Create `pipeline/fetch_cbp_qcew.py`（输出 `data/raw/cbp_ma_counties.csv`、`data/raw/qcew_area_25017.csv`、`data/raw/qcew_area_25025.csv`、`data/raw/qcew_industry_722.csv`）

**要点:**
- CBP：下载 `cbp22co.zip` → 解压 → 读 `cbp22co.txt`（`dtype=str` 读 `fipstate/fipscty/naics`，**避免** `44----` 被解析成 NaN）→ 只留 `fipstate=='25'` 且 `fipscty in {'017','025'}`。
- QCEW：`data.bls.gov` 免 key 可用；**不要**访问 `download.bls.gov`。

**验证**
```bash
python3 pipeline/fetch_cbp_qcew.py
python3 -c "import pandas as pd;d=pd.read_csv('data/raw/cbp_ma_counties.csv',dtype=str);print(len(d),sorted(d.fipscty.unique()),d.naics.nunique())"
```
**Expected:** 行数约 `2599`，县 `['017','025']`，`naics` 唯一值 > 100。

**Commit:** `feat(pipeline): add Census CBP 2022 and BLS QCEW county data`

### [x] Task 1.4 数据质量断言

**Files:** Create `pipeline/verify_pipeline.py`（失败必须 `sys.exit(1)`）

断言清单：
1. 波士顿执照行数 ≥ 3000；`latitude` 在 `[42.20, 42.45]`、`longitude` 在 `[-71.30, -70.90]`；坐标缺失率 < 10%；**且确认表中不含 `dayphn_cleaned`**。
2. 空置店面行数 > 0；`square_footage` 数值化后 > 0 的比例 ≥ 80%；`vacancy_date` 可解析为日期。
3. 家庭食品作坊许可行数 > 0；坐标缺失率 < 20%。
4. CBP 两个县都存在；`est`、`emp` 无负值。
5. **打印**所有关键字段的缺失率表（后面直接搬进 `reflection.html` 的"不确定性"一节）。

**验证:** `python3 pipeline/verify_pipeline.py && echo ALL_CHECKS_PASS` → 输出以 `ALL_CHECKS_PASS` 结束。

**Commit:** `test(pipeline): add data quality assertions and missingness report`

### [x] Task 1.5 管线单元测试

**Files:** Create `pipeline/tests/test_pipeline.py`

至少 3 个纯函数测试（不联网）：① `naics` 层级码过滤函数对 `44----` 与 `722511` 的行为；② 空置月数计算（给定快照月与 `vacancy_date`，含跨年）；③ 坐标视窗校验函数对越界值的拒绝。

**验证:** `python3 -m pytest pipeline/tests -q` → 全部通过（若未装 pytest，用 `python3 -m unittest` 亦可，但要在 `LOG.md` 写明用了哪个）。

**Commit:** `test(pipeline): unit tests for naics filtering, vacancy age, coordinate bounds`

---

## Phase 2 — 聚合与指标

### [x] Task 2.1 口径映射层（写在 `build_site_data.py` 顶部）

**Files:** Create `pipeline/build_site_data.py`

在代码里**显式**定义三层地区口径，并生成一张 markdown 表落到 `docs/data/geo_mapping.md`（`data.html` 会引用它）：

| 层 | 本方案用什么 | 局限（必须写进 reflection） |
|---|---|---|
| 剑桥商业区 | 空置店面表 `commercial_district` 原值 | 仅剑桥有，波士顿无对应 |
| 波士顿街区 | 执照表 `zip` + 坐标 | 仅覆盖持证餐饮（`licensecat` 只有 `FS`/`FT`） |
| 县域背景 | CBP/QCEW 的 `017`/`025` | **CBP 只到县，没有 Cambridge 城市级数据** → 仅作区域背景，不做精细对比 |

### [x] Task 2.2 指标 1–4（供给侧）→ `docs/data/*.json`

1. `vacancy_by_district.json`：商业区 × 快照月 → 空置门面数、中位 `square_footage`、**平均空置月数**（快照月 − `vacancy_date`）。
2. `vacancy_age_buckets.json`：空置月数桶（`<3`/`3-6`/`6-12`/`>12`）× 商业区 × 面积档（`<1000`/`1000-2500`/`>2500` sqft）。
3. `licenses_by_year.json`：波士顿餐饮执照逐年新增（2014–2026）× `licensecat`。
4. `license_points.json`：执照点集（`lat,lng,zip,licensecat,year`）—— 供地图，**不含商户名**。

**验证:** 断言 `vacancy_age_buckets` 所有桶计数之和 == 空置店面总行数；每个 json 用 `json.load` 后非空。

### [x] Task 2.3 指标 5–6（对比与需求侧）

5. `industry_structure.json`：CBP 里 722（餐饮）、`44----`（零售）、812（个人服务）的 `est`/`emp`/`ap` 对比 Suffolk vs Middlesex；另附 QCEW 同口径季度趋势。
6. `district_summary.json`：每个剑桥商业区一行 —— 空置数、平均空置月数、空置总面积、每千平方米空置密度。**这是网站的决策表。**

### [x] Task 2.4 生成 `findings.json`（数字必须由函数算出）

**Files:** `pipeline/build_site_data.py` → `docs/data/findings.json`

```python
def worst_districts(summary: pd.DataFrame, k: int = 2) -> list[dict]:
    """按 平均空置月数 × 空置门面数 排序，取前 k 个商业区。"""
    s = summary.assign(score=summary.avg_vacancy_months * summary.n_vacant)
    return s.nlargest(k, "score")[["district", "n_vacant", "avg_vacancy_months", "score"]].to_dict("records")
```

输出结构：
```json
{"headline": {"text": "...", "metric": "...", "value": ...},
 "findings": [{"id": "F1", "text": "...", "value": ..., "unit": "...", "source": "...", "method": "..."}],
 "recommendations": [{"id": "R1", "text": "...", "supported_by": ["F1"], "action": "..."}],
 "generated_at": "2026-09-22T..."}
```

**发现至少 3 条、建议至少 3 条**（作业只要求 ≥2，我们做 3）。建议内容按真实数据核实后定稿，不要照抄假设：
- R1：对空置 ≥12 个月且面积 <1500 sqft 的门面，定向招商「在同类商业区中密度最低」的业态（用 `district_summary` 判定该类）。
- R2：对已发证的家庭食品作坊持有者做"转实体店"扶持（他们已完成资质与产品验证，是现成候选商户池）——用 `cambridge_cottage_food_permits.csv` 的申请日期到发证日期算审批周期作为论据。
- R3：把外展资源集中到空置集中度最高的 2 个商业区（用 `worst_districts()` 的输出），而不是平均分配。

**验证:** `python3 -c "import json;f=json.load(open('docs/data/findings.json'));print(len(f['findings']),len(f['recommendations']))"` → `3 3`（或更多）。

### [x] Task 2.5 导出交付数据集 + 提交

**Files:** `data/processed/*.csv`（清洗+映射后，列名小写下划线）、复制到 `docs/downloads/`。

```bash
python3 pipeline/build_site_data.py && python3 pipeline/verify_pipeline.py
git add pipeline docs/data data/processed
git commit -m "feat(data): six indicators, geo mapping, findings and recommendations"
```

**验证:** `ls docs/data docs/downloads`；`git status --short` 干净。

---

## Phase 3 — 网站

> 全程只用原生 HTML/CSS/JS + CDN。每个 HTML 都要 viewport meta 和共享导航。

### [x] Task 3.1 样式与骨架

**Files:** Create `docs/assets/style.css`、`docs/assets/app.js`、`docs/index.html`

- `:root` 颜色变量；CSS Grid；`@media (max-width: 720px)` 切单列；长表格 `overflow-x:auto`；图表容器 `width:100%; min-height:320px`；导航在窄屏横向滚动（`overflow-x:auto; white-space:nowrap`）。
- 结构：`<header>`（nav 6 页互链）→ `<main>` → `<footer>`（数据来源与访问日期）。

**验证:** `grep -L viewport docs/*.html` 输出为空（此时只有 index.html）。

### [x] Task 3.2 首页三张核心图 + 发现与建议

**Files:** `docs/index.html`（数据从 `docs/data/findings.json`、`vacancy_by_district.json`、`vacancy_age_buckets.json`、`licenses_by_year.json` 异步载入）

1. 条形图：各商业区空置门面数（按平均空置月数着色）。
2. 堆叠/热力图：空置月数桶 × 面积档。
3. 折线：波士顿餐饮执照逐年新增（2014–2026）。

外加：首屏「问题 + 目标用户」段；"Key findings" 4 条（数字从 `findings.json` 注入）；"Recommendations" 3 条（每条注明支撑发现 ID）。每张图正下方一行来源（含 `accessed 2026-09-22` 与单位）。

**验证:**
```bash
python3 -m http.server 8765 --directory docs &
sleep 2 && curl -s localhost:8765/ | grep -c "vega-embed"
```
**Expected:** ≥ 1。测试完 `kill %1`。

### [x] Task 3.3 交互探索页

**Files:** `docs/explore.html` + `docs/assets/app.js`

- 一次 `fetch` 全部 json，控件变化 → 过滤 → `view.data()` 更新（**不要**重建整个图表 DOM）。
- 控件：商业区（多选）、面积区间（双滑块或两个 number input）、最小空置月数（滑块）、年份区间（执照图用）、视图切换（4 个图）。
- 实时显示"当前筛选 → N 个门面 / M 家商户"。
- 把筛选状态写进 URL query string（可分享、刷新不丢）。

**验证:** `node --check docs/assets/app.js` → 无输出；页面源码含计数元素 id。

### [x] Task 3.4 地图页

**Files:** `docs/map.html`

- Leaflet 1.9 + Carto light 底图；图层开关：波士顿执照点（`license_points.json`）/ 剑桥空置店面（若该表有坐标就用点，否则按 zip 聚合为圆点并在图注说明）。
- 弹窗只显示：业态类别、面积、空置月数或发证年份。**不显示商户名与电话。**
- 图注写明点数量与数据来源。

**验证:** `curl -s localhost:8765/map.html | grep -c leaflet` ≥ 1；页面里的数据全部来自 json，无内联硬编码数组。

### [x] Task 3.5 methodology / data / reflection 三页

- `docs/methodology.html`（**一页**，可打印）：问题与用户；四个数据源与访问日期；清洗步骤（删电话列、坐标校验、口径映射表 ← 引用 `geo_mapping.md`）；指标定义与公式；能证明什么/不能证明什么；复现命令。
- `docs/data.html`：数据字典表（字段 / 类型 / 单位 / 定义 / 缺失率）+ 每个 CSV 的下载链接 + ≥5 条来源 URL（每条带访问日期）。
- `docs/reflection.html`：缺失数据（用 `verify_pipeline.py` 打出的缺失率）、偏差（只覆盖持证商户；执照表仅 FS/FT 两类；空置为月度快照）、不确定性（CBP 小样本屏蔽；县 ≠ 市；无 2023+ 年 CBP）、局限（相关 ≠ 因果，缺口 ≠ 一定能盈利）。

**验证:** `python3 -c "import re,pathlib;h=pathlib.Path('docs/data.html').read_text();print(len(re.findall(r'https?://',h)))"` → ≥ 5。

### [x] Task 3.6 站点自检脚本

**Files:** Create `scripts/verify_site.py`，逐条断言：

- 6 个 HTML 都存在、都有 viewport meta、都引用同一个 style.css
- `docs/.nojekyll` 存在
- `docs/data/*.json` 全部可 `json.load` 且非空
- `findings.json` 的 `recommendations` 长度 ≥ 2，`findings` ≥ 3
- `data.html` 里 URL ≥ 5，且含 `accessed` 字样
- `docs/downloads/*.csv` 至少 3 个且行数 > 0
- `index.html` 文本中出现的每个形如 `\d+(\.\d+)?%` 的百分比，都能在 `docs/data/*.json` 里找到同值（**防止手写数字漂移**）
- 仓库里不存在 `dayphn_cleaned` 字样（`grep -r` 全仓检查，含 CSV）

**验证:** `python3 scripts/verify_site.py && echo SITE_CHECKS_PASS`

**Commit:** `feat(site): index, explore, map, methodology, data, reflection + verifiers`

### [x] Task 3.7 五分钟演示稿

**Files:** Create `presentation/PS1-demo-5min.md` —— 五段各 60 秒：① 问题与用户（30s）② 数据与来源（60s）③ 现场演示三个筛选动作（120s，写明点哪个控件看什么变化）④ 发现与建议（90s）⑤ 局限与不能证明什么（30s）。

**验证:** 文件里明确出现 ≥3 个"点 <控件名>"的操作指令。

### [x] Task 3.8 README 收尾 + HANDOFF

**Files:** 更新 `README.md`（数据源表、复现命令、发布步骤、`## Codex 使用记录` 每个 Phase 一行）；Create/填充 `HANDOFF.md`。

`HANDOFF.md` 必须包含：
1. 本地预览：`python3 -m http.server 8765 --directory docs` → `http://localhost:8765/`
2. 页面清单与文件名
3. `docs/data/*.json` 里每个关键数字（供 Hermes 验收对账）
4. 已知问题与未做的取舍
5. **发布步骤（给 Hermes 执行）**：
   ```bash
   gh repo create ps1-small-business-market-opportunity --public --source=. --remote=origin --push
   gh api -X POST repos/Wuhubing/ps1-small-business-market-opportunity/pages \
     -f 'source[branch]=main' -f 'source[path]=/docs'
   ```

**Commit:** `docs: README, demo script, handoff notes (ready to publish)`

### [x] Task 3.9 收尾检查

```bash
python3 pipeline/verify_pipeline.py && python3 scripts/verify_site.py && git status --short
```
**Expected:** 两个 `_PASS` 结束、`git status` 干净。
然后**停下来**，等 Hermes 做手机端验收与发布。不要 push。

---

## Phase 4 — 不归你做

发布（`gh repo create` / push / Pages）→ **Hermes**。
390×844 手机视口实检 → **Hermes**。
课程提交（PS1 Column、StudentProjects_1125_2026）→ **用户**。

---

## 卡住时怎么办

| 症状 | 处理 |
|---|---|
| 某个源返回非 200 | 先重试 1 次；仍失败 → 记 `LOG.md ## Blockers`，跳过该指标，其余照做 |
| 空置店面覆盖月份太少 | 改用以 `vacancy_date` 计算空置月数（见 Task 1.2 分支处理） |
| `pytest` 未安装 | 用 `python3 -m unittest` 替代，并记进 `LOG.md` |
| CDN 图表库加载不出来 | 换另一个 jsdelivr 版本；仍不行则在页面里内联一个最小 SVG 条形图作为降级，并在 `LOG.md` 写明 |
| 12:00 前网站仍跑不起来 | **停**，写 `QUESTIONS.md`：建议切 `fallback-mbta/` 方案（数据已就绪） |
| 任何需要账号/凭据/付费 key 的事 | 不要做，写 `QUESTIONS.md` |
