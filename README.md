# R218 OSCAR True-INT2 — 证据分支 `r218-evidence/20261024`

本分支是**独立证据分支**（orphan，无父提交），只放交付证据包与口径说明。
**不包含 vllm-ascend 源码，不与任何上游功能 PR/代码分支混用。**

- 仓库：`nqz1997/vllm-ascend`（fork；上游为 `vllm-project/vllm-ascend`）
- 分支：`r218-evidence/20261024`
- 用途：让第三方可直接取回数据集/图表/归因材料与 SHA256 自校验包
- 记录日期：2026-10-24（UTC）

## 1. 分支内容（INDEX）

| 文件 | 大小 | SHA256 | 说明 |
|---|---:|---|---|
| `r218_perf_attribution_20261024r4.tar.gz` | 689,626 B | `ac7d8154147c76b4f7f94f08c6385415c85eb799115119799b6359ad69ef1fac` | **当前最新包**：119 文件；r3 全部 ＋ `capacity/`（容量修复分支/补丁/服务尺寸日志/24-24+17-17 电池/异步负对照）＋ `PR_ADVANCE_20261024.md` ＋ `MAIN_SERVICE_VERIFY` §7 |
| `r218_perf_attribution_20261024r4.tar.gz.sha256` | 106 B | — | 上述包摘要（包内不内嵌自身 sha） |
| `r218_perf_attribution_20261024r3.tar.gz` | 667,073 B | `f6f3a8d54f2424676a3b93d00be3693e1bda5089510eff1ad0cdc12e7489ca38` | 前版（**SUPERSEDED by r4，保留不删**）：109 文件；main 异步定位更正 |
| `r218_perf_attribution_20261024r3.tar.gz.sha256` | 106 B | — | 前版包摘要 |
| `r218_perf_attribution_20261024r2.tar.gz` | 665,691 B | `8d5d7c0346faae94b0dfe51d359665d9a7ebff6f55abdab95c11c8c7e456d8c7` | 前版（**SUPERSEDED，保留不删**）：109 文件；含 CANN 归因旧措辞 |
| `r218_perf_attribution_20261024r2.tar.gz.sha256` | 106 B | — | 前版包摘要 |
| `PERF_ATTRIBUTION_ADDENDUM_20261024.md` | 24 KB | — | 补充正文（与 r4 包内同一文件）：步级二次分析、时间分解、已证实/推测/未知、版本映射 |
| `MAIN_SERVICE_VERIFY_20261024.md` | 12 KB | — | main 服务验证（与 r4 包内同一文件）：§6 异步定位更正、§7 容量修复设备验证 |
| `r218_perf_attribution_20261024.tar.gz` | 644,624 B | `bde8f9e053056f101240b4b991606beeb9477cba21dcade982c0a61503618ba1` | 首版（**SUPERSEDED by r2，保留不删**）：104 文件；含 `SHA256SUMS` 逐文件自校验 |
| `r218_perf_attribution_20261024.tar.gz.sha256` | 104 B | — | 首版包摘要 |
| `R218_DIFF_20261023.md` | 6.8 KB | — | 一页差异说明：NOMIDE 口径、非互斥账本、10.0×→4.73×、MATH-500 措辞、main 状态 |
| `UPSTREAM_PR_STATUS_20261023.md` | 14.7 KB | — | 上游 4 个 Draft PR（#19577/#19568/#19569/#19570）CI/评审快照；main 移植与服务验证实况（§七/§八） |
| `README.md` | 本文件 | — | 索引、口径纪律、版本映射、取回与校验方法 |

包内目录结构（解包后 `r218_perf_attr_20261024r4/`）：
`docs/`（精度总表、限制、协议、审阅摘要）、`figs/`（吞吐对照、归因账本、四腿协议、三联图 png/svg/pdf、
本页两张 CSV）、`runs/bg1..bg5_*/`（逐腿 `perq.json`／`serve.log`／`gates.txt`／HBM 采样）、
`scripts/`（可重跑生成脚本，含 `r218_addendum_tables.py`）、`capacity/`（容量修复补丁、
服务尺寸日志、电池原始分析与复算 README）、
`R218_ONE_PAGE_CONCLUSION.md`、`R218_PERF_ATTRIBUTION_20261023.md`、`PERF_ATTRIBUTION_ADDENDUM_20261024.md`、
`R218_DIFF_20261023.md`、`PR_ADVANCE_20261024.md`、`MAIN_SERVICE_VERIFY_20261024.md`、`README.md`、`SHA256SUMS`。

