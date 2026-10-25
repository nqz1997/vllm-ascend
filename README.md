# R218 OSCAR True-INT2 — 性能归因证据包 `20261024r5`

本目录是 `r218_perf_attribution_20261024r5.tar.gz` 解包后的内容。
包摘要见包旁 `r218_perf_attribution_20261024r5.tar.gz.sha256`；
包内逐文件摘要见 `SHA256SUMS`（不包含自身）。

## 1. 版本

| 版本 | 内容 | 状态 |
|---|---|---|
| `20261024r5`（本包） | r4 全部 ＋ **sub-B profiling 腿**（`runs/bg6_prof_{int2,bf16}_2k_c32/`：chrome trace 原件、逐步墙钟、gates）＋ `profiling_20261024/`（腿驱动/钩子/分析脚本/尝试记录）＋ `figs/PERF_PROFILING_20261024.csv` 与对比图 ＋ addendum §10（2K/C32 decode 步算子级构成）＋ §1.1/§1.2/§1.3 认识论更正 ＋ 两旧文更正注记 ＋ `PR_ADVANCE_20261024.md` 更正版（含 §3.5 撤回「Python 中层排除 C++ 算子」） | **最新** |
| `20261024r4` | 20261024r3 全部 ＋ `capacity/`（INT2 容量修复分支、补丁、服务尺寸日志、24/24+17/17 电池、异步负对照）＋ `PR_ADVANCE_20261024.md`（旧版：pymid 撤回前）＋ main 异步定位更正（`MAIN_SERVICE_VERIFY` §6、addendum 版本边界、差异页 OP/OPEN 口径） | SUPERSEDED（保留） |
| `20261024r3` | r2 ＋ main 异步定位更正 | SUPERSEDED（保留） |
| `20261024r2` | 20261024 全部 ＋ 补充页（步级分析/时间分解） | SUPERSEDED（保留） |
| `20261024` | 四腿＋复跑、2K/16K 消融、归因账本 v2、吞吐对照、一页结论、`MAIN_SERVICE_VERIFY_20261024.md` | SUPERSEDED（保留） |
| `20261023` | 20261024 的前驱（无 main 服务验证记录） | SUPERSEDED（保留） |

公开取回：`nqz1997/vllm-ascend` 分支 `r218-evidence/20261024`（独立 orphan 证据分支，不含源码）。

## 2. 口径纪律（引用前必读）

1. **同 GMU 与同总 HBM 两种容量口径独立表述。** 同 GMU 0.75：同为 29.52 GiB KV 分配，
   池 **1,719,424 vs 214,912 tok = 8.00×**；但 HBM 峰 **93% vs 77%**（每步多占 ~10.5 GiB），
   **8.00× 池 ≠ 8× 显存收益**。相近总 HBM 的公平对：**4.27×**。
2. **池容量/引擎并发打印不是实测并发。** “746×/103×” 是 `池÷(ctx+256)` 推算；
   实测活跃 batch 仅 32（2K）与 8（16K）；16K 验证至 INT2 32 / BF16 16，32 为 tested-not-max。
3. **精度与性能分账。** 所有数字只属于已测交付树组合；main 移植版默认异步 **OPEN**（INT2 中层读路径；blocking 仅时序判别），
   **不得引用本包精度/性能**。
4. **归因账本非互斥、不配平 100%。** 单项消融在同一步内可重叠，重叠量未测；
   “未被覆盖”读作**未被任何已测门控覆盖的差分观察**（非加性消融之和不构成严格下界，
   2026-10-24 晚更正；旧文中的“下界”措辞以本条为准）；不把未证实原因归为硬件下限。
   两点（2K/16K）每 KV token 归一化一致只证**两点兼容**，不构成线性标度律或机制证据
   （“7.4 µs/token 签名 / 2.5 GB/s”机制宣称已撤回，见 addendum §1.2）。
5. **首次慢样本保留。** 2K 首腿 104.39 s（prefill 离群）保留并标 SUPERSEDED；
   点估计为 3 次中位 49.31 s（4.73×）。

