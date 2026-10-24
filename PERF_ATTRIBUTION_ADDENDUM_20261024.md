# R218 吞吐归因补充（2026-10-24）— 2K/C32 未归因 decode 的二次分析与时间分解

> **版本边界（先读）**：本页所有性能数字只属于**已测交付树组合**——框架 v4 PR-22 tip `983fbac1`
> （树 ≡ 已测 `ov_restore` overlay；`[R218ID] attention_v1` sha `85051bbd2e74c117`）＋**冻结内核**
> `md5=c8a8d47a63be7ad7`（vendor `oscar_r144_v133c_grp`）＋launcher `int2_lse_fast_r152`＋**eager**。
> main 移植版（`m-port-full-ut @ 81295d899`）**默认异步正确性 OPEN**（INT2 中层读路径；
> blocking 仅作时序判别，CANN 归因已撤回，见 `MAIN_SERVICE_VERIFY_20261024.md` §6），
> 其任何数字不得引用本页。
>
> 本页是 `R218_PERF_ATTRIBUTION_20261023.md` 的**补充**，不重写主文、不改动已有数值。新增内容只有：
> ① 证据包上 GitHub 的取回与校验；② 用**已有** `perq.json`/`serve.log` 做的步级二次分析；
> ③ 按报告需要的类别时间分解（已证实/推测/未知三档）；④ 版本映射。
> r2 轮**没有跑新的 NPU 腿**（原因见 §5）；**2026-10-24 晚 sub-B 轮补采了 2 条
> profiling 腿（§10，只覆盖 2K/C32 decode 稳态步）**，其数字一律标注为新增、单独分列。

---

## 0. 本轮产物与一句话结论

- 证据分支（独立 orphan，不含源码）：`nqz1997/vllm-ascend` @ `r218-evidence/20261024`
  （HEAD 见分支页）；远端重下/API 核验通过（见 §7）。
- 新表：`figs/PERF_ATTRIBUTION_ADDENDUM_20261024.csv`（44 行）、`figs/PERF_STEP_STATS_20261024.csv`
  （4 行），生成器 `r218_addendum_tables.py`（只读 `runs/`、`figs/`、`opbench_delivered.json`）。
- 新包：`evidence_pack/r218_perf_attribution_20261024r2.tar.gz`（109 文件，本页与两张 CSV 在内；
  摘要见包旁 `.sha256` 与证据分支 `README.md`，本页不自引用包摘要）。
- **一句话**：2K/C32 的 38.89 s 总差里，已测门控按面值至多覆盖 3.80 s（≤9.8%），
  即 **35.10 s（90.2%）未被任何已测门控覆盖（差分观察，非下界）**；本轮把这一步细化到
  **每个 decode 步 483.9 ms**，并证明其中 **~470.5 ms/步在跳过中段算子执行之后仍然存在**。
  两个工作点的多余时间归一化后均为 **7.396 / 7.445 µs 每 KV token 每步**（吻合 0.7%），
  与 ∝C×ctx **兼容**——但两点不足以证线性标度律，**撤回**原先
  “逐 token 串行处理链签名 / ≈2.5 GB/s 每层带宽”的机制性宣称（见 §1.2 更正）。
  **2026-10-24 晚间（§10）已补采算子级 trace**：2K 的每步构成首次获得直接测量。

---

## 1. 已有数据能解释到什么程度（先列边界，再谈数值）

### 1.1 两点总账（口径不变）

| 点 | INT2 墙钟 | BF16 墙钟 | 总差 | prefill+排队差 | decode 差 | 输出吞吐比 |
|---|---:|---:|---:|---:|---:|---:|
| 2K/C32 | 49,309.9 ms（3 腿中位） | 10,415.3 ms（2 腿） | **38,894.6 ms** | 8,411.3 ms（21.6%） | **30,483.3 ms**（78.4%） | **4.73×** |
| 16K/C8 | 113,493.1 ms（2 腿） | 19,399.8 ms（2 腿） | **94,093.3 ms** | 32,554.6 ms（34.6%） | **61,538.7 ms**（65.4%） | **5.85×** |

`wall = prefill+排队 + decode span`，decode span = 每请求 first→last
（64 输出 token = 63 个间隔）。**口径更正（2026-10-24 晚）**：`batch wall − 逐请求 decode
span 中位数`得到的"prefill+排队"只是**统计代理量**；在 chunked prefill 与 decode 重叠的
调度下（见 §2.1），两段并非不相交的真实阶段拆分，逐项相加不构成严格的阶段分解。
表中数值照旧，仅解释降级。**2K 首条单跑腿 104.39 s（prefill 离群）保留并标 SUPERSEDED**，
本页一律用 3 腿中位 49.31 s；不因复跑更快而作废首次观测。

### 1.2 步级标度律（本页的定量支点）

| 点 | 实测步差 | 每步 KV token 数* | 每 KV token 每步 | 每层每 token | 折算每层带宽** |
|---|---:|---:|---:|---:|---:|
| 2K/C32 | **483.86 ms/步** | 65,424 | **7.396 µs** | 0.2054 µs | 2.49 GB/s |
| 16K/C8 | **976.80 ms/步** | 131,196 | **7.445 µs** | 0.2068 µs | 2.48 GB/s |

\* `n_in + C×31.5`（prompt + 生成中段），与主文 §4b 一致。
\*\* 每 KV token 按 512 B（2×8 kv head×128 dim×2 bit）计；`512 B ÷ (每层每 token µs)`。
**解释降级（2026-10-24 晚，撤回机制性宣称）**：两个工作点归一化后每 token 差 0.7%
只证明**两点与 ∝C×ctx 兼容**；仅凭两个工作点不足以确立线性标度律，
也**不构成**“逐 token 串行处理链签名”或“≈2.5 GB/s 每层带宽”这类机制结论——
2.5 GB/s 只是该假设下的折算量，不是实测带宽，也不是处理模式证据。
“不是读带宽受限”的旧推断同样依赖该机制假设，一并降级为**待证**。
（后续 §10 的算子级 trace 对 2K 的每步构成给出了直接测量，可作对照。）

### 1.3 现有门控的覆盖（不改主文数字）

