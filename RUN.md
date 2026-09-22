# RUN.md — 运行手册（Hermes 与用户用）

> Codex CLI 已装：`codex-cli 0.155.1`，登录态 `Logged in using ChatGPT`（2026-09-21 验证）。
> 规则在 `CODEX-BRIEF.md`，任务在 `TASKS.md`。**分阶段跑，不要一次让它跑完全部**——
> 一是避免撞上用量限制把进度全丢，二是每个 Phase 结束我能独立复核。

## 0. 前置检查（每次开跑前 10 秒）

```bash
cd /Users/ww/Desktop/26f/software/hw1
codex --version            # 期望 codex-cli 0.155.1
codex login status         # 期望 Logged in using ChatGPT
git status --short         # 期望干净（或只有本次意图内的改动）
```

## 1. 命令模板

```bash
cd /Users/ww/Desktop/26f/software/hw1
codex exec \
  -C /Users/ww/Desktop/26f/software/hw1 \
  --skip-git-repo-check \
  -c sandbox_workspace_write.network_access=true \
  --approve-for-me \
  --json \
  -o .codex-last-message.txt \
  "<本节对应的 PROMPT>" < /dev/null 2>&1 | tee -a codex-$(date +%m%d-%H%M).jsonl
```

> **2026-09-21 已实测通过**（沙箱内 `curl` 返回 200、`touch` 写入成功、`-o` 正常落盘）。
> 三个坑：① `-s/--sandbox` 与 `--approve-for-me` **互斥**，同时用会直接报参数错误 —— 只用 `--approve-for-me`（它本身就是 workspace-write 沙箱）；② 必须 `< /dev/null`，否则 Codex 会去读 stdin（管道场景下会打印 "Reading additional input from stdin..."）；③ 目录没 `git init` 时要 `--skip-git-repo-check`，否则报 "Not inside a trusted directory"。

参数含义（都用 `codex exec --help` 与实跑核实过）：

| 参数 | 作用 |
|---|---|
| `-C <dir>` | 把仓库根设为工作根，Codex 的所有相对路径基于此 |
| `--approve-for-me` | 审批请求走自动复核（内部用 workspace-write 沙箱），无人值守也能连续跑 |
| `-c sandbox_workspace_write.network_access=true` | 沙箱内允许联网（下载数据必需） |
| `--skip-git-repo-check` | 允许在非 git 目录里运行（本地已 `git init`，留作兜底） |
| `--json` | 事件流输出成 JSONL，便于事后审计 |
| `-o <file>` | 把 Codex 最后一条消息落盘，便于快速读结论 |
| `< /dev/null` | 切断 stdin，防止 Codex 误读管道内容 |


**降级方案（若沙箱内网络不通）**：`curl` 在沙箱里失败时，由 Hermes 先把原始文件下载到 `data/raw/`，
再用下面的 prompt 让 Codex 只做读取与建模（把 prompt 里的"抓取"改成"读取已存在的 data/raw/ 文件"）：

```bash
mkdir -p data/raw
curl -L -o data/raw/boston_food_licenses.csv "https://data.boston.gov/dataset/5e4182e3-ba1e-4511-88f8-08a70383e1b6/resource/f1e13724-284d-478c-b8bc-ef042aa5b70b/download/tmp3aemwqxo.csv"
curl -s -o data/raw/cambridge_vacant_storefronts.json "https://data.cambridgema.gov/resource/swpv-8j3w.json?\$limit=50000"
curl -s -o data/raw/cambridge_cottage_food_permits.json "https://data.cambridgema.gov/resource/q9yz-5w2v.json?\$limit=50000"
curl -s -o data/raw/cbp22co.zip "https://www2.census.gov/programs-surveys/cbp/datasets/2022/cbp22co.zip"
```

## 2. 三个 PROMPT

### PROMPT 1 — Phase 0 + Phase 1（数据层）