### 版本保留策略

- 本分支保留 **r4（最新）**、**r3/r2/20261024（SUPERSEDED）**；均含包内 `SHA256SUMS`。
- `20261023`（103 文件，SHA256 `69e300b0980979691ef7f5dcd9fc7d8e0877c55311c0252ec33eed151198d894`）
  状态 SUPERSEDED，仍在交付服务器 `report_eval/evidence_pack/`；本分支不重复承载。
- 更早的精度战役包（`r218_evidence_20261022_*`，746 文件）归档在交付服务器，本分支不重复承载（体积原因）。
- 版本链：`20261023` → `20261024`（＋main 服务验证记录）→ `20261024r2`（＋补充归因）→
  `20261024r3`（＋异步定位更正）→ `20261024r4`（＋容量修复设备验证与 PR/异步报告）。

## 2. 口径纪律（引用前必读）

1. **同 GMU 与同总 HBM 是两种独立口径，不得混写。**
   - 同 `gpu_memory_utilization=0.75`：两模式均为 29.52 GiB KV 分配，池 **1,719,424 vs 214,912 tok = 8.00×**。
   - 但 HBM 峰 **93% vs 77%**（INT2 生成期每步多占 ~10.5 GiB 工作区），**8.00× 池不等于 8× 显存收益**。
   - 相近总 HBM 预算的公平对（80.6% vs 79.1%）：**4.27×**（956,032 vs 223,744 tok）。
2. **池容量/引擎并发打印不是实测最大可服务并发。** 引擎的 “746×/103×” 是
   `池 tokens ÷ (ctx+256)` 推算；本批**实测活跃 batch** 仅 2K/C32 与 16K/C8，16K 验证至 INT2 32 / BF16 16
   （BF16@32 物理不可行，池 16.92× < 32×16,640）。32 为 tested-not-max。
3. **精度与性能分账。** 精度数字只属于已测交付树组合（见 §3）；main 移植版默认异步
   **OPEN**（INT2 中层读路径；blocking 仅作时序判别，CANN 归因已撤回），其任何结论
   **不得引用**本包数字。
4. **归因账本非互斥、不配平 100%。** 单项消融差分在同一步内可重叠，重叠量未测；
   文中给出的是“未被任何已测门控覆盖”的下界，不是互斥残差，也不把未证实原因归为硬件下限。
5. **首次慢样本保留。** 2K INT2 首腿 104.39 s（prefill 离群）保留并标 SUPERSEDED；
   点估计为 3 次中位 49.31 s（→ 4.73×）。不因复跑更快而作废首次观测。

## 3. 版本映射（包 ↔ 代码身份 ↔ 证据 ↔ 适用口径）

