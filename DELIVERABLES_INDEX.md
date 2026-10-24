# R218 服务评测交付材料索引（**2026-10-23 吞吐归因修订版 —— 双模式全部收官**）

根目录：`acceptance/report_eval`（核心道/性能/容量/交付）与 `acceptance/lc_eval`（LB-E/RULER/LCB 长上下文与代码专项）。
**便携包（终版）：`report_eval/evidence_pack/r218_evidence_20261022_1024.tar.gz`（49MB/746 文件（含 lc_diag+diag512）＋sha256 清单；sha256=5f54aad10df20b4a5163131b8bdad6e48e44eccb0cb913244a10a909a043d5df）**——含审阅校准版表与 REVIEW_SUMMARY、核心道逐题 predictions/reviews/reports（v2 修复：早期包 `predictions*.jsonl` 匹配缺陷致 core 逐题数据静默缺失）、ext＋topup_score×2、LB-E/RULER/LCB 原始与官方分＋lbe_task_detail、defects。同目录另有 0959 中间版（sha c69b7268…，含 LC 机制定谳但**不含帽 512 区分腿**与 FACTS ③ 改写；RP 根下同名副本同 sha）与 `/tmp/r218_pack/0649` 旧中间版（表未含逐题列）；盘满期移出大件：`/tmp/r218_lb_data`、`/tmp/r218_lcb_data`、`/tmp/r218_math500_rescue`。

## 审阅与证据修正轮（2026-10-22 R218_EVIDENCE_TO_REPORT 新增）
- `report_eval/CORRECTIONS_0959_vs_0718.md` — **GPT 审阅用更正清单**（math500 逐题 18↔18、逐腿身份与 PR 链缺口、LC 诊断判定、容量图证据状态、保留稳定性问题、归档仓性质声明；gitcode oscar_39M 同名文件）
- `report_eval/PAIRED_SUMMARY.md`/`.json` — **统一逐题配对汇总**（自动生成 r218_pairs_all.py；方向统一 INT2−BF16；范围/口径/去重规则逐数据集标注；math_500 逐题 18↔18 修正"逐题同分"误述）
- `report_eval/EVIDENCE_MAP.md` — 逐腿版本/配置/证据映射＋全树对照（IDENTITY_TREE_DIFF.json：overlay 681=v3 430 逐字节+modelslim 差异+250 rc53 件）＋TT 窗实值订正（128/896）
- `report_eval/REVIEW_SUMMARY.md` — 一页审阅摘要（已验证收益/实际代价/未成立）
- `figs/PERF_POINT_EVIDENCE.{csv,md}` — 三联图逐点证据（NS/池/引擎并发上限/实际 token/TPOT/HBM/排队与 tested-not-max 标注；生成器 r218_perf_points.py）
- `lc_diag/DIAG_RESULTS.{json,md}` — 长上下文小规模诊断（hotpotqa/passage_count 帽 32↔128、cwe@8192 帽 120↔480，双模式；失败模式分类）

