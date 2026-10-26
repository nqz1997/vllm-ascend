# R218 文章材料冻结入口（ARTICLE_MATERIALS_ENTRY，2026-10-25）

> **用途**：GPT 写作系列四（及后续引用 R218 材料的任何文章）的**唯一入口**。本页只做
> 版本锚定、数字冻结与引用边界声明，不产生新结论；一切数字引自下列已冻结文档，未改动。
> **阅读顺序**：`R218_ONE_PAGE_CONCLUSION.md`（含 2026-10-24 晚更正注记）→ 归因主文
> `R218_PERF_ATTRIBUTION_20261023.md` → `PERF_ATTRIBUTION_ADDENDUM_20261024.md`
> §1.1–1.3/§10（含 §10.5 终版更正）。冲突时以**更晚的更正**为准。
>
> **总纪律（引文红线）**：① 无预先认可的质量阈值，差值不构成通过/失败判定，"INT2 测得
> 较高"不得写成"更准"；② 不写硬件下限/内核地板（"无原生 INT2 不可能更快"类表述禁用）；
> ③ 已撤回结论（见 §5 撤回边界）不得复活；④ 精度/性能数字只属于冻结交付组合（§1）；
> main 移植版（默认异步缺陷已定谳并修复，见 §7.1/§9/§11 终版发布材料汇总）数字**单列**，
> **不得引用**冻结组合数字；⑤ 容量两种口径（同 GMU / 相近总
> HBM）分列，不得混引；⑥ "5.1×" 是 TPOT 混合口径，勿引。

## 1. 版本映射（当前有效版与 SUPERSEDED 历史）

### 1.1 组合身份（一切精度/性能/容量数字的版本边界）

| 项 | 冻结交付组合（精度+性能+容量数字的唯一属主） |
|---|---|
| 框架 | v4 PR-22 tip `983fbac1`（树 ≡ 已测 `ov_restore` overlay；`attention_v1.py` sha `85051bbd2e74c117`） |
| 内核 | 冻结 `oscar_r144_v133c_grp`，候选 `.o` md5 `c8a8d47a63be7ad79abce43de005f238` |
| launcher | `int2_lse_fast_r152`；姿态 eager、前缀缓存关、block 128、MNBT 8192 |
| 运行时 | `oscar-r103-runner`，CANN 9.0.0 / vLLM 0.22.1，Qwen3-8B，单卡，greedy |
| 精度组合 | PR 链 v3-pr-22 tip `a6ef9b97` overlay（含修复 12ee434b/8c23a2ce）＋同一冻结内核（双模式身份门一致） |

main 移植（单列，不作产品结论）：细拆链 `oscar-int2/m-pr-01..m-pr-18`（上游 16 个开放
PR；head 以 `/tmp/r218_wave6_state.md` 为准），上游 nightly 镜像 CANN 9.2.0 /
torch 2.10.0 / vLLM 0.31.0。**默认异步缺陷已定谳并修复**（§7.1）：修复 launcher＝
`int2_op_launch_lse_fast_r152.cpp` sha256 `41bce535…`（＝#19570 终 tip `96ef95c9a`
内容），冻结 `.o` 内核不变；隔离 UT（wave-6: 127 passed；wave-7 集成树: 141 passed）
＋默认异步修复版电池（§9 A 线终局）。

### 1.2 证据包版本

| 包 | 内容要点 | 状态 |
|---|---|---|
| 性能归因 `r218_perf_attribution_20261024r6.tar.gz`（sha256 `fb52b69d…e31f75`，163 项） | r5 全部＋第 4 波呈现更正：§10.5 撤回跨条件混合量、三分类 CSV 93 行（measurement_condition 列）、三面板图、新旧对照 SUPERSEDED_MAP＋r5 备份 | **当前有效** |
| `…20261024r5` | sub-B profiling 腿（chrome trace 原件、逐步墙钟）、addendum §10、§1.1–1.3 认识论更正 | SUPERSEDED（host 间隙/各半/遮蔽表述由 r6 §10.5 取代） |
| `…20261024r4/r3/r2/20261024` | 容量修复目录、main 异步定位、补充页、四腿＋消融＋归因账本 v2 | SUPERSEDED（保留） |
| `…20261023` | 前驱（无 main 服务验证记录） | SUPERSEDED（保留） |
| P6 异步 `r218_p6_async_evidence_20261025r2.tar.gz`（v4，sha256 `d986fdef…d35135`，74 文件） | 载体 missing-write 哨兵实锤＋onset 首事件证据；第 3 波"跨代环残留"归因推翻；p6_compare.py 已修复（fe2fce54…） | **当前有效** |
| P6 `…20261024.tar.gz` | 第 3 波（哈希流＋环张量；归因已被第 4 波更正） | SUPERSEDED（保留） |