| 点 | 已测门控按面值可覆盖 | 未被任何已测门控覆盖（差分观察） | 其中 decode | 其中 prefill+排队 |
|---|---:|---:|---:|---:|
| 2K/C32 | ≤3.80 s（≤9.8% 总差；整腿代数和 3.13 s / 8.0%） | **35,098 ms（90.2%）** | 28,221 ms（**447.95 ms/步**） | 6,877 ms |
| 16K/C8 | NOMIDE 52.96 s + NOSLIDE2 0.49 s = 53.45 s（至多 56.8%） | **40,644 ms（43.2%）** | 16,715.5 ms（**265.33 ms/步**） | 23,928.7 ms |

**这不是互斥账本。** 门控在同一步内可重叠，重叠量未测；**措辞更正（2026-10-24 晚）**：
非加性消融的按面值扣除之和不构成严格下界，上表“未被覆盖”列应读作
**“未被任何已测门控覆盖的差分观察”**，而非“至少这么大”的下界证明。
不追求 100%，也不把未覆盖部分归为硬件下限。

### 1.4 一个决定性的新观察（只用已有 perq 数据）

**跳过中段算子执行后，2K 仍然每步慢 470.5 ms。** 直接由两条已有腿相减：

| 点 | INT2 基线步 | INT2 NOMIDE 步 | BF16 步 | NOMIDE 后剩余步差 | 占原点步差 |
|---|---:|---:|---:|---:|---:|
| 2K/C32 | 603.17 ms | 589.82 ms | 119.31 ms | **470.51 ms** | 97.2% |
| 16K/C8 | 1,164.47 ms | 454.23 ms | 187.67 ms | **266.58 ms** | 27.3% |

也就是说：**2K 下“中段算子执行”只解释了 13.35 ms/步（占步差 2.8%），
剩下 470.5 ms/步发生在这个算子之外**；16K 下该算子解释了 710.2 ms/步，
仍剩 266.6 ms/步。这与主文“2K/C32 没有单一主项、≥90% 未覆盖”完全一致，
但把“未覆盖”锚定到了**每步**，而不只是一个总数。

> NOMIDE 腿输出错误（2K 0/32、16K 0/8），**只作诊断限制**。且其早退点在
> **载体（Kc/Vc）已组装、fill/gather 已完成之后**（`middle_exec.py:1290-1385`），
> 所以它删不掉读侧 gather/dequant，也删不掉写侧打包。
> 这也解释了为什么它只减 13 ms/步而减不掉 470 ms/步。

---

## 2. 采样结构、active batch、探针开销（引用前必须知道）

| 项 | 2K/C32 | 16K/C8 |
|---|---|---|
| 实测活跃 batch | **32**（`Running: 32`） | **8**（`Running: 8`） |
| 每请求输出 | 64 token（greedy，无早停） | 64 token |
| 计时单位 | 每请求 first→last（63 间隔） | 同 |
| 引擎统计采样间隔 | **10 s**（vLLM `loggers.py`） | 10 s |
| 探针开销 | **0**（`R197_PROBE=0`，诊断全关；无额外文件 IO） | 0 |
| 请求首 token 到达跨度（批内） | INT2 **9,818 ms** / BF16 **4,390 ms** | INT2 **35,445 ms** / BF16 **12,051 ms** |
| 每请求 span 中位（各腿汇总） | INT2 37,999.8 ms / BF16 7,493.7 ms | INT2 71,688.9 ms / BF16 11,051.2 ms |
| span IQR（汇总各腿） | INT2 35,477.9–39,415.5 / BF16 6,520.1–8,464.0 | INT2 63,505.1–79,210.5 / BF16 7,572.1–14,497.0 |
| 引擎吞吐交叉核对 | INT2 55.5–55.7 tok/s ÷32 = **575–577 ms/步** | INT2 8.4 tok/s ÷8 = **952 ms/步** |

关键解释（新）：

1. **chunked prefill 使 decode 与 prefill 重叠。** MNBT=8192，2K 每请求约 2,013 token，
   一次 prefill 只能纳入约 4 个请求；16K 每请求 16,368 token，单个请求需 2 个 chunk。
   因此首 token 跨度达 9.8 s / 35.4 s，**早期请求的 decode 段包含与后续 prefill 的争用**。
   逐请求 span 的 IQR 很宽（2K INT2 35.5–39.4 s），正是这种重叠的表现。
2. **span-based 步时是“批平均”，不是纯稳态。** 2K 的 603 ms/步 与引擎 10 s 窗口给出的
   575–577 ms/步 相差 4.6%；16K 的 1,164 ms/步 与引擎窗口 952 ms/步 相差 22%。
   **本页的标度律与账本沿用主文的 span-based 口径**，以保持与已发布数字逐项可比；
   引擎窗口只作交叉核对，不替换。BF16 16K 的单个引擎样本（4.0 tok/s）横跨请求结束，
   **不作稳态证据**。
3. 本页 span 用的就是主文的口径：**每腿取 span 上中位数，再对腿取中位**
   （2K INT2 三腿 37,637.5/38,214.8/37,999.8 → 37,999.8；BF16 两腿 → 7,516.5；
   16K INT2 两腿 → 73,361.7；BF16 两腿 → 11,822.9），与账本逐项一致。
   CSV 里另给“汇总各腿的 IQR/min/max”，只用于展示批内分布，不替换账本数字。

---

## 3. 时间分解：INT2 相对 BF16 多出的时间（按报告类别）

下表按报告需要的类别给出**每个全 batch 步**的多余时间。**不是互斥账本，不能相加到 100%。**
数值来源分三档：`实测`=已有门控腿直接差分；`微基准`=同内核直调 ×36 层（不在服务内）；
`未知`=现有门控无法删除。

### 3.1 2K/C32（原点步差 483.86 ms/步；总差 38,894.6 ms）