## 3. 已测组合（本包全部性能数字的版本边界）

- 框架：v4 PR-22 tip `983fbac1`（树 ≡ 已测 `ov_restore` overlay）；`attention_v1.py` sha `85051bbd2e74c117`
- 内核：冻结 `md5=c8a8d47a63be7ad7`，vendor `oscar_r144_v133c_grp`
- launcher：`int2_lse_fast_r152`；姿态：**eager**、前缀缓存关、block 128、MNBT 8192
- 运行时：`oscar-r103-runner`，CANN 9.0.0 / vLLM 0.22.1，Qwen3-8B，单卡 dev7，greedy，64 tok/请求

main 移植（单列）：`nqz1997/vllm-ascend` `oscar-int2/m-port-full-ut` @ `81295d899`
（main 基 `dde85f6b8`；attn `704cf4e0c3a7fa5a`；同一冻结 kernel），上游 nightly 镜像
（digest `8eaf0b4f…`，CANN 9.2.0 / torch 2.10.0 / vLLM 0.31.0 @ `db9527a4`）。
仅构建/import/BF16 冒烟/隔离 UT 135 passed（适配后）＋串行化发射 41/41；默认异步 18/24 损坏，
最小复现 B=1 1080 tok 5/12 vs blocking 0/12，定位 INT2 中层读路径。
**结论 OPEN（默认异步正确性未关闭），不标生产可用；容量记账修复已在独立分支设备验证（见 §7）。**

## 4. 目录

- `R218_PERF_ATTRIBUTION_20261023.md` — 归因主文（四腿、复跑、容量-vs-HBM、prefill/decode 拆分、标度律、消融账本、三级结论）
- `PERF_ATTRIBUTION_ADDENDUM_20261024.md` — **本轮补充**（步级二次分析、时间分解、已证实/推测/未知、版本映射）
- `R218_ONE_PAGE_CONCLUSION.md` — 一页结论；`R218_DIFF_20261023.md` — 一页差异说明
- `MAIN_SERVICE_VERIFY_20261024.md` — main 服务验证（OPEN；§6 异步定位更正、§7 容量修复设备验证）
- `capacity/` — 容量修复补丁、服务尺寸日志与电池原始分析（24/24、17/17、异步负对照 12/12）
- `PR_ADVANCE_20261024.md` — PR/依赖/修复映射/异步/容量对账报告
- `docs/` — 精度总表、限制、审阅摘要、旧结论归档
- `figs/` — 归因账本、吞吐对照、逐点证据、三联图、本轮两张 CSV
- `runs/bg1..bg5_*/` — 逐腿 `perq.json`／`serve.log`／`gates.txt`／HBM 采样
- `runs/bg6_prof_{int2,bf16}_2k_c32/` — **profiling 腿**（torch_npu chrome trace 原件
  229/18 MB、`prof_steps.jsonl` 逐步墙钟与钩子生命周期、gates；**采样腿 batch wall 含
  ~60 s 导出停顿，不可作吞吐口径**；探针开销 +197.7/+21.2 ms/步）
- `profiling_20261024/` — 腿驱动、CAN 副本与 `CAN_DIFF.txt`、sitecustomize 钩子
  （spawn/fork 双路径）、`analyze_prof_trace.py`／`make_prof_outputs.py`、
  `ATTEMPTS.md`（4 次尝试与两次失败机制的如实记录）、smoke
- `figs/PERF_PROFILING_20261024.csv`／`PERF_PROFILING_STEP_20261024.png` —
  op 级分解（78 行，含证据列）与 INT2 vs BF16 纯 decode 步构成图
- `scripts/` — 可重跑生成脚本（含 `r218_addendum_tables.py`）

## 5. 校验（当前包 = 20261024r5）