文档当前版：一页结论（2026-10-23 正文＋10-24 晚 append 更正注记 4 条）；归因主文
（2026-10-23）；ADDENDUM（含 §10/§10.5 终版更正）；MAIN_SERVICE_VERIFY（§6.2 已应用
第 4 波替换文本）；PR_ADVANCE（含 §10 第 4 波终报）。~~已知滞后~~ **已消除（2026-10-25
第 5 波）**：P6 v4 包（修复版 `fe2fce54…`）已重打包发布并随本入口同步证据分支；分支顶层
README 标题已更正为 r6。

## 2. 精度（冻结组合；引自 `ACCURACY_TABLE.md` 终版 2026-10-22，不改数）

核心六道（EvalScope 全量，同题/同模板/同评分器，Δ=INT2−BF16）：

| 数据集 | n | INT2 % | BF16 % | Δ |
|---|---|---|---|---|
| GSM8K | 1319 | 93.18 | 92.49 | **+0.69** |
| C-Eval val | 1346 | 78.45（macro 78.88） | 79.05（macro 79.64） | −0.60 |
| MATH-500 | 500 | 80.80（404/500） | 80.80（404/500） | **0.00**（逐题 18 退化 / 18 改善） |
| GPQA-Diamond | 198 | 45.45 | 47.47 | **−2.02**（最大单项差） |
| HumanEval | 164 | 84.76 | 86.59 | −1.83 |
| IFEval (prompt-strict) | 541 | 81.52 | 82.07 | −0.55 |

简单平均 **−0.72 pp**；单项区间 −2.02..+0.69。扩展：MMLU-Pro(700) 63.86 v 63.71（+0.15）、
AIME25 20.0 v 20.0（6/30 同）、LCB pass@1(454) 24.67 v 24.23（+0.44）。

长上下文：**LongBench-E 735 题官方分 36.83 v 39.26（−2.43）**——退化带 hotpotqa 8k+
（−7.17，桶 45.94 v 72.83）、passage_count 0.00 v 10.00、triviaqa 8k+（−3.33，桶 −10）；INT2 测得
较高的桶：hotpotqa 0-4k/4-8k、qasper 0-4k、samsum 全桶、multifieldqa 4-8k、lcc 4-8k。NV RULER 27 格（4096/8192/16384×9
任务，官方器）：niah 族 INT2 93.33–97.50 v BF16 99.17–100（每 30 题丢 1–2 针）；
**cwe@8192 0.33 v 14.00**（已定谳＝帽×CoT 交互：480 帽下两模式 13/13 恢复）；fwe 4K/8K
INT2 较高；qa_1 三长度 INT2 较高；vt 双模式协议性 0。退化机制三层定谳（受控帽对照）：
cwe=帽×CoT；hotpotqa 8k+=信息性答错＋跨跑漂移（截断排除）；passage_count=输出风格×
官方计分＋真计数错误 3/6（512 帽仍 0/6）。**口径**：INT2 侧 LB-E 用分桶并发
（<4k C=4/4-8k C=3/8k+ C=2）绕行 C=8 楔死，与 BF16 C=8 不对称已披露；greedy 下并发
不应改输出。批探针 bs=8 100/100 与单并发逐字节同（0.98==0.98）。

## 3. 容量（同 GMU 与相近总 HBM 分列；引自一页结论 §2 / MSV §7）