| 类别 | 每步多余时间 | 占原点总差 | 来源 | 置信档 | 重叠/限制 |
|---|---:|---:|---|---|---|
| 共享模型计算（BF16 基线步时） | 119.31 ms/步（**参照，不计入“多余”**） | — | 已有 BF16 腿 | 实测 | 两模式共同支付 |
| **middle 执行**（跳过中段算子执行的墙钟差分） | **24.25 ms/步**（墙钟口径）；decode 13.35 | 3.9%（墙钟） | NOMIDE 腿 | 实测（诊断，输出错） | 早退点在载体组装之后 |
| **操作数/载体准备**（gather/fill/pack） | **未测** | — | `middle_exec.py:1290-1385` | 未知 | 无门控删除它；是 470 ms 残差的首选候选 |
| **旋转/量化**（新 token 写侧） | 32.18 ms/步（微基准 ×36） | 5.2% | `opbench_delivered.json` | 推测（直调外推） | 服务内可能被流水/重叠；未在端到端中删除过 |
| **S+R（前缀+近期窗口）** | 3.27 ms/步 | 0.5% | NOSRSTAGE | 实测 | 单门控 |
| **环维护/搬运（slide2）** | 28.90 ms/步（墙钟）；decode 22.56 | 4.7% | NOSLIDE2 | 实测 | 单门控；与 staging 同段可重叠 |
| **G stage 换路** | −6.66 ms/步（**更慢**） | −1.1% | NOGSTAGE | 实测 | 换路不是删除 |
| **合并（merge）** | 未跑 | — | `R155_T_NOMERGE` 存在但本批未用 | 未知 | 需一次额外腿 |
| **host 等待/逐层编排** | 未测 | — | eager，无 graph；无 host-only 门控 | 未知 | NOMIDE 后的 470 ms 是其上界包络 |
| **自定义算子直调 ×36** | 16.42 ms/步（attention）＋32.18（quant）= 48.60 | 7.9%（若串行） | 直调微基准 | 推测 | attention 与 NOMIDE 重叠；quant 未在服务内验证 |

**已测门控按面值的并集**：NOMIDE 1.53 s ＋ NOSLIDE2 1.82 s ＋ NOSRSTAGE 0.21 s ＝ 3.56 s
（9.2% 总差；整腿代数和 3.13 s / 8.0%，因 NOGSTAGE 为负）。若把 quant 微基准 2.03 s
也算进来（它不是端到端门控），**至多 5.59 s（14.4%）**。
**无论哪种算法，≥33.3–35.1 s（≥85.6%–90.2%）仍未被覆盖。**

### 3.2 16K/C8（原点步差 976.80 ms/步；总差 94,093.3 ms）

| 类别 | 每步多余时间 | 占原点总差 | 来源 | 置信档 | 重叠/限制 |
|---|---:|---:|---|---|---|
| 共享模型计算（BF16 基线步时） | 187.67 ms/步（参照） | — | 已有 BF16 腿 | 实测 | — |
| **middle 执行** | **840.68 ms/步**（墙钟）；decode 710.23 | **56.3%**（墙钟） | NOMIDE 腿 | 实测（诊断，输出错） | 16K 的最大单项 |
| **操作数/载体准备** | 未测（部分落在 NOMIDE 差分内） | — | 同上 | 未知 | NOMIDE 只跳 launch 之后的早退；fill 已发生 |
| **旋转/量化** | 31.54 ms/步（微基准 ×36） | 2.1% | 直调 | 推测 | 16K 下占比小 |
| **S+R** | 未测（16K 未跑 NOSRSTAGE） | — | — | 未知 | — |
| **环维护/搬运（slide2）** | 7.72 ms/步；decode 1.25 | 0.5% | NOSLIDE2 | 实测 | 16K 下很小 |
| **G stage / 合并 / host** | 未测 | — | — | 未知 | — |
| **自定义算子直调 ×36** | 16.78（attention）＋31.54（quant）＝48.31 | 3.2%（若串行） | 直调 | 推测 | 与 NOMIDE 重叠 |

**覆盖**：NOMIDE 52.96 s ＋ NOSLIDE2 0.49 s ＝ 53.45 s → 至多覆盖 56.8% 总差；
**≥40.64 s（≥43.2%）未被覆盖**（decode ≥16.72 s、prefill ≥23.93 s）。
加 quant 微基准 1.99 s（2.1%）后至多 58.9%，**仍 ≥38.7 s 未覆盖**。

### 3.3 prefill 侧（两模式共同的 per-token 链路也变差）

| 点 | INT2 prefill | BF16 prefill | 差 | 每输入 token（INT2/BF16） |
|---|---:|---:|---:|---:|
| 2K/C32 | 11,310.1 ms | 2,898.8 ms | 8,411.3 ms | **0.176 / 0.045 ms** |
| 16K/C8 | 40,131.4 ms | 7,576.9 ms | 32,554.6 ms | **0.306 / 0.058 ms** |

prefill 与 decode **同步变差**是重要约束：它把可疑面从“decode 专用路径”收窄到
**两种阶段共享的 per-token 链路**（载体读写、旋转/量化、host 逐层编排）。
这也是“每 KV token 固定开销”这一标度律能跨阶段成立的原因。

---

## 4. 三档结论（已证实 / 推测 / 未知）

### 4.1 已证实（直接测量，可复现）

1. 两点总差与墙钟拆分：38,894.6 ms / 94,093.3 ms；decode 占 78.4% / 65.4%
   （span 口径为统计代理量，见 §1.1 更正）。
2. **两工作点每 KV token 每步差 7.396 与 7.445 µs（差 0.7%）**：这是两点实测量的
   归一化一致性，**不是已证实的标度律**；“每层 ~0.205 µs / ~2.5 GB/s”仅为该假设下的
   折算量（机制宣称已撤回，见 §1.2）。
3. **NOMIDE 差分**：2K 24.25 ms/步（墙钟，3.9%）、16K 840.68 ms/步（墙钟，56.3%）。
4. **NOMIDE 后剩余步差**：2K **470.51 ms/步**（97.2% 原点步差）、16K **266.58 ms/步**。
5. slide2：2K 28.90 ms/步（4.7%）、16K 7.72 ms/步（0.5%）；SR stage 2K 3.27 ms/步（0.5%）；
   G stage 换路更慢（−6.66 ms/步）。
6. 未被任何已测门控覆盖的差分观察：2K **35,098 ms（90.2%）**、16K **40,644 ms（43.2%）**
   （非加性消融之和不构成严格下界，见 §1.3 更正）。
7. 生成期额外 **~10.5 GiB** 工作区（HBM 93% vs 77%），只在 decode 平台期出现。
8. 批内首 token 跨度与 span 分布（§2），证明 decode 与 chunked prefill 重叠。
9. 直调微基准：attention 0.456/0.466 ms、quant 0.894/0.876 ms（sync-per-call）。

### 4.2 推测（有数值支撑，但不是端到端证明）

1. **写侧旋转/量化**每步约 31.5–32.2 ms（×36 层外推）。它 ∝C、不 ∝C×ctx，
   因此**不足以解释 2K 的 470 ms 残差**，但在 2K 是可观的小项（~6–7%）。