```
先完整阅读 CODEX-BRIEF.md 和 TASKS.md，然后从 Task 0.1 开始，按顺序执行 Phase 0 与 Phase 1 的全部 Task。

纪律要求：
- 每完成一个 Task：先跑该 Task 的「验证」命令，把命令与关键输出写进 LOG.md，然后 git commit（一个 Task 一个 commit）。
- 严禁编造任何数字；所有数字必须来自脚本对原始数据的实际计算结果。
- 严禁 git push、严禁 gh repo create、严禁登录任何账号。
- 遇到 TASKS.md「卡住时怎么办」里的情况，按表处理并记 LOG.md；只有影响方向的事才写 QUESTIONS.md 并停下。

全部完成后，在最后一条消息里给出：完成的 Task 清单；每个验证命令的实际输出摘要；`git log --oneline` 输出；未完成项及原因。
```

### PROMPT 2 — Phase 2（指标与发现）

```
继续本项目。先读 CODEX-BRIEF.md、TASKS.md，再读 LOG.md 与 QUESTIONS.md 了解当前进度（Phase 0/1 应已完成）。

现在执行 Phase 2 的全部 Task（2.1 至 2.5）：
- 口径映射层必须显式写在 build_site_data.py 里，并输出 docs/data/geo_mapping.md。
- findings.json 的每一条发现与建议都必须由函数从数据算出，禁止手写数字。
- 建议内容要用真实数据核实后再定稿，不要照抄 TASKS.md 里的假设措辞。
- 每完成一个 Task 跑验证、写 LOG.md、commit。

完成后在最后一条消息里给出：每个 json 的行数/结构摘要；findings.json 的完整内容；`python3 pipeline/verify_pipeline.py` 的实际输出；未完成项。
```

### PROMPT 3 — Phase 3（网站）

```
继续本项目。先读 CODEX-BRIEF.md、TASKS.md、LOG.md，然后执行 Phase 3 的全部 Task（3.1 至 3.9）。

要点：
- 原生 HTML/CSS/JS + CDN（vega@5/vega-lite@5/vega-embed@6、Leaflet 1.9），不引入任何构建工具或框架。
- 每个页面必须有 viewport meta；每张图下方必须有 Source/accessed 日期/单位行。
- 首页与 explore 页出现的数字必须来自 docs/data/*.json，禁止硬编码。
- 地图弹窗不得显示商户名与电话。
- Task 3.6 的 scripts/verify_site.py 必须真的能拦住手写数字与遗漏项。
- Task 3.9 结束时停下，不要 push；在 HANDOFF.md 写清发布步骤与关键数字清单。

完成后在最后一条消息里给出：6 个页面清单；`python3 scripts/verify_site.py` 的实际输出；HANDOFF.md 的关键数字清单；未完成项。
```

## 3. 每阶段跑完后 Hermes 的独立复核（不由 Codex 提供）

```bash
cd /Users/ww/Desktop/26f/software/hw1
git log --oneline | head -20
python3 pipeline/verify_pipeline.py; echo "pipeline_exit=$?"
python3 scripts/verify_site.py;     echo "site_exit=$?"
grep -ri "dayphn_cleaned" . --exclude-dir=.git | head   # 期望无输出
grep -c '' LOG.md && tail -20 LOG.md
```

## 4. 中断与恢复

```bash
# 续跑最近一次会话
codex exec resume --last "继续执行 TASKS.md 中未完成的 Task，先读 LOG.md 了解进度。"

# 交互式接管（想看过程时）
codex -C /Users/ww/Desktop/26f/software/hw1 --last

# 会话列表 / 用量
codex agents
```

撞上用量限制时：等一会再 `resume`，进度不会丢（每个 Task 都已 commit）。

## 5. 边界（不交给 Codex）

| 事项 | 谁做 | 命令 |
|---|---|---|
| 建远端仓库 + push | Hermes | 见 `HANDOFF.md` 里的两行 `gh` 命令 |
| 打开 GitHub Pages | Hermes | 同上，或网页 Settings → Pages → main / docs |
| 线上 URL 真读回验证 | Hermes | `curl -sI <pages-url> \| head -1` |
| 390×844 手机视口实检 | Hermes | 浏览器工具 |
| 填 PS1 Column、挂到 StudentProjects_1125_2026 | 用户 | 课程页面 |