| 包版本 | 代码身份 | 运行时/姿态 | 证据文件 | 适用口径 |
|---|---|---|---|---|
| `20261024r4`（最新） | 同上 | 同上 | r3 全部 ＋ `capacity/`（`oscar-int2/capfix-int2-spec` 分支补丁、服务尺寸日志、24/24+17/17 电池、异步负对照）＋ `PR_ADVANCE_20261024.md` ＋ `MAIN_SERVICE_VERIFY` §7 | 交付树精度/吞吐/归因；容量修复为 **main 单列诊断结果**，不混入交付树 |
| `20261024r3`（SUPERSEDED） | 同上 | 同上 | r2 全部 ＋ main 异步定位更正（`MAIN_SERVICE_VERIFY` §6、addendum 版本边界、差异页 OPEN 口径） | 交付树精度/吞吐/容量/归因；**main 数字不适用** |
| `20261024r2`（SUPERSEDED） | 交付树 **v4 PR-22 tip `983fbac1`**（≡ 已测 `ov_restore` overlay）；`attention_v1.py` sha `85051bbd2e74c117`；冻结内核 md5 `c8a8d47a63be7ad7`（`OscarInt2FusedAttnInt2Lse`，vendor `oscar_r144_v133c_grp`）；launcher `int2_lse_fast_r152` | `oscar-r103-runner` 容器，CANN 9.0.0 / vLLM 0.22.1 引擎，Qwen3-8B 单卡 dev7；**eager**、前缀缓存关、block 128、MNBT 8192、greedy、64 tok/请求 | 20261024 全部 ＋ `PERF_ATTRIBUTION_ADDENDUM_20261024.md` ＋ `figs/PERF_ATTRIBUTION_ADDENDUM_20261024.csv`、`figs/PERF_STEP_STATS_20261024.csv` ＋ `r218_addendum_tables.py` | 交付树精度/吞吐/容量/归因；**main 数字不适用** |
| `20261024`（SUPERSEDED） | 同上 | 同上 | 20261023 全部内容 + `MAIN_SERVICE_VERIFY_20261024.md`（main 服务验证）+ 差异页 §5/§6 更新 | 同上（不含补充归因） |
| `20261023`（SUPERSEDED） | 同上 | 同上 | 四腿 + 复跑、2K/16K 消融、账本 v2、吞吐对照、一页结论 | 同上（除 main 验证记录） |
| **main 移植（单列，OPEN）** | `nqz1997/vllm-ascend` `oscar-int2/m-port-full-ut` @ `81295d899`（main 基 `dde85f6b8`）；`attention_v1.py` sha `704cf4e0c3a7fa5a`；同一冻结内核 md5 `c8a8d47a63be7ad7`；launcher 同 r152；容量修复另支 `oscar-int2/capfix-int2-spec` @ `d1db5264`（本地 `d67b3a0b1`） | 上游 nightly 镜像 `nightly-ci-main-a2-openeuler`（digest `sha256:8eaf0b4f…`），CANN 9.2.0 / torch 2.10.0+cpu / torch_npu 2.10.0.post7 / vLLM 0.31.0 @ `db9527a4`；NPU 7 | `MAIN_SERVICE_VERIFY_20261024.md`；补丁 `main_port_runtime_fixes.patch` sha256 `c227321d…`；`capacity/int2_capacity_fix.patch` sha256 `8289c8bf…` | **仅**构建/import/BF16 冒烟/隔离 UT 135（容量支 142）+ 串行化发射 41/41；默认异步 18/24 损坏，最小复现 B=1 1080 tok 5/12 vs blocking 0/12，定位 INT2 中层读路径、**OPEN**；容量修复在独立支验证 306,432→849,280 tok（2.77×；BF16 5.54×）、blocking 41/41，**未合入/未正式姿态复跑**；不标生产可用，不引用交付树精度/性能 |

## 4. 取回与校验

```bash
# 方式 A：直接取分支文件（raw）
BASE=https://raw.githubusercontent.com/nqz1997/vllm-ascend/r218-evidence/20261024
curl -fL -O "$BASE/r218_perf_attribution_20261024r4.tar.gz"
curl -fL -O "$BASE/r218_perf_attribution_20261024r4.tar.gz.sha256"
# 首版（追溯用，可选）：
# curl -fL -O "$BASE/r218_perf_attribution_20261024.tar.gz"

# 方式 B：浅克隆分支
git clone --depth 1 --branch r218-evidence/20261024 \
  https://github.com/nqz1997/vllm-ascend.git r218-evidence

# 校验 1：包摘要
sha256sum -c r218_perf_attribution_20261024r4.tar.gz.sha256

# 校验 2：包内逐文件（118 项）
mkdir r218_pack && tar xzf r218_perf_attribution_20261024r4.tar.gz -C r218_pack
cd r218_pack/r218_perf_attr_20261024r4 && sha256sum -c SHA256SUMS
```

分支文件页：<https://github.com/nqz1997/vllm-ascend/tree/r218-evidence/20261024>
GitHub API 树：`https://api.github.com/repos/nqz1997/vllm-ascend/git/trees/r218-evidence/20261024?recursive=1`

## 5. 边界

- 本分支**不含**产品源码补丁、PR 正文或 DCO 签署；上游贡献以
  `vllm-project/vllm-ascend` 的 4 个 Draft PR 为准（见 `UPSTREAM_PR_STATUS_20261023.md`）。
- 客户 `oscar-int2/pr-e2e` 仍预留，未建 PR。
- 未修改宿主驱动/CANN/系统 OPP；PROMOTION=NO。
- 证据分支只追加、不重写历史；包版本更新时保留旧包并标注 SUPERSEDED。