2. **自定义 attention 算子**直调 ×36 ≈ 16.4–16.8 ms/步；2K 下 NOMIDE 只暴露出
   13.35 ms/步，说明**并非全部算子设备时间都落在步的关键路径上**（或直调含同步开销、
   高估了设备时间）。两者不可直接相加。
3. **读侧载体 gather/dequant 是 2K 残差的首选候选**：它 ∝C×ctx、在 NOMIDE 早退点之前、
   与两点归一化一致性兼容（原“与 2.5 GB/s 串行处理率一致”的表述依赖已撤回的机制宣称）；
   但本批**没有能单独删除它的门控**，故只是候选（§10 的 trace 对此有新证据）。
4. host 逐层编排若为纯常数，应与 ctx 无关；实测强烈依赖 C×ctx，除非 host 成本正比于
   分块数/循环迭代数，否则不是主项。

### 4.3 未知（如实留白，不硬归因）

1. **2K ≥90%、16K ≥43.2% 的未覆盖量**在三个候选（读侧 gather/dequant、写侧打包、host 编排）
   之间的**互斥切分**。需要算子级 trace 或“真正删掉载体组装”的对照。
2. **直调 vs 服务内的数量级矛盾**：16K 下 NOMIDE 差分 710 ms/步，而直调 attention
   ×36 只有 16.8 ms/步（42×）。可能来自服务内 block table 分散/填充、tiling 变化、
   或 NOMIDE 的下游连锁；**未查清**。（`middle_exec.py:1370` 的代码注释还记录了一个
   “R201 probe dev 9.6–9.9 ms/layer，B=3..31 平坦”的旧数据；该 probe 原始输出未找到、
   姿态也不同，**不作为证据**，只作为待核对的线索。）
3. **合并（merge）成本**：本批未跑 `R155_T_NOMERGE`。
4. **host 等待**与**设备计算**在 470 ms/步内的比例。
5. **2K 首条腿 prefill 离群（104.39 s，复跑 11.31 s）根因**。
6. 7.4 µs/token 的标度律目前只有**两个工作点**（2K/C32、16K/C8），不能外推到其他
   ctx/并发组合；也不能据此宣称“没有原生 INT2 所以不可能更快”或“内核地板”。

---

## 10. 2026-10-24 晚间补充（sub-B profiling 腿）：2K/C32 decode 步的算子级构成

> 本节为**新增测量**，与前文既有数字分列：前文所有数值一律未改。本节只覆盖
> **2K/C32 一个工作点**的 decode 稳态步，不外推 16K。

> **⚠ 更正（2026-10-24 深夜，第 4 波 sub-B）**：本节 §10.2–§10.4 原文中把
> **profiler-OFF 步墙钟**与 **profiler-ON kernel 并集**混在一个等式里（"host/发射间隙 =
> 墙钟−kernel 并集"），并由此得出"步差≈Δkernel+Δhost 各半"“NOMIDE 被 host 遮蔽”等
> 结论——这些是**跨测量条件的混合量**，不是直接测得的步构成。按裁定全部撤回/降级，
> 更正后口径见 **§10.5**（原文按 append-only 原则原样保留，仅加指针）。

### 10.1 协议与身份（bg6 两条腿）

- 腿：`runs/bg6_prof_int2_2k_c32`（mode B）与 `runs/bg6_prof_bf16_2k_c32`（mode N），
  由 `profiling_20261024/r218rp_prof_leg.sh` 驱动——与冻结 `r218rp_leg.sh` thrcap 腿
  **同包络同参数**（NS=32、ctx=2048、GMU=0.75、MNBT env=0→引擎缺省 8192、points="32"、
  eager、ASCEND_LAUNCH_BLOCKING=0 异步）。
- 唯一增量（profiling 腿专用，不回写交付资产）：① `R118_SC` 指向
  `profiling_20261024/sitecustomize_r218prof`（链式加载原 R137→R114 sitecustomize，
  另装 profiler 钩子）；② CAN 用副本 `r218_report_eval_prof.py`
  （=冻结 `r218_report_eval.py` +31 行幂等注入，见 `profiling_20261024/CAN_DIFF.txt`）。
  **overlay 文件零改动**。
- 身份门全绿：`[R218ID] attention_v1 sha 85051bbd2e74c117`（ov_restore）、内核
  `md5=c8a8d47a63be7ad7`、KV 池 1,719,424 / 214,912 tok、`Running: 32 reqs`、
  `enforce_eager=True`、两腿命中 32/32。
- 采样：`torch_npu.profiler`（activities=CPU+NPU）包住
  `vllm_ascend NPUModelRunner.execute_model`，**门控在纯 decode 步**
  （`total_num_scheduled_tokens==32`，排除一切 chunked-prefill 混排步），
  warm 10/6 步后采 **12 步**（INT2 步 n=20..31、BF16 n=16..27，EngineCore
  pid 5724/6692，钩子生命周期见各腿 `prof_steps.jsonl`）。
- **探针开销（同腿前后对照，n=43 个未采样步 vs n=12 个采样步中位）**：
  INT2 **+197.67 ms/步**（764.72 vs 567.05；+34.9%）、BF16 **+21.24 ms/步**
  （110.98 vs 89.74；+23.7%）。采样腿的 batch wall 含约 60 s 的 trace 导出停顿
  （INT2 111.4 s / BF16 37.8 s），**不可作吞吐口径**；吞吐仍以冻结腿为准。

### 10.2 decode 稳态步构成（探针关，n=43 步中位；kernel union 为全流区间并集）

| 量 | INT2 | BF16 | 差（INT2−BF16） |
|---|---:|---:|---:|
| 纯 decode 步墙钟（中位） | **567.05 ms** | **89.74 ms** | **477.31 ms** |
| NPU kernel 时间（并集/12 步） | **266.39 ms** | **28.95 ms** | **237.44 ms** |
| host/发射间隙（墙钟−kernel 并集） | **300.66 ms** | **60.79 ms** | **239.87 ms** |
| 图：`figs/PERF_PROFILING_STEP_20261024.png`；逐 op：`figs/PERF_PROFILING_20261024.csv` | | | |

> ⚠ 本段及上表"host/发射间隙"行为跨条件混合量，已于第 4 波撤回（§10.5）；原文如下保留。