| 口径 | 量 | 值 |
|---|---|---|
| **同 GMU 0.75**（同为 29.52 GiB KV 分配） | 池 token | **1,719,424 v 214,912 = 8.00×**（实测 8.00–8.03×） |
| 同上 | HBM 峰 | **93% v 77%**——INT2 生成期每步多占 **~10.5 GiB** 工作区 ⇒ **8.00× 池 ≠ 8× 显存收益** |
| **相近总 HBM 公平对**（80.6% v 79.1%，±1.9%） | 池 token | **4.27×**（956,032 v 223,744） |
| 16K 实测驻留（质量门最大验证活跃 batch） | INT2 32（**tested-not-max**；池 1,009,280 tok，HBM 峰 79%）v BF16 16 | **BF16@32 物理不可行**（池 281,472 tok=16.92×＜32×16,640=532,480，gates.txt 直证）——16K BF16 32 驻留不可行，引擎 16.92× 直证 |
| 引擎打印 | "并发 746×/103×" | `池÷(ctx+256)` 推算，**不是实测并发**（实测活跃 batch 仅 32@2K、8@16K） |
| **main capfix（未合入，非产品结论）** | 池 token（2K 引擎口径） | 修复前 306,432 → **849,280**（=修复前 **2.77×**；对 BF16 153,216 = **5.54×**）；16.40 GiB 预算=21.04−4.64 HP 环；849,280×576 B×36 层 与预算一致。**仅诊断姿态（BLOCKING=1）41/41 无损坏；默认异步同最小复现修复前 11–12/12 坏→提交边界修复后 0/12（§7.1，治本非治标：错误位置 flush 亦 0/12 但不构成顺序保证）；capfix 叠加腿（p9）849,280 tok＝BF16 153,216 的 5.54× **复现**（未合入、不进产品结论、未测吞吐）；分支 `oscar-int2/capfix-int2-spec` 实测@`d1db5264a8f1`，后叠 fail-safe 提交至 `db6398286`（UT 146 passed）** |

## 4. 吞吐（同工作负载、同 GMU 0.75；引自一页结论 §3）

| 点 | INT2 | BF16 | 差距 |
|---|---|---|---|
| 2K / C=32 | 41.5 tok/s（49.31 s 中位；3 腿 49.10/49.31/104.39） | 196.6 tok/s（10.4 s 中位；2 腿） | **4.73×** |
| 16K / C=8 | 4.51 tok/s（113.5 s 中位） | 26.4 tok/s（19.4 s 中位） | **5.85×** |

- 旧 2K 点估计 **10.0×** 来自首腿单跑（104.39 s，prefill 离群；decode span 正常），已
  SUPERSEDED 但在 `THROUGHPUT_COMPARISON.csv` 保留；逐次配对区间 4.70–10.05×；点估计＝
  3 腿中位 49.31 s。
- **并列口径（互不混用）**：单流稳态 decode TPOT **2.2–2.7×**（@1024–8192，p50
  65.8/24.7→67.4/30.7 ms，平于 ctx）；C=8 吞吐比随 ctx **8.9/12.7/17.0×**（2K/8K/16K）；
  e2e **2.4–3.7×**（prefill 4–5× 为主）。2K 的 4.73×（thrcap 端到端）与 8.9×（稳态解码）
  是不同协议，不可互换引用。**"5.1×"＝TPOT 混合口径，勿引。**
- **INT2 未在任何并发域追平 BF16**（2K C=1..128：4.83→45.12 v 12.59→273.43 tok/s）；
  prefill 每 token 0.17 v 0.044 ms、decode 每 token 603 v 119 ms（C=32）——共享 per-token
  链路同步变差。**不写硬件下限**：分组内核 10–12 ms/层·调用是"两 vendor 实现共同的观测
  地板"，非硬件下限论断。

## 5. 最终图与 CSV 清单（全部在 r6 包 `figs/`；引用条件与撤回边界）