## 第四篇报告（吞吐归因，2026-10-23 新增）
- `report_eval/R218_ONE_PAGE_CONCLUSION.md` — **一页结论（报告入口）**：精度结果 / 内存收益 / 吞吐差距 / 已定位原因 / 未解与受阻
- `report_eval/R218_PERF_ATTRIBUTION_20261023.md` — 归因主文（四腿身份与协议、可复现性、容量-vs-HBM、prefill/decode 拆分、标度律、2K+16K 消融账本、三级结论、受阻测量）
- `figs/r218_samegmu_pair.{png,svg,pdf}` — 三联图（吞吐 / 墙钟拆分 / **容量-vs-HBM**，含 8.00× 与 4.27× 两对）
- `figs/INT2_vs_BF16_attribution.csv`（**32 行 v2**：baseline_wall/ablated_wall/delta_wall/delta-base/Δdecode/Δprefill/hits；`metric_ok` 区分诊断态；未覆盖量按阶段分列，不做 100% 配平）、`figs/THROUGHPUT_COMPARISON.csv`（**13 行最终吞吐对照**：逐腿身份/GMU/实际 token/墙钟/吞吐/比值；旧 10.0× 保留标 SUPERSEDED）、`figs/bg1_fourleg_protocol.csv`、`figs/bg_legs_raw.json`、`runs/bg1..bg5_*/`
- `report_eval/R218_DIFF_20261023.md` — **一页差异说明**（NOMIDE 口径、账本互斥性、10.0×→4.73×、MATH-500 措辞、PR/运行时状态）
- `report_eval/PERF_ATTRIBUTION_ADDENDUM_20261024.md` — **2026-10-24 补充（r5 版）**：2K/C32 步级二次分析、按类别时间分解（已证实/推测/未知）、版本映射；**§1.1/§1.2/§1.3 认识论更正**（span 拆分=统计代理量、7.4 µs/token 两点兼容≠标度律、"未覆盖"≠下界）；**§10 新增 sub-B profiling 腿**（bg6：torch_npu 算子级 trace，2K/C32 纯 decode 步：INT2 567.05 ms/步 = Oscar 中层核 209.25 + 其他 kernel 57.9 + host 间隙 300.7；BF16 89.74 = 12.6+16.3+60.8；NOMIDE 13 ms 之谜=host 遮蔽；服务内单次中层核 5.81 ms=直调 12.7×）——**⚠ 第 4 波（2026-10-24 深夜）更正**：上括号内"host 间隙 300.7/60.8""NOMIDE=host 遮蔽""12.7×"三条已撤回/降级（跨测量条件混合量与未证归因；12.7×→两场景观测比）；更正后三分类口径与 execute_model 计时核查见同文件 **§10.5**，取代关系见 `figs/PERF_PROFILING_20261024_SUPERSEDED_MAP.md`（r6 起 CSV/PNG 为三分类版，r5 版备份于 `figs/_backup_20261024r5/`）
  - 配套 `figs/PERF_ATTRIBUTION_ADDENDUM_20261024.csv`（44 行）、`figs/PERF_STEP_STATS_20261024.csv`（4 行）、生成器 `r218_addendum_tables.py`
  - **profiling 新增（r6 三分类版，第 4 波修正）**：`figs/PERF_PROFILING_20261024.csv`（93 行，measurement_condition 列：profiler_off_wall/profiler_on_sample/overhead/derived_deprecated）、`figs/PERF_PROFILING_STEP_20261024.png`（三面板分列图，非堆叠）、`figs/PERF_PROFILING_20261024_SUPERSEDED_MAP.md`（新旧对照）、`runs/bg6_prof_{int2,bf16}_2k_c32/`（trace 原件+逐步墙钟）、`profiling_20261024/`（腿驱动/钩子/分析/`ATTEMPTS.md`；r5 旧 78 行 CSV 与堆叠图备份于 `figs/_backup_20261024r5/`）
  - 公开证据分支：`nqz1997/vllm-ascend` @ `r218-evidence/20261024`（orphan，不含源码；**HEAD ae4888888，r5 为最新**）
- 证据包 `evidence_pack/r218_perf_attribution_20261024r5.tar.gz`（**157 文件/17 MB**，sha256 `32361729a1680bf797d47bbbc180fe63aba53fa721c696ed7b602e3585372ae0`）；r2/r3/r4 保留为 SUPERSEDED（r4 的 `PR_ADVANCE` 为 pymid 撤回前旧版）；构建器 `r218_perf_pack.sh`（r5=r4 staging 拷贝+增量，手动）

## 一页总表与协议
- `report_eval/REVIEW_SUMMARY.md` — **审阅摘要（推荐入口）**：已验证收益/实际代价/OPEN/钉死版本，供用户审阅与 GPT 报告取材
- `report_eval/ACCURACY_TABLE.md` — 精度总表（**终版**：核心六道 Δ 区间 −2.02..+0.69＋逐题退化/反超列、扩展、RULER 27 格、LB-E 735；口径声明=无预设阈值）
- `report_eval/FACTS_AND_LIMITATIONS.md` — 已证明事实 / 已知限制（含 C=1 楔死、结构性超时 top-up、盘满三事件）/ 未关闭
- `report_eval/IDENTITY.md` — 组合身份表（PR 链＋修复链 12ee434b/8c23a2ce＋内核＋overlay＋旋转＋配置）
- `report_eval/ES_PROTOCOL.md` / `EXTENSIONS_PROTOCOL.md`（含执行偏差披露节）/ `lc_eval/LBE_PROTOCOL.md` — 三份冻结协议（子集种子、并发、模板、评分器）
- `report_eval/REPORT.md` — 入口导读

## 图与性能/内存
- `report_eval/figs/r218_triple.{png,svg,pdf}` — 三联图（A 2K / B 16K 吞吐曲线 / C 长度→质量门最大 Batch）
- `report_eval/figs/perf_detail.json`、`triple_data.csv` — 全实测点（只画实测点；OOM/质量失败/超时标注）
- `report_eval/r218_perf_table.py` — 性能/内存表生成器