两个模式在 eager 下都**同时**有可观的 kernel 时间与 host 间隙；2K 的步差
（纯 decode 口径 477.31 ms）**近似对半**来自 Δkernel（+237.4）与 Δhost 间隙（+239.9）。
注意：纯 decode 步墙钟（567/89.7 ms）与前文 span 口径步时（603/119 ms）不同——
span 口径含 chunked-prefill 混排步，两者分列、不可互换。

### 10.3 kernel 级分解（每步，12 步合计/N；NPU kernel 总时间占比）

| op（trace 直接命名） | INT2 ms/步（占 kernel） | BF16 ms/步（占 kernel） | 备注 |
|---|---:|---:|---|
| **OscarInt2FusedAttnInt2Lse**（冻结中层核） | **209.25（78.3%）** | — | 432 次=12 步×36 层；**单次 5.81 ms** |
| FusedInferAttentionScore（非中层注意力路径，疑 S+R 档） | 5.09（1.9%） | **12.64（43.7%）** | BF16 的主注意力核 |
| aclnnMatmul…MatMulV2 | 19.66（7.4%） | 13.31（46.0%） | INT2 调用数为 BF16 的 2.00×（3468 vs 1740），未查因 |
| aclnnCat…ConcatD | 11.77（4.4%） | —（BF16 无此项进前 10） | |
| aclnnMuls…Muls | 7.55（2.8%） | — | |
| 其余（RmsNorm/SwiGlu/rope/拷贝类/未映射，逐 op 见 CSV） | ~13（~4.9%） | ~3.0（~10%） | 名称→类别的映射为启发式，逐 op 保留原名 |

**读法（非加性提醒）**（⚠"kernel 并集+host 间隙=步墙钟"的互补性说法已撤回，见 §10.5）：
kernel 内部各类为**命名求和**，多流重叠在本腿可忽略（并集 266.39 ≈ 求和 267.11）。

### 10.4 对 §3/§4 悬案的直接回答与新增未知（⚠ 第 1/2 条的因果表述已降级，见 §10.5）

1. **§4.3.2 的“直调 vs 服务内数量级矛盾”在 2K 定量闭合**：服务内单次 5.81 ms vs
   直调微基准 0.456 ms（**12.7×**）。差距本身已实测，但**成因未查**（block table 布局/
   tiling/批形状差异，仍是未知）。
2. **NOMIDE 只省 13 ms/步的原因**：2K 步是 host 间隙主导（300.7/567.1=53%），删掉
   209 ms 的中层 kernel 大部分被 host 时间**遮蔽**（墙钟只降 13.35 ms）；16K 时 kernel
   时间超过 host 时间，NOMIDE 才显出 710 ms/步。即“NOMIDE 后剩余 470.5 ms/步”中
   约一半是**未被遮挡的 kernel 时间**（≈209 ms 中层核 + 其他 kernel 差）、约一半是
   host 间隙差。**§4.2.4“host 编排应与 ctx 无关”的推断被证伪**：host 间隙本身
   INT2 300.7 ms vs BF16 60.8 ms（同 ctx 同 batch），差 239.9 ms。
3. **仍未知**：① host 间隙 300.7 ms 的内部构成（Python/发射/同步等待，cpu_op 事件
   嵌套不可加，未作分解）；② 非 Oscar kernel 的类别归属（拷贝类 vs 计算 vs 未映射）
   只有启发式命名映射；③ INT2 每层多出的 matmul 调用（×2）来源；④ 16K 未采 trace，
   本节不外推。

### 10.5 更正（2026-10-24 深夜，第 4 波 sub-B，本轮终版）：测量条件分列，撤回跨条件混合量

> 裁定与更正依据：§10.2/§10.3/§10.4 原文把 **profiler-OFF** 的步墙钟与 **profiler-ON**
> 的 kernel 并集放进同一个等式。r5 生成脚本 `make_prof_outputs.py`（旧行 :34/:35/:51/:152，
> 备份于 `figs/_backup_20261024r5/`）以 `median(profiler-OFF 墙钟) − (profiler-ON kernel
> union / 12)` 命名为 "host/launch gap"。两量来自**不同测量条件**（探针开销 INT2
> +197.7 ms/步本身就是两条件差的量级），其差**不是直接测得的步构成**。以下四条撤回/降级。

**撤回/降级清单（原文 → 新表述）**

| # | 原文（r5） | 处置 | 新表述 |
|---|---|---|---|
| R1 | "host/发射间隙 INT2 300.66 / BF16 60.79 ms＝墙钟−kernel 并集"（§10.2 表行，及堆叠图） | **撤回为直接测量** | 该差是跨条件混合量。同条件下的正确量见下表：profiler-ON 窗口内设备空闲 INT2 502.1 / BF16 85.8 ms/步（含探针开销）；profiler-OFF 条件**无设备时间数据**，其"kernel 之外残差"不可得，只可中性记作"trace 未覆盖残差（条件混算，deprecated）" |
| R2 | "步差≈Δkernel 237.4＋Δhost 239.9，近似对半"（§10.2 尾段、图注） | **撤回** | 唯一成立的分列：Δwall(OFF)=477.31（同条件）；Δkernel(ON)=237.44（同条件）。"各半"来自把两个不同条件的差强行相加；代数上 Δ"host"=Δwindow(ON)−Δunion(ON)−Δ探针−Δ未计时段——含"探针开销可加性"假设，非测量 |
| R3 | "NOMIDE 只省 13 ms/步的原因＝host 间隙 300.7 ms 遮蔽 kernel 时间"（§10.4.2） | **降级为未证** | 撤回"遮蔽"这一已定论归因（无 NOMIDE 配对时间线/关键路径证据，且 R1 已撤）。保留事实：NOMIDE 差分 2K 24.25 ms/步（§4.1.3 实测）vs 中层核 ON 条件 209.25 ms/步；两者关系是**待解释的观测**，不是结论 |
| R4 | "host 间隙 INT2 300.7 vs BF16 60.8（同 ctx 同 batch）⇒ 证伪'host 编排与 ctx 无关'"（§10.4.2） | **撤回推理** | 同 ctx 的 INT2/BF16 host 侧差不能证明 host 成本随 ctx 变化（两模式 host 链路不同：INT2 有 36 层×每层额外 carrier/cat/muls 发射）。§4.2.4 的证伪撤回，问题回到 OPEN |
| R5 | "服务内单次 5.81 ms＝直调 0.456 ms 的 **12.7×**"（§10.4.1） | **降级为场景间观测比** | 两场景条件见下文"两场景条件对照"；12.7× 只是观测比，不构成"同一负载下服务放大 12.7×"的结论，成因未查 |