| 文件 | 内容 | 引用条件 |
|---|---|---|
| `PERF_PROFILING_STEP_20261024.png`（仅 png） | **三面板分列图**（OFF 墙钟 / ON kernel 并集＋窗口空闲 / 探针开销），无堆叠构成 | 三条件分列呈现；①②不可互减/相加构成"步构成"；②空闲是 ON 条件观测（含探针、含未计时段 ~3.8 ms/步） |
| `PERF_PROFILING_20261024.csv` | **93 行三分类**（measurement_condition 列；r5 量仅存 deprecated 行） | 同上；deprecated 行（host gap 300.66/60.79）不得再作数据引用 |
| `PERF_PROFILING_20261024_SUPERSEDED_MAP.md` | r5→r6 逐项取代关系 | 撤回边界权威说明 |
| `figs/_backup_20261024r5/` | r5 堆叠图＋78 行 CSV＋step_decomp.r5.json | 仅历史追溯 |
| `r218_samegmu_pair.{png,svg,pdf}` | 吞吐/墙钟拆分/容量-vs-HBM 三联（冻结组合） | 容量面板按 §3 两口径读 |
| `THROUGHPUT_COMPARISON.csv` | 逐腿身份/token/墙钟/吞吐/比值（旧 10.0× 标 SUPERSEDED） | §4 |
| `INT2_vs_BF16_attribution.csv`（32 行）、`PERF_POINT_EVIDENCE.csv`、`bg1_fourleg_protocol.csv`、`triple_data.csv`、`bg_legs_raw.json`、`opbench_delivered.json`、`throughput_nogain_ledger.json` | 归因账本/逐点证据/腿协议/图数据/原始/直调微基准/nogain 台账 | 门控差分**非加性**（见 §6） |

**撤回边界（写作红线，2026-10-24 深夜第 4 波终版，ADDENDUM §10.5）**：
1. "host/发射间隙 300.7/60.8 ms＝墙钟−kernel 并集"——**跨条件混合量，已撤回为 deprecated**；
   OFF 条件"kernel 之外残差"不可得。
2. "步差≈Δkernel 237.4＋Δhost 239.9 各半"——**撤回**（两条件差强行相加，非测量）。
3. "NOMIDE 只省 13 ms/步的原因＝host 间隙遮蔽"——**降级为未证**（观测保留：NOMIDE 2K 差分
   24.25 ms/步 vs 中层核 ON 条件 209.25 ms/步，关系待解释）。
4. "host 编排与 ctx 无关"的证伪——**撤回推理**，回到 OPEN。
5. **"12.7×"＝服务采样（ON trace，per-call 5.81 ms）vs 直调（sync-per-call，0.456 ms）
   两场景的观测比**，两场景布局/tiling/采样条件不同，成因未查；不得写成"服务放大 12.7×"。
6. "∝C×ctx 标度律 / 7.4 µs/KV token 签名 / 2.5 GB/s / ≥90% 无覆盖下界"——均**认识论降级**
   （两点兼容非标度律；非加性消融之和不构成下界，措辞用"未被任何已测门控覆盖的差分观察"）。
7. execute_model host 计时**不保证覆盖设备完成**（fork 两段式返回路径无无条件同步；"＝设备
   完成口径步时"读法不成立）。

## 6. 性能已证实 / 未知（2K/C32 decode 步；ADDENDUM §10.5）

**已证实（同条件直接测量）**

| 条件 | 量 | INT2 | BF16 |
|---|---|---|---|
| ① profiler OFF（n=43/43） | execute_model host 墙钟中位 [p25–p75] | **567.05** [563.17–571.55] ms/步 | **89.74** [88.86–91.12] ms/步 |
| ① 同条件差 | Δwall(OFF) | **+477.31 ms/步** | — |
| ② profiler ON（12 步窗口） | NPU kernel 并集/步（78,364/7,383 事件） | **266.39** | **28.95** |
| ② 同条件差 | Δkernel(ON) | **+237.44 ms/步** | — |
| ② | 12 步窗口跨度/步 | 768.50 | 114.75 |
| ② | 窗口内设备空闲/步（含探针开销） | **502.12（65.3% 空闲）** | **85.81（74.8% 空闲）** |
| ③ 观测开销 | median(ON)−median(OFF) 同腿 | **+197.67（+34.9%）** | **+21.24（+23.7%）** |
| ② | 中层核 per-call（432 次 min/med/max） | **5.81 ms**（5.78/5.81/5.85），服务内合计 209.25 ms/步 | —（无中层） |