## 原始数据
- 核心道：`report_eval/es/full_{int2,bf16}_{A,B}/<ds>/`（逐题 predictions＋evalscope reports）；配对 `es/es_pairs_{coreA,coreB,cross}.json`（逐题退化/反超明细）
- 扩展：`es/ext_{bf16,int2}/{mmlu_pro,aime25}/`；top-up 评分 `es/ext_int2/aime25/topup_score.json`、`es/full_int2_A/math_500/topup_score.json`（同库零漂移＋verify 26/26）
- LongBench-E：`lc_eval/preds/{int2,bf16}/*.jsonl`（含 raw 边车）＋官方分 `lc_eval/score/BF16_sub/pred_e/BF16_sub/result.json`（INT2_sub 落地后并入）＋配对 `lc_eval/lbe_pairs.json`
- RULER：`lc_eval/ruler_official/{data_gen,preds,score}`（官方器，N=30/格 × 9 任务 × 3 长度 × 2 模式）
- LCB：`lc_eval/lcb_preds/{BF16,INT2}/{generations.jsonl,eval.json}`（官方沙箱 pass@1）
- 批量验证子集（队列排空后）：`es/batch_subset/`

## 复现入口
- 服务腿：`report_eval/r218es_leg.sh`、服务器 `r218es_server.py`；队列 `r218es_queue.sh`、扩展 `r218es_ext.sh`
- LB-E：`lc_eval/r218_lbe_pred.py`→`r218_lbe_fill.py`→`r218_lbe_score.sh`→`r218_lbe_pairs.py`
- RULER：`lc_eval/ruler_official/ruler_gen.sh`→`r218_ruler_call.py`→`ruler_score.sh`
- LCB：`lc_eval/r218_lcb_run.py`（gen/eval 两相）
- INT2 全夜链：`lc_eval/int2_chain.sh`→`int2_chain3.sh`（fill→RULER→ext）→`int2_chain4.sh`（LCB INT2）

## 日志与缺陷
- `report_eval/LOG_INDEX.md` — 全日志索引（含 2026-10-22 收官日节：math_500 终局、服务器终态、⚠不可引用件）
- `lc_eval/defects/LC_INT2_16K_C8_GRIND.md` — INT2 C=8 楔死取证（根因 UNKNOWN，绕行=分桶并发）
- `lc_eval/defects/AIME25_INT2_C1_WEDGE_20261021.md` — INT2 C=1 长时楔死取证（重启恢复、非题特异；与 C=8 形态独立）

## 已知回归项（保留，不静默）
batch-64 row33 确定性退化；B_g184 算术、C_2wikimqa_44 重复循环；NS=1 跨 generation 残留；电池间歇（aclnn 发射层竞态）；LC 三形态（r116×2 已修、C=8 楔死 UNKNOWN）

## PR 提交轮（2026-10-22 /goal 终态）
- `delivery/PR_SUBMISSION_LEDGER.md` — **PR 台账**（21 Draft 已建＋核验：链接/head/base/依赖；PR-22 客户保留；上游两项 WAITING；自有仓推送记账）；gitcode oscar_39M@217ad9b 同步 `PR_SUBMISSION_STATUS.md`
- `delivery/CODE_VS_TESTED_MAPPING.md` — **提交代码↔已测代码对应表**（三缺件折入：r116/OGA/modelslim 接线；OGA=树级审计补实、0959 未列；一行 NameError 修复=唯一内容差；回归=13 尖 UT 绿+IDENTITY_TREE_DIFF_V4+dev6 冒烟参考 sha 3/3 逐字节）
- `delivery/RESERVED_FOR_CUSTOMER_PR22.md` / `delivery/USER_ACTIONS.md` — 客户保留说明／用户最短操作清单（GitHub 上游 PR、CANN 目标仓确认、可见性可选）
- `delivery/pr_texts/BRANCHES.md`（v4 化）＋`v4_addendum_pr{10,16,21}.md`＋`v4_evidence_block.md`；`delivery/pr-branches-v4.bundle`（23 refs）＋`pr_patches/framework_v4/`（25 件）
- v4 链：`oscar-int2/v4-pr-10..22`（tip 983fbac1，pr-01..09 沿用）；远端 `gcw_S4YvZ8l6/vllm-ascend`（私有，25 refs）＋`oscar-int2-ops`（私有）；冒烟原始件 `runs/needle_v4smoke{,2,3}.json`