**三分类呈现（本轮替换 §10.2 表；`figs/PERF_PROFILING_20261024.csv` measurement_condition 列）**

| 条件 | 量 | INT2 | BF16 | n |
|---|---|---:|---:|---|
| ① profiler OFF | execute_model host 墙钟中位 [p25–p75] | **567.05** [563.17–571.55]（min 559.81/max 608.26） | **89.74** [88.86–91.12]（min 86.87/max 94.82） | 43/43 |
| ① 同条件差 | Δwall(OFF) | **+477.31** | — | — |
| ② profiler ON | execute_model 墙钟中位 | 764.72 [762.42–769.09] | 110.98 [110.65–114.11] | 12/12 |
| ② profiler ON | 12 步窗口跨度/步（首 kernel 起→末 kernel 止） | 768.50 | 114.75 | 12/12 |
| ② profiler ON | NPU kernel 并集/步 | **266.39** | **28.95** | 78,364/7,383 事件 |
| ② profiler ON（新增） | 窗口内设备空闲/步（窗口−并集；含探针开销） | **502.12（65.3% 空闲）** | **85.81（74.8% 空闲）** | 12/12 |
| ② 同条件差 | Δkernel(ON)、Δwindow(ON) | **+237.44**、+653.75 | — | — |
| ③ 观测开销 | median(ON)−median(OFF)（同腿） | **+197.67（+34.9%）** | **+21.24（+23.7%）** | 12 vs 43 |
| deprecated | r5 "host gap"（条件混算） | ~~300.66~~ | ~~60.79~~ | — |

读法纪律：①与②不可互减/相加构成"步构成"；②内窗口空闲是 **ON 条件**观测（含探针，
且窗口含未计时段 sample_tokens/调度 ≈3.8 ms/步）；OFF 条件下设备占用**未测**。
新图 `figs/PERF_PROFILING_STEP_20261024.png`（三面板分列，无堆叠构成）；
r5 堆叠图与 78 行 CSV 备份于 `figs/_backup_20261024r5/`，逐项取代关系见
`figs/PERF_PROFILING_20261024_SUPERSEDED_MAP.md`。

**B2：execute_model 计时是否覆盖设备完成——不可判定为"覆盖"；"＝设备完成口径步时"的读法不成立**

- 计时对象：钩子只包 `NPUModelRunner.execute_model`（`r218prof_hook.py`，
  `orig = cls.execute_model`；prof_steps.jsonl 的 `ms`＝该调用的 host 墙钟）。
- 代码路径（ov_restore overlay `vllm_ascend/worker/model_runner_v1.py`）：本 fork 为
  两段式——`execute_model` 构造输入、发射 forward、存 `ExecuteModelState` 后
  `return None`（尾注 "Now the batch has been launched…"）；**常规返回路径无无条件
  `torch.npu.synchronize()`**（入口 `_sync_device` 仅在 profiling_chunk_config.
  need_timing 分支；R166_PFSYNC/R169 诊断默认关）。采样在 `sample_tokens()`，
  设备→主机同步落在其 `_bookkeeping_sync`（采样 id 的 D2H）——**在计时窗口之外**。
- 因此：第 N 步设备收尾**确定不在**第 N 步的计时内；稳态步周期还含未计时段
  （ON 条件实测 window−ON墙钟 ≈3.8 ms/步；OFF 条件未测）。
- 计时内是否含"隐式等待前序设备工作"（发射队列背压）：**离线不可判定**（trace 无队列
  深度记录）。所需证据形态：worker 级（execute_model+sample_tokens）墙钟、钩子内记录
  stream/event 完成时间戳、或系统级时间线（msprof）。
- 附：trace 窗口尾核查——最后一个 kernel 结束仅超出最后一个 cpu_op 结束 2.44 ms
  （INT2）/1.02 ms（BF16），只证明 profiler stop 时设备已近排空，不能反证计时含同步。

**两场景条件对照（R5 降级的依据；两者同一内核 md5 c8a8d47a63be7ad7）**

| 维度 | 服务内 5.81 ms/次 | 直调 0.456 ms/次 |
|---|---|---|
| 测量方式 | torch_npu profiler ON，chrome trace kernel 事件时长（432 次统计：min 5.78/med 5.81/max 5.85） | host 计时，**sync-per-call**（含每次同步开销），`runs/bg_nogain/opbench_delivered.json`（2026-10-23 dev6） |
| 负载形态 | 服务 decode 稳态：C=32、ctx≈2048（TT 帽 2K）、生产 paged block-table（R144 v133c grouped 路径、cap 32、GMU 0.75 池）、36 层×12 步与同层 cat/muls/matmul 交织 | 单算子微基准：B=32、S=1920、blocks=15 合成块表、空载邻居 |
| 未记录/不可比 | tiling 选择是否与服务内一致、stride/块表分散度、并发流、L2/流水状态 | 同左；且 sync-per-call 使 host 值非纯设备时间 |

**保留仍然成立的量**（本轮未动）：①类全部（OFF 墙钟分布，含同条件 Δ477.31）；
②类 kernel 并集/op 表（注明 ON 条件）与新增窗口空闲；③探针开销；NOMIDE/slide2/
SR/G 各门控差分（§4.1 原测值）；中层核 per-call 5.81（ON 条件）与 209.25 ms/步合计。

**仍未知（如实）**：OFF 条件设备占用；ON 窗口空闲内部的 launch/API/等待切分
（cpu_op 嵌套不可加）；12.7× 观测比的成因；16K 未采 trace。

---

## 5. 为什么 r2 轮没有新增 profiling（设备与边界）——**已于同日晚间由 sub-B 轮补采（见 §10）**

协议要求：任何 NPU 使用须 `flock /tmp/r218_npu7.lock`，**锁内先核实 NPU 7 空闲**，
且 profiling 不得与 A 线并行。2026-10-24 检查时：