门控差分（§4.1 原测值，**非加性、同步内可重叠**）：NOMIDE 2K 24.25 ms/步、16K 52.96 s
（46.7%，841 ms/步，**诊断腿输出错误只作诊断限制**）；slide2 3.7%（2K）/0.4%（16K）；
SR stage 0.21 s；G stage 换路 −0.42 s（更慢）。

**未知（如实留白，不硬归因）**：OFF 条件设备占用（无设备时间数据）；ON 窗口空闲内部的
launch/API/等待切分（cpu_op 嵌套不可加）；12.7× 观测比成因（两场景 tiling/块表分散度/
并发流未记录）；16K 未采 trace；bg1 2K 单次 prefill 离群（104.39 s）根因；未覆盖差分的
进一步切分（需 msprof 或真删 carrier 组装的对照）。

## 7. 已知限制（既有条目，如实披露）

1. **main 默认异步缺陷——已定谳并修复（2026-10-25 第 5 波，CLOSED）**：根因＝launcher
   直调 ACLNN 越过 torch_npu 任务队列提交边界（`stream(false)` 取裸句柄；TASK_QUEUE_ENABLE
   缺省 1 时 ATen/op_api 主机调用经 Repository consumer 线程异步提交，直调可在未提交的
   lse 哨兵 fill 与调用方 staging 之前先发射）。修复＝7 个直调入口在"最后一次 ATen 操作
   之后、直调提交之前"取 `stream(true)`（官方主机侧提交边界，非设备同步）＋r/ex/lr 硬
   检查；**默认异步保持**（无全局 blocking/设备同步），边界开销 0.32–16 µs/call。三分
   定谳：pristine 11/12 坏、边界修复 0/12、错误位置 flush 亦 0/12（治标非保证）。上游化
   ＝#19570 终 tip `96ef95c9a`（全 CI 绿）。验证范围：B=1 1080 tok 最小复现＋服务电池
   （§9 A 线终局）；**不产生新的精度/吞吐数字**。
2. **capfix 5.54× 未合入**：独立分支诊断姿态验证，非产品结论（见 §3）。
3. **16K BF16 32 驻留物理不可行**（池 16.92×；INT2 32 为 tested-not-max）。
4. 服务缺陷三 UNKNOWN：INT2 C=8 长上下文楔死（LB-E/RULER 被迫分桶绕行）；C=1 长时累积楔死
   （重启恢复、非题特异）；batch-64 row33 确定性退化（63/64，3/3 复现）。另 8110 终死单发
   未取证。
5. 评测限制：RULER stage-1 N=30/格（±9% CI）；LB-E=分层 20% 子集；MMLU-Pro=700 子集；
   C=1 top-up 结构性超时适配已披露；TTFT 批值为冷锚上界。
6. "框架、算子均由 PR 源码构建"组合＝OPEN（冻结 .o 位级复现既往已证不可达）。
7. P6 表述边界（2026-10-25 更新）：哨兵留存的机制已由 §7.1 定谳＝**发射顺序违反**（直调
   越过任务队列提交边界、哨兵 fill 尚未提交到流），**不是**"内核从未写入"的证明；输入/
   输出哈希一致只是观测，不称"写侧无罪"。P6 v4 包证据按此口径引用。

## 8. 源码与证据直链（GitHub 证据分支 raw；分支 `r218-evidence/20261024`）

Base：`https://raw.githubusercontent.com/nqz1997/vllm-ascend/r218-evidence/20261024/`（tip 2026-10-25 起推进至 `3cc27abee` 以上；本页文件名即直链路径）

- **性能 r6 包**：`r218_perf_attribution_20261024r6.tar.gz` ＋ `.sha256`（sha256
  `fb52b69d8b57e078dc2ac4addcfdf0beec6b5cfefef6518a4710c2a969e31f75`）
- **P6 v4 包（当前有效）**：`r218_p6_async_evidence_20261025r2.tar.gz` ＋ `.sha256`（sha256
  `d986fdef9825d9ebeda64d12a786c2ee1f1b615acafa218945622278d9d35135`，74 内容文件；包内
  `p6_compare.py` 已是修复版 `fe2fce54…`，含 `ref_reproduction_20261025.txt` 复现记录）