```bash
sha256sum -c r218_perf_attribution_20261024r5.tar.gz.sha256   # 包旁
mkdir -p r5 && tar xzf r218_perf_attribution_20261024r5.tar.gz -C r5
cd r5/r218_perf_attr_20261024r5 && sha256sum -c SHA256SUMS    # 包内 156 项
```

直链：<https://raw.githubusercontent.com/nqz1997/vllm-ascend/r218-evidence/20261024/r218_perf_attribution_20261024r5.tar.gz>

分支另存 r2/r3/r4 旧包（SUPERSEDED，保留可追溯）与 `PERF_ATTRIBUTION_ADDENDUM_20261024.md`
（r5 版，含 §10 profiling 补充）、`R218_ONE_PAGE_CONCLUSION.md`（含更正注记）、
`PR_ADVANCE_20261024.md`（含 §3.5 pymid 撤回）、`MAIN_SERVICE_VERIFY_20261024.md`
（05:40 版；§6.2 替换文本未并入，以 `PR_ADVANCE_20261024.md` §3.5 为准）。

本页写作时间 2026-10-24；不修改任何已有数值。

## 6. 第 4 波增量（2026-10-24 晚）

- **P6 main 异步定位证据（v3＝第 4 波）**：`r218_p6_async_evidence_20261025.tar.gz`（28MB，
  sha256 `92ac574bec121a68dee5808f50be4a7cea4a34ec199a5b27d41f40f11ae4bee7`）＝v2 全部关键件＋
  **第 4 波证据**：MIDCAP2 实操作数捕获（`p6e/p6f`——**missing-write 哨兵实锤**：async#2 全量同步后
  lse=−9999×3、cos=0.000000 vs blocking 0.999994，`p6_compare.py --ref` 可独立重跑）、WTRACE2
  轻探针 onset 捕获（jsonl+onset 样本+首事件分析）、更新版 README（**推翻第 3 波"跨代环残留"
  归因**：首事件环逐字节干净、环尾 NaN 为 rep9+ prefill 自写、步内瞬态级联）。旧版
  `r218_p6_async_evidence_20261024.tar.gz`（`70457e17…`）SUPERSEDED 保留。v2 原始描述＝
  关键张量子集（8 个环行 .pt：NaN 增长序列 r00→r05 多层）＋async/blocking 哈希流 jsonl＋
  最小复现三件套（async_diag.sh/p6_compare.py/x1080x1_req.json）＋每腿 analysis 权威判据＋
  **全量 141 文件 SHA256SUMS**（全量 445MB 原件在交付盘
  `acceptance/report_eval/p6_async_evidence/raw/`，本包为关键子集）。
  结论摘要与表述边界见包内 README；完整定位记录 `PR_ADVANCE_20261024.md` §3.5/§3.6/§9
  （本分支版本已含）。**main 诊断与冻结组合服务结果分账，不混引。**
- `MAIN_SERVICE_VERIFY_20261024.md` 更新：§6.2 替换文本已应用（pymid 撤回＋新定位＋口径降级），
  替代 r5 包内 05:40 版。
- **性能呈现更正包 r6（已发布）**：`r218_perf_attribution_20261024r6.tar.gz`（17MB，
  sha256 `fb52b69d8b57e078dc2ac4addcfdf0beec6b5cfefef6518a4710c2a969e31f75`，163 文件）。
  §10.2–10.4 的 host 间隙/各半/遮蔽表述由 **§10.5 取代**（跨测量条件混合量撤回为直接测量）；
  同条件新量：ON 12 步窗口 768.50/114.75 ms/步、窗口设备空闲 65.3%/74.8%；CSV 93 行含
  measurement_condition 列；堆叠图→三面板；12.7×→两场景观测比（条件对照 §10.5）；
  execute_model 计时不保证覆盖设备完成（两段式 return None、钩子仅 host 墙钟）；
  新旧对照 SUPERSEDED_MAP＋`_backup_20261024r5/`。**引用性能 profiling 数字以 r6 为准，
  r5 表述勿再引用**（r5 及更早 SUPERSEDED 保留）。