- NPU 7：**HBM 41,165 / 65,536 MB，AICore 18%**（`npu-smi info`）；
- 容器 `r218-main-verify` 内 `VLLM::EngineCore` 在运行（A 线的 main 服务验证环境）；
- `npu-smi info -t proc-mem -i 7` 显示 “No process in device”——这是已知的
  **容器 PID 不可见**陷阱，不能据此判定空闲；
- 锁日志显示 A 线在 02:46–02:48 使用过 NPU 7；检查时无人持锁，但**设备被占用**。

因此**没有启动任何服务或 msprof**——既满足“不与 A 线并行”，也避免干扰他人的
`r218-main-verify` 容器。**本页没有伪造任何“新测量”**。

若后续拿到空闲的 NPU 7，最短路径（约 15–20 分钟）是：

```bash
# 在已测 overlay + 冻结内核上重放 2K/C32 一条腿，只开阶段探针：
R197_PROBE=1 ...（沿用 runs/bg2_int2_thrcap2k_c32 的同一组 env）
# 探针输出 /tmp/r197_probe.jsonl：ring / stage / q / fillop / glue / sr / tot + device event
```

该探针在交付 overlay 内已存在（默认关，`middle_exec.py:160-180, 327, 1145, 1274, 1728, 2188`），
只增加每层一次 `perf_counter` 与一对 device event，采样 72 次后每 40 次一次；
**在同一腿上先跑无探针基线、再跑探针腿**即可量化探针开销。
它能直接把 §4.3 的第 1、4 项切开；**仍切不开** NOMIDE 早退点之前的读侧 gather
（需要“真正删掉 fill”的对照，目前没有）。

---

## 6. 口径表维护（不改数）

### 6.1 精度（与 `ACCURACY_TABLE.md` 一致；无预设阈值，不作通过/失败判定）

核心六道（Δ=INT2−BF16）：GSM8K **+0.69**（93.18 vs 92.49，n=1319）、
C-Eval **−0.60**（78.45 vs 79.05，1346）、MATH-500 **0.00**（80.80 vs 80.80，500；
**总分相同 404/500 = 404/500，逐题 18 题退化 / 18 题改善**）、
GPQA-Diamond **−2.02**（45.45 vs 47.47，198）、HumanEval **−1.83**（84.76 vs 86.59，164）、
IFEval **−0.55**（81.52 vs 82.07，541）；简单平均 **−0.72 pp**。
扩展：MMLU-Pro +0.15、AIME25 20.0=20.0、LCB +0.44。
长上下文限制照实保留：**LB-E 36.83 vs 39.26（−2.43）**、RULER niah 每 30 题丢 1–2 针、
cwe@8192 0.33；**不写成无损、不写成全面通过**。

### 6.2 容量（两种口径独立表述，不混写）

- **同 GMU 0.75**：两模式同为 **29.52 GiB KV 分配**，池 **1,719,424 vs 214,912 tok = 8.00×**。
- **同总 HBM 预算**（80.6% vs 79.1%，±1.9%）：**4.27×**（956,032 vs 223,744 tok）。
- HBM 峰 **93% vs 77%** ⇒ INT2 生成期每步多占 **~10.5 GiB**；**8.00× 池 ≠ 8× 显存收益**。
- 引擎 “746×/103×” 是 `池÷(ctx+256)` 推算，**不是实测并发**；实测活跃 batch 仅 32（2K）
  与 8（16K）；16K 验证至 INT2 32 / BF16 16（BF16@32 物理不可行），**32 为 tested-not-max**。

### 6.3 吞吐（互不混用的协议）

| 口径 | 值 | 说明 |
|---|---|---|
| 同 GMU 端到端输出吞吐 | **4.73×（2K/C32）/ 5.85×（16K/C8）** | 本页主口径；墙钟含 prefill |
| 旧 2K 点 | **10.0× SUPERSEDED** | 单次 prefill 离群腿；保留可追溯，不作点估计 |
| 稳态 decode TPOT | **2.2–2.7×** | 单流稳态；不可与 4.73× 互换 |
| C=8 吞吐比随 ctx | **8.9× / 12.7× / 17.0×**（2K/8K/16K） | 另一协议 |
| e2e | **2.4–3.7×** | prefill 4–5× 为主 |

---

## 7. 交付、取回与校验（本轮实际执行）

| 项 | 值 |
|---|---|
| 证据分支 | `r218-evidence/20261024`（orphan，无父提交；不含 vllm-ascend 源码） |
| 分支创建 commit（首版） | `13d36345876bf65a3329c6899f8494129652810b`（r2 追加后 HEAD 见分支页） |
| 分支文件 | `r218_perf_attribution_20261024.tar.gz`＋`.sha256`（首版，保留）、`r218_perf_attribution_20261024r2.tar.gz`＋`.sha256`（含本页）、`R218_DIFF_20261023.md`、`UPSTREAM_PR_STATUS_20261023.md`、`README.md`（索引/口径/版本映射/取回） |
| 首版包（20261024）SHA256 | `bde8f9e053056f101240b4b991606beeb9477cba21dcade982c0a61503618ba1`（远端重下核验；104 文件） |
| 本页所在包（20261024r2） | 见分支 `README.md` 与包旁 `.sha256`（109 文件；摘要不在包内自引用） |
| 远端文件数 | **104**（包内 `SHA256SUMS` 103 项逐文件校验全过；第 104 项是 `SHA256SUMS` 自身） |
| 分支页 | <https://github.com/nqz1997/vllm-ascend/tree/r218-evidence/20261024> |
| 包直链 | <https://raw.githubusercontent.com/nqz1997/vllm-ascend/r218-evidence/20261024/r218_perf_attribution_20261024.tar.gz> |

校验命令（已在**从远端重新下载**的副本上执行）：

```bash
curl -fL -O https://raw.githubusercontent.com/nqz1997/vllm-ascend/r218-evidence/20261024/r218_perf_attribution_20261024.tar.gz
curl -fL -O https://raw.githubusercontent.com/nqz1997/vllm-ascend/r218-evidence/20261024/r218_perf_attribution_20261024.tar.gz.sha256
sha256sum -c r218_perf_attribution_20261024.tar.gz.sha256     # -> OK
tar tzf r218_perf_attribution_20261024.tar.gz | grep -v '/$' | wc -l   # -> 104
mkdir -p r218_pack && tar xzf r218_perf_attribution_20261024.tar.gz -C r218_pack
cd r218_pack/r218_perf_attr_20261024 && sha256sum -c SHA256SUMS         # -> 103/103 OK
```