- 文档（分支顶层）：`PR_ADVANCE_20261024.md`（含 §3.5/§3.6/§9/§10 第 4 波终报）、
  `MAIN_SERVICE_VERIFY_20261024.md`（§6.2 替换文本已应用）、
  `PERF_ATTRIBUTION_ADDENDUM_20261024.md`（含 §10.5）、`R218_ONE_PAGE_CONCLUSION.md`
  （含 4 条更正注记）、`R218_PERF_ATTRIBUTION_20261023.md`、`R218_DIFF_20261023.md`、
  `DELIVERABLES_INDEX.md`、`UPSTREAM_PR_STATUS_20261023.md`、`README.md`
- 历史包（SUPERSEDED 保留）：`r218_perf_attribution_20261023/20261024/r2/r3/r4/r5.tar.gz`
  ＋各自 `.sha256`；`r218_p6_async_evidence_20261024.tar.gz` ＋ `.sha256`、`r218_p6_async_evidence_20261025.tar.gz`
  （v3，sha256 `92ac574b…`，包内 p6_compare.py 为缺陷版——已由 v4 取代）
- 本地镜像：`/home/n00928095/OSCAR_PARALLEL_WORK/R218_OSD/acceptance/report_eval/`
  （文档＋`evidence_pack/`＋`p6_async_evidence/`）；上游 PR 源码 `nqz1997/vllm-ascend`
  分支 `dco-signed/pr01..pr04`（#19577）与 `oscar-int2/*`（#19568–#19570 等）。

## 9. main 线增量（2026-10-25 第 5 波；只作增量行，不覆盖冻结组合评测结果）

- **A 线（终局，NPU 7，2026-10-25）**：假设三分定谳——H_B（torch_npu 任务队列提交边界
  缺失）成立，H_A（CANN 发射层竞态）/H_C（跨代环残留）证伪；pristine launcher 11/12
  坏→边界修复 0/12，旧位置 flush 亦 0/12（治标）。修复上游化 #19570 终 tip `96ef95c9a`
  （全 CI 绿）；修复版默认异步电池 60/60＋20/20、UT 139；capfix 叠加复现见 §3。
- **B 线（本波，纯 CPU）**：① P6 `p6_compare.py` 两缺陷修复（GQA reshape 崩溃＋错 unpack
  布局；c72b874c…→fe2fce54…＝主 Agent 实跑版），4 捕获 CPU 复现全 0 退出码、哨兵结论逐字
  复现（async#2 cos=0.000000/kern_lse=−9999×3；blocking#2 0.999994；捕获#1 两腿 0.999927），
  8 组合判别扫描证明修复方向唯一——`p6_async_evidence/ref_reproduction_20261025.txt`；
  ② 包清单拆分 `PACKED_MANIFEST`/`RAW_MANIFEST`（229 项快照）/README 最新有效版本块；
  ③ 本入口文件。**主 Agent 已重打包发布 v4**（`r218_p6_async_evidence_20261025r2.tar.gz`，
  sha256 `d986fdef…`，74 文件，包内校验 73/73 OK）——引用一律用 v4；v3 列入 SUPERSEDED。
- capfix 分支推进：fail-safe 上推 `db6398286`（UT 146 passed），仍**未合入**。
- 上游 PR（2026-10-25 主 Agent）：**6 个已投**——#19577/#19568/#19569/#19570 全部
  **ready for review**（评审线程已逐条回复＋resolve：#19568×2、#19569×2、#19570×20；
  #19570 修复提交 `314f9186e`＋异步边界修复 `96ef95c9a`，全 CI 绿）＋
  **#19728（05 helpers，依赖声明叠堆，全 CI 绿含 cpu-ut×2）**＋**#19729（06 ctx hub，
  main 适配版）**。完整提交台账（每单元依赖/阻塞依据/解除条件/已备分支）见证据分支
  `PR_ADVANCE_20261024.md` §12。

---
## 10. main 线增量（2026-10-25 第 6 波——上游评审整改＋单元 08-18 提交；只作增量行）