> GitHub `github.com` 的 git 端点在本机曾出现 HTTP/2 framing 超时；本轮 `git push`
> 在重试后成功，并用 GitHub API 的 tree/ref 与 `raw.githubusercontent.com` 下载
> **双重核验**（ref SHA = 本地 commit；包 SHA 与文件数一致）。未动任何代码分支/PR。

---

## 8. 版本映射

| 包版本 | 代码身份 | 运行时 / 姿态 | 证据文件 | 适用口径 |
|---|---|---|---|---|
| **20261024r5**（本页 §10 所在包） | 交付树 v4 PR-22 tip `983fbac1` 同下；**profiling 增量不触 overlay**：`R118_SC`→`profiling_20261024/sitecustomize_r218prof`（链 R137→R114＋钩子）＋ CAN 副本 `r218_report_eval_prof.py`（冻结 CAN＋31 行幂等注入） | `oscar-r103-runner`、NPU 7（flock 全程，窗口 12:31–13:15 UTC）、其余同冻结腿；**采样**：纯 decode 步（tot==32）warm 10/6 后 12 步（INT2 n=20..31/BF16 n=16..27）；**探针开销 +197.67/+21.24 ms/步**；ASCEND_LAUNCH_BLOCKING=0 | `runs/bg6_prof_{int2,bf16}_2k_c32/`（trace 原件 229/18 MB、`prof_steps.jsonl`、gates、serve.log）、`figs/PERF_PROFILING_20261024.csv`、`figs/PERF_PROFILING_STEP_20261024.png`、`profiling_20261024/`（脚本+分析+smoke） | **仅** 2K/C32 decode 稳态步构成；不作吞吐、不外推 16K；采样腿 batch wall 含导出停顿不可用 |
| **20261024r3**（本页 §1–§9 在该包中） | 同下 | 同下 | 20261024r2 全部 ＋ main 异步定位更正（`MAIN_SERVICE_VERIFY` §6、本页版本边界） | 交付树；main 不适用 |
| **20261024** | 交付树 v4 PR-22 tip `983fbac1`（≡ `ov_restore`）；attn `85051bbd2e74c117`；kernel md5 `c8a8d47a63be7ad7`；launcher r152 | `oscar-r103-runner`，CANN 9.0.0 / vLLM 0.22.1，Qwen3-8B，dev7；**eager**；block 128、MNBT 8192、greedy、64 tok | 四腿＋复跑、2K/16K 消融、账本 v2、吞吐对照、一页结论、main 验证记录 | 交付树精度/吞吐/容量/归因 |
| 20261023（SUPERSEDED） | 同上 | 同上 | 同上（缺 `MAIN_SERVICE_VERIFY_20261024.md`） | 同上 |
| **main 移植（单列，OPEN）** | `nqz1997/vllm-ascend` `oscar-int2/m-port-full-ut` @ `81295d899`（main 基 `dde85f6b8`）；attn `704cf4e0c3a7fa5a`；同一冻结 kernel md5 | 上游 nightly `nightly-ci-main-a2-openeuler`（digest `8eaf0b4f…`），CANN 9.2.0 / torch 2.10.0+cpu / torch_npu 2.10.0.post7 / vLLM 0.31.0 @ `db9527a4`；NPU 7 | `MAIN_SERVICE_VERIFY_20261024.md`；补丁 `main_port_runtime_fixes.patch` sha256 `c227321d…` | **仅**构建/import/BF16 冒烟/隔离 UT 135 passed（适配后）＋串行化发射 41/41；默认异步 18/24 损坏，最小复现 B=1 1080 tok 5/12 vs blocking 0/12，定位 INT2 中层读路径、**OPEN**；不标生产可用，不引用交付树数字 |

---

## 9. 文件索引（本轮新增/使用）

| 文件 | 内容 |
|---|---|
| `PERF_ATTRIBUTION_ADDENDUM_20261024.md` | 本页 |
| `figs/PERF_PROFILING_20261024.csv` | 78 行 op 级分解（step/category/op 三层，含证据来源列；§10） |
| `figs/PERF_PROFILING_STEP_20261024.png` | INT2 vs BF16 纯 decode 步构成堆叠图（§10.2） |
| `profiling_20261024/r218rp_prof_leg.sh` | profiling 腿驱动（冻结腿同包络＋R118_SC/CAN 副本注入） |
| `profiling_20261024/r218_report_eval_prof.py`＋`CAN_DIFF.txt` | CAN 副本与冻结 CAN 的逐行 diff |
| `profiling_20261024/sitecustomize_r218prof/{sitecustomize.py,r218prof_hook.py,r218prof_cfg.json}` | 钩子（spawn/fork 双路径、幂等、cfg 门控） |
| `profiling_20261024/analyze_prof_trace.py`、`profiling_20261024/make_prof_outputs.py` | trace→CSV/图（只读 trace 与 steplog） |
| `profiling_20261024/smoke_out/` | torch_npu.profiler 冒烟（12:31，设备 7） |
| `runs/bg6_prof_{int2,bf16}_2k_c32/prof.trace.json` | chrome trace 原件（228,858,963 / 18,136,135 B） |
| `runs/bg6_prof_{int2,bf16}_2k_c32/prof_steps.jsonl` | 钩子生命周期＋逐步墙钟（含探针前后对照） |
| `figs/PERF_ATTRIBUTION_ADDENDUM_20261024.csv` | 44 行分解表：value/unit/per-step/share/basis/confidence/source |
| `figs/PERF_STEP_STATS_20261024.csv` | 逐点 span 分布、池化步时、批内首 token 跨度、引擎样本 |
| `r218_addendum_tables.py` | 生成器（只读已有腿；含对已发布账本的 6 条断言） |
| `runs/bg{1..5}_*/{perq.json,serve.log,gates.txt,hbm_samples.txt}` | 原始腿（未改） |
| `figs/bg_legs_raw.json`、`figs/INT2_vs_BF16_attribution.csv`、`figs/THROUGHPUT_COMPARISON.csv` | 主文口径（未改） |
| `/home/n00928095/R218_UPSTREAM_WORK/opbench_delivered.json` | 直调微基准（dev6，sync-per-call） |

生成链：`runs/*` → `r218_addendum_tables.py` → 两张 CSV；本页数值全部可由该脚本复算
（`python3 -I r218_addendum_tables.py`）。