- **细拆链推进至 18/22 逻辑单元、开放 PR 16 个**（不得再写 "4/22"）：第 6 波新投
  #19732(08)/#19734(07+09)/#19735(10+12)/#19739(11)/#19741(13)/#19742(14)/#19743(15)/
  #19746(16)/**#19747(17 decode)**/**#19750(18 prefill)**。head 以
  `/tmp/r218_wave6_state.md`（活交接）为准，报告时重验；PR↔单元↔增量 diff↔CI↔线程
  总表随终局交付给出。
- **评审修复（全部 CPU 可复验、逐条先锚定）**：① 作者侧四修（paths `_REPO_ROOT` 层数＋
  `/tmp/oscar_runner-<uid>` 多用户隔离；`_r218_diag` OSCAR_DIAG 门控＋重定向；`_R166SlotAlloc`
  重复 rid fail-closed；zeroed 槽位换手剪枝＋events 有界）；② gemini 二轮实锤五修
  （decode TND packed-varlen——B≥2 曾全体读最后一条 KV，入口未接线属 latent；≤3.11
  f-string 换行 SyntaxError ×3；R113 staging 缩容 realloc；prefill `_tt_plen`→`_tt_pref`；
  R166 冗余分支折叠）＋一驳（`.view` 非连续——接收者皆新造连续张量）；③ CI 真败修复
  （typos `dum`/codespell `dout`/全包 mypy `_fb` str-句柄同名）。TND 回归测试已负控
  （旧打包下红）。
- **验证范围声明**：容器 `tests/ut/oscar` **127 passed**（含新 TND/prefill 契约）＋scoped
  mypy 3.10/3.12 零新错＋ruff 全绿＋**真 python3.11 ast 全树解析扫描**（f-string 文法
  门；`feature_version` 不查该类）。**边界：以上全部属 main 线结构/健壮性修复；冻结
  组合（§1.1）的精度/性能/容量数字不受影响、不重新解释**（冻结组合=v4 链 overlay，
  本波修复不在其内；decode TND 修复对象为未接线入口，无已发布数字可影响）。
- **集成树↔已测代码**：main 细拆链 tip `oscar-int2/m-pr-18`（head 见状态文件）↔ 容器
  `/tmp/mpr18_wt` 全树 tar 同步（UT 127 绿）；每分支推送前 blob 逐字节校验，且载体经
  trees API 证实（m-pr-11/13/14 不携带 quantcache 即由该检查发现）。
- **维护者等待（单列，非自主可解）**：全部 PR 的 `ci-gate`＝维护者标签门（ready-precise/
  ready-all）；#19728 cpu-ut＝基础设施失败（CANN 镜像 SWR 拉取 TLS 超时、pod 未上线、
  零测试运行），重跑已请求；19552 CLOSED（由 #19577 取代）。
- 单元 19-22 结构性阻塞（19 组装 import 全部 12 mixin；20-22 为 release 线适配、main 缺
  路径），本轮不投。

---
冻结：子 Agent B（第 5 波）2026-10-25；第 6 波增量按 §10 追加；本页不改任何既有数值。

## 11. 终版发布材料汇总（2026-10-26 05:5xZ；技术文章由 GPT 撰写，本节为其事实底稿）

### 11.1 术语与版本对应表（勿混用）
| 组合 | 版本锚 | 用途 |
|---|---|---|
| 冻结组合（v4 链 overlay） | §1.1 身份＋evidence pack r218_evidence_20261022_* | 全量精度/性能/容量数字唯一来源（§2-§6） |
| **同步上游 main 后的集成 tip** | fork `oscar-int2/m-pr-22`@**bfad514b0**（tree `6a8b6c444c63…`，attention_v1 sha256[:16]=`9eb603e3b10ea866`） | 小规模功能回归＋20 PR 提交载体；**上游尚未合入，非"已合并 main"** |
| 合并前集成 tip（历史锚） | `a7da582bd`（attention_v1 `81f6adc0`） | 13 文件生命周期电池证据锚（内容为 bfad514b0 的字节子集，我方文件） |

### 11.2 20 PR 链接表（全部开放；Ready=可评审，**非生产验收通过**）
#19577@c1d1772b5 · #19568@bc7bd8578 · #19569@04303a2e0 · #19570@96ef95c9a（01-04 ready，全 CI 绿）｜#19728（cpu-ut=基建重跑待办）· #19729 · #19732 · #19734 · #19735 · #19739 · #19741 · #19742 · #19743 · #19746 · #19747 · #19750（05-18，ci-gate=维护者标签门）｜**19-22（同步 main 后）**：#19764@25bfa36fb · #19765@bb488d49e · #19766@a5c2c53b0 · #19767@bfad514b0（四头 pre-commit/DCO/main 绿；cpu-ut 64/65/66 双腿绿、67 在跑；DCO 合并豁免成立）。01-18 各头以 /tmp/r218_wave6_state.md 与 PR 页为准（报告时重验）。

### 11.3 质量判读（三分离；详见 WAVE7_SERVICE_ADDENDUM_20261026.md）
- **答案正确性**：服务级答案证据唯一来源=冻结组合评测组（核心六道 INT2≈BF16）；集成 tip 电池为合成探针无语义答案，HTTP 200/choices 存在≠精度通过；logprobs 近并列（探针待跑）只解释首 token 分岔成因，**不作为答案正确性证明**。
- **异常重复/截断**：循环续写=贪心+短帽下基线行为（BF16 201/201 同循环）；截断边界 ±1 token=长度伪差；INT2 特有=25% 请求（5/20 提示，逐提示稳定）选择 3 个替代循环 token（不在 BF16 分布内）——**已特征化的行为差异，保留 OPEN**（边际量化待 lp_probe）；非 ASCII=循环 token 字节内容，本身不判错。
- **输出一致性**：INT2↔BF16 45/60 逐 token 全同、15/60 首 token 岔、0 措辞渐变；响应内自一致 INT2 36/60 vs BF16 60/60；跨 rep INT2 多态。
- 证据分层：**新 tip 8 文件电池**与**旧 tip 13 文件生命周期电池**（已跑，39/39 结构有效＋调度器级槽复用）分别列示，不合并覆盖范围。
  **截至本节发布时点（2026-10-26 06:1xZ）：lp_probe 与 ranchor 均未执行＝BLOCKED_DEVICE**
  （dev6/7 被非本项目容器负载持续占用 ~52GB；对等 pid 保护未触碰）。待执行命令与续接方式见
  /tmp/r218_wave6_state.md round L（lp_probe=2e watcher 触发 /tmp/lp_probe.sh；ranchor=/tmp/ranchor_leg.sh，
  ID 门 9eb603e3；可判分最小集=/tmp/gradeable/，6 题严格判分）。**"已准备"不等于"已验证"。**
  #19767@bfad514b0 cpu-ut(v0.31.0 腿)=自建 runner 容器实现失败（注记仅含基础设施错误、零测试失败注记、
  日志不可取；作者侧重跑 403=admin 权限）＝与 #19728 同类基建失败，单列外部等待，不归为代码失败。

### 11.4 吞吐/内存/瓶颈与未解项（全部引自冻结组合，不改数）
- 吞吐/内存：§3/§4（同 GMU 容量 8.00×、decode 2.2-2.7× slow、e2e 2.4-3.7×）；图与 CSV=r6 包 figs/（§5）。
- 瓶颈证据：middle kernel 209ms/步地板＋host gap 构成（§6/ADDENDUM §10.5）；未解项=host gap 构成、12.7× 成因、16K 未采样、INT2 首 token 分岔边际（新增）。
- OPEN 清单：跨代状态残留（NS=1 长 ctx）、INT2 批量分组内核地板、集成 tip 电池双锚注记待 ranchor 后由 PR 侧发布。

### 11.5 证据包
- 冻结组合包：/tmp/r218_pack/r218_evidence_20261022_0649.tar.gz 与 evidence_pack/r218_evidence_20261022_1024（终版；SHA256 于包内 MANIFEST）
- wave-7 归档：/home/n00928095/R218_UPSTREAM_WORK/delivery/r218_wave7_final/（22+2 文件：电池原始输出、身份、PAIRED/ANSWER_CHECK 分析、全树 diff 映射）
- 证据分支：github.com/nqz1997/vllm-ascend tree `r218-evidence/20261026`（ARTICLE+ADDENDUM+PR_ADVANCE；本节发布后以读回 SHA 为准）
