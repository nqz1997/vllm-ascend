# R218 子 Agent A 交付：PR 推进 / main 集成 / 异步定位 / 容量对账

日期：2026-10-24（会话日）
角色：子 Agent A（PR 推进与 main 集成）
基线：`m-port-full-ut` @ `18d56c698` + 测试适配 `81295d899`（main 0.31 / vllm-ascend main 线）
设备：仅 NPU 7（`flock /tmp/r218_npu7.lock` 内使用；每次 leg 结束已停服释放）

---

## 0. 结论速览

| 项 | 结论 |
|---|---|
| 05–22 UT | **全部在真实 import 闭包基座上全绿**（17/17 单元；06 的 4 条包级审计测试已按语义归位到装配单元 19，06 基座现 16/16 全绿，见 §1.2 注①） |
| 上游依赖评审方式 | 仓库 CONTRIBUTING/docs/PR 模板**没有** stacked-PR 或"依赖 PR"机制；`main2main` 只是 CI 标签。→ **05+ 不开上游 PR**，只准备 fork 分支并标 blocked |
| fork 产物 | `oscar-int2/m-port-full-ut` @ `81295d899` + 17 个 `oscar-int2/prep-unit-NN` 预览分支 + 1 个 blocked 标签（§1.3） |
| 六项修复归属 | 2 项 main-only、4 项 upstream-general；**四个已提交 PR（01–04）都不需要改**（§2） |
| 默认异步故障 | **第 4 波更新（§10，推翻第 3 波"跨代环残留"读法）**：首事件 rep1/step4/L30 q/kr/vr 同时全 0x7FFF（=INT32_MAX 位型，哈希 9a887382f507 已被主 Agent独立构造复证）且**该时刻环逐字节干净——环读/写被排除**，污染经隐层流进入 QKV；**载体层实锤＝MIDCAP2 全量同步后 lse 哨兵 −9999 留存＋out 垃圾（真实 missing-write 且 enqueue 报成功，launcher 返回只含 r）**，主 Agent已亲自重跑纯 torch 参考复现（async#2 cos=0.000000 vs blocking 0.999994）；环尾 +80 行/rep 自 rep9 起为各自 prefill 自写、NaN 不跨 token 边界；最小复现 async 11–12/12 vs blocking 0/12；**指令级写入者未定位、无可合入修复 → OPEN**（§10） |
| 2.00× 容量 | 真因 = KV spec 用 `head_size`（未用 packed `head_size//4`）记账 = 每 token 每层 2048 B，物理 576 B；现池仅用掉 10.58/21.04 GiB。**独立分支已设备验证**：池 306,432 → **849,280 tok（2.77×；对 BF16 5.54×）**，HP 环 4.64 GiB 预留，blocking 电池 41/41（§4、`MAIN_SERVICE_VERIFY` §7）；产品结论仍 OPEN（未合入/未正式姿态复跑） |
| 立场 | **OPEN**；不以 blocking 回归替代正式模式验收；不称 main 可生产（§5） |

---

## 1. 任务 1 — 05..22 推进

### 1.1 方法（可复算）

- 预览树：`/tmp/r218_mpf_ut_3270309`（工作树，分支 `prep-depgrp-05-06`）。
- UT 基座构造：从 main-port 链根 `dde85f6b8` 起，按**主链历史顺序** cherry-pick 该单元的**最小 import 闭包（含单元自身）**，再叠加两处 main 适配提交：
  - `90340bb70` = `int2/ctx.py` 的 vLLM 0.31 main 导入适配（`common_cp→attention_cp`，删除 kvcomp/flashcomm2/enable_cp 再导出）；
  - `268b8ff16` = `attention_int2.py` 的 main 导入适配（19–22 单元需要）。
- 运行：`PYTHONPATH=/tmp/r218_ut_bases /home/n00928095/R218_UPSTREAM_WORK/venv_main/bin/python -m pytest --noconftest -q tests/ut/oscar`
  （`--noconftest`：main 的仓库级 conftest 依赖 vLLM core 测试夹具，本树不可用；不影响 oscar UT 语义。）
- 驱动脚本：`/home/n00928095/R218_UPSTREAM_WORK/verify_scripts/ut_matrix2.sh`、`ut_fixup3.sh`；**2026-10-24 二轮重排后以 `ut_matrix3.sh` 为准**（审计测试归位 19 + 21/22 测试适配进分支本体），原始日志 `ut_matrix3_20261024.{log,tsv}`
- 原始日志：`verify_scripts/ut_matrix2_20261024.{log,tsv}`、`ut_matrix1_20261024.{log,tsv}`、`ut_fixup3_20261024.log`

> 首版矩阵（`ut_matrix.sh`）有缺陷：基座只含依赖单元、**漏掉了被测单元自身**，测的是"依赖基座"而非单元。已用 `ut_matrix2.sh` 修正并全量重跑；下表全部来自修正版。

### 1.2 依赖表 + UT 结果（05..22）

| 单元 | 真实 import 闭包（最小基座，含自身） | UT（tests/ut/oscar 全量） | 状态 |
|---|---|---|---|
| 05 | 01 03 05 | 37 passed | PASS |
| 06 | 01 06 | **16 passed** | PASS（注①：审计测试已移出） |
| 07+09 | 01 03 05 06 07 09 | 68 passed | PASS（**成对不可分**；不含审计测试，注①） |
| 08 | 01 03 05 08 | 43 passed | PASS |
| 10 | 01 02 03 05 06 10 **12** | 67 passed | PASS |
| 11 | 01 03 05 06 **07 09** 11 | 72 passed | PASS（需 PR-07 的 `_oscar_dbg`） |
| 12 | 01 02 03 05 06 12 | 57 passed | PASS |
| 13 | 01 03 05 06 13 | 41 passed | PASS |
| 14 | 01 03 05 06 13 14 | 44 passed | PASS |
| 15 | 01 03 05 06 10 12 15 | 60 passed | PASS |
| 16 | 01 02 03 05 06 10 12 13 14 16 | 73 passed | PASS |
| 17 | 01 03 05 06 07 09 10 12 17 | 87 passed | PASS |
| 18 | 01 02 03 05 06 07 09 10 12 13 14 16 18 | 102 passed | PASS |
| 19 | 01–19 全部 | **123 passed** | PASS（**含接收的 4 条包级审计测试**——从 ctx 文件移到 assembly 文件、同基座同总数，见注①） |
| 20 | 01–20 全部 | 123 passed | PASS |
| 21 | 01–19 + 21 | **135 passed**（适配已进分支本体，注②） | PASS |
| 22 | 01–19 + 21 + 22 | **135 passed**（适配已进分支本体，注②） | PASS |

注①（2026-10-24 二轮重排，取代初版结论）：06 原带的 4 条**包级审计**测试（`test_backend_modules_have_no_star_imports`、`test_registry_names_never_bare_globals`、`test_remaining_bare_globals_names_are_module_local`、`test_every_module_registry_binding_is_the_ctx_object`）扫描**整包**模块，而 06（ctx 枢纽）基座上包不完整，**在自己单元基座上必然失败**——初版把它们记作「设计使然的假失败」不成立，已按测试语义归位：
- **接收单元＝19（装配单元）**。理由：(a) 四条断言都是整包不变式（全模块无 star import、11 个 handoff 名不走裸 globals()、其余裸 globals() 名模块局部、每模块 `_R2XX_G` 绑定同一 ctx 对象），只有在**包含完整包的树**上才可断言且才有意义；(b) 19（`e2638eae2` "assemble the INT2 backend from the twelve mixins"）是第一个 15 个包模块齐全的单元（其闭包＝01–19）；(c) 其测试文件 `test_int2_assembly.py` 语义即「装配审计」（方法清单 53/12 mixin），整包审计属同一审计职责；(d) 07+09 基座只含 ~6 个模块（缺 08/10-18），把整包门放那里只会**欠审计**；17 是 decode mixin（基座缺 08/11/13-16/18），同样不完整。
- 实现：`7a23bec98`（06 侧：`test_int2_ctx.py` 只留 4 条 ctx 模块内契约测试）+ `e5e688038`（19 侧：4 条审计测试连同 `AUDIT_REGISTRY_NAMES`/`_AUDIT_GLOB` 进 `test_int2_assembly.py`，测试名不变）。驱动 `ut_matrix3.sh`（闭包修正含 11 需 07+09），16 行全绿：06 **16/16**、19 **123**（审计 4 条从 ctx 文件移入 assembly 文件、同基座同总数）、20 123、21/22 **135**；07+09..18 各行数字−4（其基座本就不该跑整包审计）。05/08 闭包不含 06，数字不变（37/43）。
- `m-port-full-ut`（81295d899）集成分支不动：整包在位，`test_int2_ctx.py` 9 条照旧全绿（135 计数不变）。

注②（2026-10-24 更新：适配已进分支本体）：21/22 首轮各有 5 failed，全部在 `tests/ut/oscar/test_kv_int2.py`——main 把 release 线的 `get_cache_scale(kv_type, name)` 谓词换成了 `get_cache_scale_mapper() -> WeightsMapper`，且 `modelslim_config` 不再导出 `FusedMoE`。适配内容（`81295d899`）：改用 `AscendModelSlimConfig.get_cache_scale_mapper(SimpleNamespace(...)).map_name()`；INT2 offset 名字**原样透传**而非 None；去掉 `msc.FusedMoE` patch；补 `_update_packed_modules_mapping` 桩。该提交现已 cherry-pick 进 **prep-unit-21 / prep-unit-22 分支本体**（不再依赖外部测试文件替换；`ut_fixup3.sh` 方式作废）。验证＝自 fork 推送后 ref 的**全新 worktree**（`/tmp/r218_p21_check`、`/tmp/r218_p22_check`）用分支自带测试跑 `tests/ut/oscar`：**135 passed / 135 passed**。

### 1.3 分支与 SHA（本地 / fork `github.com/nqz1997/vllm-ascend`）

集成主分支（已推送并 `ls-remote` 校验）：

| 本地分支 | SHA | fork 分支 |
|---|---|---|
| `m-port-full-ut` | `81295d899` | `oscar-int2/m-port-full-ut` |

预览分支（fork 上命名 `oscar-int2/prep-unit-NN`；均为"就绪但因上游未接受 01/03 而 blocked"）。**2026-10-24 二轮（force 更新，`--force-with-lease`）**：除 05/08（闭包不含 06，树未变）外全部重推，嵌入注①的审计归位两提交（`7a23bec98`→06、`e5e688038`→19）与注②的 21/22 测试适配：

| 单元 | 本地分支 | 本地 SHA | fork SHA（二轮后经 GitHub API 复核一致；git 协议超时） |
|---|---|---|---|
| 05 | `utc-05` | 6e401e6e2 | 6e401e6e2 |
| 06 | `utc-06` | 048e14aa3 | 048e14aa3 |
| 07+09 | `utc-0709` | 1ce0a1ea6 | 1ce0a1ea6 |
| 08 | `utc-08` | fe6357aec | fe6357aec |
| 10 | `utc-10` | b2426d27f | b2426d27f |
| 11 | `utc-11` | 69b1f313d | 69b1f313d |
| 12 | `utc-12` | b83e01f18 | b83e01f18 |
| 13 | `utc-13` | d7472545f | d7472545f |
| 14 | `utc-14` | c56976240 | c56976240 |
| 15 | `utc-15` | 5585d499a | 5585d499a |
| 16 | `utc-16` | 3f3d16fb0 | 3f3d16fb0 |
| 17 | `utc-17` | cc57ace5a | cc57ace5a |
| 18 | `utc-18` | 7b4902457 | 7b4902457 |
| 19 | `utc-19` | d6eaad09c | d6eaad09c |
| 20 | `utc-20` | 008b7fc8b | 008b7fc8b |
| 21 | `utc-21` | db15c9224 | db15c9224 |
| 22 | `utc-22` | eab326066 | eab326066 |
| 05+06 依赖组 | `prep-depgrp-05-06` | 90340bb70 | 90340bb70 |

标签：`r218-prep-depgrp-05-06-blocked-on-01-03` → `90340bb70`（**blocked 标记载体**）。
（推送输出已确认 `* [new tag] r218-prep-depgrp-05-06-blocked-on-01-03 -> r218-prep-depgrp-05-06-blocked-on-01-03`，本地 tag 指向同一对象；事后复核 `ls-remote` 因网络 HTTP/2 抖动未能再次连通，非推送失败。）

> （初版 `ut2-11b`/`ut2-17`/`ut2-18` 已被二轮统一命名 `utc-*` 取代。）
> 预览分支内容 = 最小闭包基座 + 该单元，**不含**测试适配；用途是复现 UT 而非提交候选。提交候选仍是 01–04（已投）与将来基于 main 重建的 05+。

### 1.4 维护者接受的依赖评审方式（核实结论）

已核实的证据：

- `CONTRIBUTING.md` 只有指向官方 contributing 文档的指针；`docs/source/developer_guide/contribution/*.md` 未出现 stacked PR / dependent PR / 依赖声明机制。
- `docs/source/developer_guide/contribution/testing.md:282`：`main2main` 是 **CI 标签**（对 vLLM main 已验证 commit 与对应 release tag 各跑一次全量），**不是**依赖评审方式。
- `.github/PULL_REQUEST_TEMPLATE.md` 为通用模板（What/Why、user-facing、How tested），无依赖字段。
- 现有 4 个 Draft（#19577/#19568/#19569/#19570）均为 **main 基、独立可评审的最小差异**。

**明确说明**：上游只接受 main 基、可独立评审的 PR；不存在"跨 fork 堆叠"通道。fork 内部 Draft 不构成上游贡献。因此 **05–22 不开上游 PR**，仅在 fork 上备好分支并标 "ready, blocked on 01+03 / 01"（本表 + 标签即标记）。待 #19577（01，main 基；release 基首投 #19552 已关闭取代）被接受后，按同一"最小差异"方法逐个重建提交。

---

## 2. 任务 2 — `18d56c698` 六项修复 → 贡献单元映射

先核实：**四个已提交 PR（01–04）都不触碰这六个文件**（`m-pr-01/02/04` 文件集合无 `patch_kv_cache_dtype.py`、`worker/worker.py`、`int2/quantcache.py`、`int2/bridge.py`、`int2/slotstate.py`、`attention/attention_v1.py` 的这些 hunk）→ **不需要改动已投 PR**。

| # | 修复 | 文件 | 归类 | 归属贡献单元 | 是否需要新 PR |
|---|---|---|---|---|---|
| 1 | INT2 存储 dtype 注册（`STR_DTYPE_TO_TORCH_DTYPE["int2_per_token_head"]=uint8` + `_CACHE_DTYPE_WITH_ASCEND` 增补 + 幂等检查） | `patch/platform/patch_kv_cache_dtype.py` | **main-only**（release 线无此文件；全树仅 pr-21/22 的 `get_kv_cache_shape`/`model_runner_v1` 引用 int2） | 需并入将来的 **PR-21/22** 或单开一个 "platform dtype registration" 单元 | 是（新单元，或并入 21/22） |
| 2 | worker 侧 `cache_dtype == "int2_per_token_head" → torch.uint8` | `worker/worker.py` | **main-only**（main 的 worker 走 `STR_DTYPE_TO_TORCH_DTYPE` 查表；release 线不同） | **PR-22** | 否 |
| 3a | release 线 kvcomp/hamming-sparse 分支剔除（main 无该特性） | `attention/attention_v1.py`（`enable_hamming_sparse`） | **main-only** | **PR-20** | 否 |
| 3b | INT2 免静态量化 recipe 门（`enable_c8_quant=False`） | `attention/attention_v1.py` | **upstream-general**（INT2 自带 per-token-head scale，不能依赖 C8 的 checkpoint recipe） | **PR-20** | 否 |
| 4 | 分页 scatter 从 `.view()` 平坦化改为 `(block, offset)` 跨步写（V2 block-strided pages） | `int2/quantcache.py` | **main-general**（V2 runner 物理页有 padding，任何 V2 后端都适用） | **PR-12** | 否 |
| 5 | CANN 根目录改为环境解析（`ASCEND_HOME_PATH`/`ASCEND_TOOLKIT_HOME`，回落 `/usr/local/Ascend/cann-9.0.0`）替代硬编码 | `int2/bridge.py`（3 处 include/LD/rpath） | **upstream-general**（上游 CI 镜像 CANN 版本不同） | **PR-13**（或并入 PR-01 的路径处理） | 否 |
| 6 | HP 行池 +1（`_tt_mseq = max(_TT_MAX_SEQS, 4, _mns + 1)`，V2 runner 可能追加 1 个 padding 请求） | `int2/slotstate.py` | **main-general**（V2 批宽 = max_num_seqs+1） | **PR-07** | 否 |

**最小通用实现状态**：3b/4/5/6 的实现即上表所在分支的现有实现（main 线代码就是"最小通用"形态——不含本机路径、不含 release 线特性假设），并已被 §1.2 的 UT 覆盖（对应单元 PASS）。1/2 是 **main 独有胶水**：需要在 main 线新增/复用一个单元把"dtype 注册"从本地适配提升为上游可接受的通用实现（当前实现已写成通用形式：环境变量解析、`setdefault` 幂等、无本机绝对路径），**新 PR 依赖 01（#19577）先合并**，否则注册代码没有 INT2 消费者可评审。

---

## 3. 任务 3 — 默认异步故障定位（同等最高优先）

### 3.1 最小复现（已定稿，可独立重放）

**场景**：单请求、1080 token 提示（`"The quick brown fox jumps over the lazy dog. "` 截断到 4860 字符）、`max_tokens=24`、`temperature=0`、`--enforce-eager`、默认异步。
**几何**：prefix 128 + recent 896 = 1024 走 HP bf16 环；中层 = 1080 − 1024 = **56 token** 走 INT2 分页缓存。

| 对照 | 结果 |
|---|---|
| 默认异步 | **5/12 坏**（整段 24 token 全为 `!` 的退化输出） |
| `ASCEND_LAUNCH_BLOCKING=1`（同请求、同配置、仅此变量不同） | **0/12** |
| 无中层（890 token，4 行批） | **0/6** |
| 前缀缓存关闭（有中层） | 7/12 坏 |

判定：故障**与 INT2 中层路径共存亡**，与批大小、前缀缓存无关；blocking 只证明"时序相关"，不作归因（未据此归因 CANN）。

### 3.2 二分与消融（全部在 NPU 7、flock 内、逐 leg 停服）

| 腿 | 配置 | 请求 | 坏/总 | 结论 |
|---|---|---|---|---|
| `int2base` | 生产默认 | ragged/l4/l4mix/long2 ×6 | 18/24 | 基线 |
| `bf16a` | **BF16** 同请求 | 同上 | **0/24** | 非框架/CANN 通用竞态，属 INT2 路径 |
| `e_nobatched` | `R161_BATCHED_MID=0` | 同上 | 18/24 | **死开关**（主树 0 处读取），A/B 无效 |
| `e_nofused` | `R152_FUSED=0` | 同上 | 18/24 | **死开关**（同上） |
| `e_up1` | `R218_UPSYNC=1` | 同上 | 18/24 | 图路径专用，eager 无效 |
| `e_up3` | `R218_UPSYNC=3` | 同上 | 17/24 | 同上 |
| `e_pyquant` | `R113_QUANT_CPP=0` | 同上 | 11/24 | C++ 量化器**有贡献但非唯一因** |
| `e_nomiddle` | `R109_THREETIER_MIDDLE=0` | — | 启动即 507015 aicore 异常 | 不支持配置，**不能作阴性对照** |
| `noprefix` | `--no-enable-prefix-caching` | l4/ragged ×6 | 7/12 | 前缀缓存**非必要条件** |
| `x900x4` | 4 行 × ~890 token（无中层） | ×6 | **0/6** | 无中层→不坏 |
| `x1601x1` | B=1 1601 token（中层 577） | ×12 | 8/12 | B=1 也坏 → 非批/行交错问题 |
| `x1601x1_blk` | 同上 + `ASCEND_LAUNCH_BLOCKING=1` | ×12 | **0/12** | 时序相关 |
| `x1080x1` | B=1 1080 token（中层 56） | ×12 | **5/12** | **最小复现** |
| `x1080_wsync` | + `R166_WSYNC=1`（每次分页写后 device sync） | ×12 | 9/12 | 写→读边**不是**缺口 |
| `x1080_hpsafe` | + `R164_PREFILL_SAFE=1`（HP 环写用自有 clone+sync） | ×12 | 8/12 | HP 写生命周期**不是**主因 |
| `x1080_pymid` | + `R113_MIDDLE_CPP=0`（Python 中层操作数准备） | ×12 | **11/12** | **换 Python 操作数准备路径不治**。⚠更正（2026-10-24 复核）：该腿**不构成对中层自定义算子的排除**——`R113_MIDDLE_CPP=0` 只把操作数 staging 从 C++ `oscar_middle_prep` 换回 Python ATen，`R112_LSE_FAST=1` 默认未变，自定义算子仍被调用（`middle_candidate.py:542 launch_lse_fast`；`R133_GRAPH_V1=1` 时 :504/:530 `launch_lse_v1_own`；R112_LSE_FAST=0 时 :563 `launch_lse`），见 §3.5 |
| `x1080_qsync0` | + `R113_QUANT_SYNC=0` | ×12 | **12/12** | 量化器→scatter 的 host sync **确实掩盖了一条边**（5/12→12/12），但**不是**主因 |

### 3.3 已排除 / 已确认

- **排除（复核后仍成立，均不依赖 pymid 腿）**：框架/CANN 通用发射竞态（BF16 0/24）、前缀缓存交互（noprefix 仍坏）、批宽/行交错（B=1 仍坏）、分页写→读顺序（写后 device sync 不治，反而 9/12）、HP 环写的 copy-engine 生命周期（`R164_PREFILL_SAFE=1` 不治）。
- **⚠撤回（2026-10-24）**：原「排除 INT2 中层 C++ 算子（Python 中层路径仍 11/12）」**不成立**。`R113_MIDDLE_CPP=0` 时 Python 准备路径**仍调用**自定义算子（`launch_lse_fast`/`launch_lse_v1_own`/`launch_lse`），pymid 腿只证明「换 Python 操作数准备不治」，中层自定义算子回到**候选集**（见 §3.5 file:line）。
- **确认**：故障需要 INT2 中层存在（无中层 0/6）；表现为**整段退化**（24 token 全 `!`），即首个 decode 步的注意力输出已崩。
- **⚠降级（2026-10-24）**：原「存在两条以上独立边」改为**观察**：失败率随同步/量化器开关显著变化（`R113_QUANT_SYNC` 0→12/12 vs 1→5/12；`R113_QUANT_CPP` 0→11/24 vs 1→18/24）——host sync 确实掩盖了至少一条通路，但**不能据此断言独立边数**（同一缺陷在不同时序下可有不同触发率）。

### 3.4 结论与后续（OPEN）

- 症状在 **INT2 中层（paged INT2 KV）参与的首个 decode**：prefill 只写不读中层（prefill 注意力走 float KV，见 `int2/prefill.py:35` 文档串），decode 首次 gather+dequantize 中层时输出即退化。
- 量化器同步边（`R113_QUANT_SYNC`）已证非充分修复；**C++ 中层算子排除已撤回**（§3.5），故剩余候选＝ **eager 三层 decode 胶水**（中层 gather/dequant 的输入：block table、slot、scale 缓存，与 HP 环 slide / 元数据填充之间的流序、`_ensure_int2_scale_buffers` 首次分配与首次读的先后）**∪ 中层自定义算子本身在异步时序下的行为**。对后者的正确定性须用独立纯 torch 参考（保持量化后操作数、旋转、布局、有效长度、LSE 语义一致）重做，不再拿 `R113_MIDDLE_CPP` 开关当排除证据。
- 进一步收敛建议（按性价比）：在 eager 路径逐点插入 device-side 事件等待（不改变语义、不加 host sync），二分"gather 输入前 / dequant 后 / HP slide 后"三点；配合 `R218_QINDUMP` 之类的 dump 判断"存进去的就错"还是"读出来才错"。
- **当前状态 OPEN**：未取得 0/N 的可合入最小修复，因此不声称异步正确性关闭。复现脚本与全部原始日志见 §6，任何一方可直接重放（单 leg ~2.5 分钟）。


### 3.5 【更正记录】`R113_MIDDLE_CPP=0` 不排除中层自定义算子（2026-10-24 方法论复核）

复核基线：`m-port-full-ut` @ `81295d899`，`vllm_ascend/attention/int2/middle_candidate.py`（`_r109_middle_candidate`）：

- `:81-82`：`R113_MIDDLE_CPP == "1" and R112_LSE_FAST == "1"` 才进入 C++ 单调用准备分支（`:226 oscar_middle_prep`；R118 统一 staging 腿 `:219 launch_lse_fast` 也在该 gate 内）。
- `R113_MIDDLE_CPP=0` 时落到 Python ATen 操作数准备（gather/permute/`[:mid_len]` 截断/scale 展平/`torch.matmul(q,R_k)`，约 `:315-410`），随后**仍调用自定义算子**：`:416` `R112_LSE_FAST=="1"` → `:542 launch_lse_fast`（默认腿；pymid 腿仅 `-e R113_MIDDLE_CPP=0`，`R112_LSE_FAST` 取 `serve_int2_exp.sh:14` 默认 1）；`R133_GRAPH_V1=1` 时 → `:504`（R136 unified）/`:530`（R135 tight）`launch_lse_v1_own`；`R112_LSE_FAST=0` 时 → `:563 _r91_mod.launch_lse`。
- `middle_exec.py:484-485`：批化中层路径同样要求 `R113_MIDDLE_CPP=1`，pymid 腿的批化入口也关闭，全部中层调用走上述 per-row 候选。

结论：pymid 腿（11/12）的自变量＝「操作数准备 C++→Python」，**自定义注意力算子（launch_lse* 家族）在两腿中都在执行**。故该腿只证明「换 Python 准备路径不治」，不能作为「C++ 中层算子无罪」的排除证据。GPT 的判断与源码一致，本节据此更正 §3.2/§3.3/§3.4 与 `MAIN_SERVICE_VERIFY_20261024.md` §6.2（替换文本已交主 Agent）。


### 3.6 设备定位轮 2（2026-10-24 13:16–14:53Z，NPU 7 / flock，窗口见 lock log）

驱动：`verify_scripts/p6_run.sh` + 探针（R117_MID_DIAG 为**树内** env 门探针；R218_KRVDBG/R218_RINGROWDBG 为本会话容器内临时补丁，**已还原**——容器 `middle_exec.py` md5 回到 `9ea86ce1…`，`git status` 干净）。

| 腿 | 配置 | 结果 |
|---|---|---|
| `p6a_mdiag_async` | async + R117_MID_DIAG=1（哈希流） | **8/12 坏**（诊断同步不掩盖） |
| `p6b_mdiag_blk` | 同上 + blocking | **0/12** |
| `p6g_krv_async` | async + R117 + KRVDBG（环写输入值哈希） | **11/12 坏** |
| `p6h_krv_blk` | 同上 + blocking | 0/12 |
| `p6i_sfix_async` | + `R166_STREAMFIX=ring`（out= 写环） | **12/12 坏**（更差，不治） |
| `p6j_eslide_async` | + `R164_EAGER_SLIDE=1`（恒 slide 语义） | **9/12 坏**（不治） |
| `p6k_row_async` | async + 环行张量捕获（96 文件） | 12/12 坏 |
| `p6l_row_blk`(rerun) | blocking 同上 | **NOT-READY**（设备内存残留：EngineCore 反复启停后 60.1/64G 未释放，无进程持有；p6z 复查同样 NOT-READY，环境性非回归） |

**结论（每条都有原始文件）**：

1. **好 rep 上 async==blocking 逐字节**：p6a 前 4 rep 全部 828×2 条记录（页 src_k/src_v/src_ks、环、q、中层 out/lse）与 blocking 完全一致。
2. **写侧（INT2 页）无罪**：所有 12 rep 的 `src_k/src_v/src_ks` 哈希从不与 blocking 分歧——「存进去就错」被否定；量化页内容正确。
3. **首个分歧张量＝HP 环 bf16 行**：坏 rep 首个 decode step 内（p6a rep5 rec18；p6g rep2 rec11）`ring_k/ring_v` 先分歧，此刻 q、中层页、**中层算子输出**全部仍与 blocking 逐字节一致；q 从下一记录起才错（该层 HP 层注意力读到坏环 → 输出错 → 后续全错）。中层自定义算子以「分歧点输入/输出逐字节一致」**直接排除该缺陷类**（不经 R113 开关）。
4. **写落地被污染而非写值错**：p6g rep2 分歧点上 `key_rot/value_rot`（环写输入值）哈希与 blocking **相同**，环行却已不同——NaN 不经写入值进入。
5. **污染形态＝环 recent 窗 NaN**：张量级（p6k，层 8–23 × 6 rep）：recent 窗列段 [128,1024) 变 NaN，prefix 段 [0,128) 始终正确；NaN 计数每代恒增 **1,310,720 元素/rep**（rep2 1.09M → rep5 5.02M，等差）＝**跨代环残留累积**（与 2026-10-17 r218-cross-generation-ring-staleness 的旧怀疑吻合）。
   ⚠**第 4 波更正（§10）**：本条"跨代残留"归因被推翻——首事件时刻环逐字节干净（环读/写排除）；环尾 +80 行/rep 自 rep9 起为各自 prefill 自写（r09=74/r10=154/r11=234 行，锚 1023，层间同构）；NaN 不跨 token 边界（每步瞬态级联）。等差计数观察本身仍真，归因以 §10 为准。
6. **环内容本就逐代合法不同**（blocking 亦然：ring_k 每 rep 不同、rk_pre/q 相同），async 前几 rep 与 blocking 的逐 rep 哈希**完全一致**，从首个坏 rep 起才分岔。
7. **修复候选两枚均不治**（3.6 表 p6i/p6j）→ 未取得可合入最小修复，**P6.e 保持 OPEN**；capfix 叠加复验按任务仅在取得修复后执行，故未跑。
8. **未证实（OPEN）**：NaN 的**种子**来源（候选：外部核/工作区越界写命中环分配；环读侧 slide 复制已污染内存放大）——两候选均未闭合；**不归因 CANN**；不以失败率差异断言独立边数。侧流检查：树内 side-stream 仅出现在默认关闭的 warmup/capture 协议块（middle_exec.py:766/1696/2087，两端 wait_stream 配对）。

**最小复现包（就绪）**：容器 `r218-main-verify`（镜像=nightly，树=`81295d899`）+ `/tmp/x1080x1_req.json` + `flock … async_diag.sh <tag> int2exp`（REPS=12）×（async vs `ASCEND_LAUNCH_BLOCKING=1`）；证据 `/tmp/r218_p6_host/{p6a_mdiag_async,p6b_mdiag_blk,p6g_krv_async,p6h_krv_blk,p6k_row_async}`（jsonl 哈希流 + 96 个环行张量）+ 分析脚本 `p6_mdiag_diff.py`；复现率 5–12/12（async），0/12（blocking）。


### 3.7 第 5 波（2026-10-25 01:33–02:0xZ，NPU 7 / flock）：根因定谳＝torch_npu 任务队列提交边界缺失，修复 12/12 全绿（P6.e 闭合候选）

**机制（T1，全部 file:line 于 torch_npu 2.10.0.post7 精确构建 commit `3363ea59d49f3e08cfd8d4a1f532b756ccda0682`，取证源拷贝 `/tmp/r218_p6_host/p7/T1_SOURCE_PROVENANCE.txt`）**：

- torch_npu 的 op_api/ATen 算子 host 侧提交**不在调用线程执行**：`OpCommand::RunOpApi`（OpCommand.cpp:183-228）在 `TASK_QUEUE_ENABLE=1`（**缺省 1**，OptionsManager.cpp:645）时经 `enCurrentNPUStream`（NPUStream.cpp:739-782）→ `Repository::Enqueue`，由 **consumer 线程**异步执行（NPUQueue.cpp `ReadQueue` 只在 `manager().Call()` 执行完后才推进 read_idx:493）。
- `NPUStream::stream(false)`（NPUStream.cpp:838-847）返回**裸句柄、不排空任务队列**；官方隐式转换 `operator aclrtStream()` 与 `stream(true)` 才先 `MakeSureQueueEmpty`（NPUQueue.cpp:243-362，eventfd 阻塞到 ring 清空＝**host 提交边界**，非设备同步）。`ASCEND_LAUNCH_BLOCKING=1` → `GetTaskQueueEnable()=0`（OptionsManager.cpp:157-168/630-634）→ 内联执行＋逐算子同步——**这就是 blocking 腿恒对的机制**。
- r152 launcher（`csrc/oscar/int2_op_launch_lse_fast_r152.cpp`，pristine md5 `a46aa35e076117a235aa4c080113da96`）全部 7 个直调入口都是「`stream(false)` → ATen（fill 哨兵/staging）→ **直接 ACLNN**」模式（129/137/139、254/255、543/544、604/605、656/657、1046/1047、1176/1186 行族）：直调在调用线程**立即提交**，可越过 consumer 尚未处理的哨兵 fill **与调用方的算子 staging**——同时解释 MIDCAP2 捕获 #2（lse 全 −9999＋out 垃圾）与首事件 q/kr/vr 0x7FFF（内核读到未写完的输入）。该服务姿态实际入口＝`oscar_middle_prep`（serve log `[R218-QBOUND] entry=oscar_middle_prep slot=1 ACTIVE`）。

**三分对照实验（T2，x1080x1×12、默认 async、逐腿冷启动；窗口 lock log 01:33:21–01:43:03Z）**：

| 腿 | 树 | 结果 | 裁定 |
|---|---|---|---|
| `p7a_base` | pristine | **11/12 坏** | 基线复现（与第 4 波一致） |
| `p7b_bound` | 修复＝fill/staging 后、直调前 `stream(true)` 边界＋r/ex/lr 硬检查 | **0/12 坏**（0 TORCH_CHECK 触发） | **假设成立（因果）** |
| `p7c_wrong` | 仅旧位置（fill 之前）`stream(false)→stream(true)` | **0/12 坏** | 见下「错误边混淆」 |

- **H_A 任务未正确提交：证伪**（所有 r=0/lr=0；blocking 同码正确）。
- **H_B 哨兵晚到覆盖（更准确：直调越过任务队列——哨兵与输入 staging 双重受害）：成立**（边界修复 0/12）。
- **H_C 缓冲区复用（g_ws 跨层共享）：证伪**（bound 腿 g_ws 共享制不变即 0/12；无需复制 workspace）。
- **错误边混淆（诚实记录）**：旧位置（fill 前）flush 也治愈本复现——它排空了深层积压，遗留「fill 单算子竞态」由 GetWorkspaceSize 的 host 耗时（~88µs/call 量级，r152 源注释 msprof）掩盖；但这**不是源码级顺序保证**（Enqueue 与直调之间无顺序原语），正确修复＝fill 之后的右边界。任务书「不能只把旧位置改 stream(true)」的警告被实验精确证实为「能治标、非保证」。

**修复（T3，分支 `oscar-int2/launcher-commit-boundary`，本地 `74e0a67b2`/树 `4207cf23`＝设备验证字节同一，cpp md5 `c2ca87a90a15da012da964a7abab0fd8`；fork 已推 `22834cabc`（树逐字节同）；主 Agent 裁定归属 **#19570**＝m-pr-04 后续提交 `96ef95c9a`（tip 链 82dbc3e24→fc030caa→96ef95c9a＝ruff/禁 re 仓规修正后终版；DCO/pre-commit/main check pass，cpu-ut 运行中；PR 评论 issuecomment-6392527971＋rebase 注记；本地孪生 `9aa1894cf`；树 `2568c99f` 系＝314f9186e 加固＋边界，容器 BUILD-IMPORT OK `r113.orch.v9+r145v3+r218p7bound`＋契约测试 4/4（regex 导入版））**：7 个直调入口统一加 `r218_qbound_flush`（＝官方 `stream(true)` 边界，含 flush 失败 nullptr 硬报错——nullptr 若流入 aclnn 即默认流跨流灾难）＋ GetWorkspaceSize r/ex 与 launch lr 的 TORCH_CHECK 硬报错（替代「只查 r 后继续消费输出」）＋ `qbound_stats()` 计数器＋每入口一次性 ACTIVE 标记。**保持默认异步**（无全局 ASCEND_LAUNCH_BLOCKING、无设备同步）；契约测试 `tests/ut/oscar/test_int2_launcher_commit_boundary.py`（4 项，静态顺序契约：边界必须在哨兵之后、直调之前，7 入口全覆盖＋lr 检查数守恒）。

**开销记账**：flush 快路径 0.32µs/call（vs raw 0.09µs）；带 1 个挂起算子（生产典型）排空 ~16µs/call（独立微基准 `/tmp/flushbench`，NPU7）；36 层/步 ⇒ ~0.6ms/步理论上限，服务级吞吐三腿一致（4.8–4.9 tok/s，不可测差异）。

**遗留边界（如实）**：修复覆盖「直调越过已入队 ATen 提交」这一边；未触及（也无需触及）g_ws 复用、quant/scatter 路径（自有 barrier 且 p6c/p6d 已证清白）、图模式 op_v3（本姿态 eager 未激活，边界同样已加）。

**默认异步全电池（T4，修复树，窗口 01:55:13–02:14:31Z，lock log）**：

| 腿 | 内容 | 结果 |
|---|---|---|
| `p8c1/c2/c3` | 3 次冷启动 ×（x1080x1 + ragged/l4/l4mix/long2 ×3 rep） | **45/45 全绿**（0 TORCH_CHECK） |
| `p8s` | 连续生成 sweep（reuse/long1/mix2/h8/s4/n8/n2/n3/n4/single ×2，含 7200 项长 prompt、槽位复用、批量更替） | **20/20 全绿** |
| `p8cap` | 第 4 冷启动（同形状；注：capfix 因遗留未跟踪文件 apply 失败，此腿实为 fix-only） | **15/15 全绿** |
| `p9` | **真 capfix 叠加**（清遗留 `tests/ut/oscar/test_int2_kv_spec.py` 后 `81295d899..db6398286` 干净 apply） | KV 池 **849,280 tok（414.69×@2048）**；smoke 输出干净；CAPFIX-REVERTED |

容量对账（同日同设备）：INT2 记账基线（fix 树）306,432 tok；BF16 153,216 tok → 记账 2.00×；capfix 849,280/153,216 = **5.54×**（对 BF16）、849,280/306,432 = 2.77×（对记账）——与 2026-10-24 capfix 记录逐位复现。**按用户裁定 5.54× 不升格产品结论**。可用 KV 预算 16.40 GiB。

**UT 回归（fix 文件 staged，容器内 tests/ut/oscar 全量）**：**139 passed**（含新增 4 项契约测试）22.5s。

**提交形态（T5，主 Agent 已裁定 2026-10-25）**：设备验证原树＝本地 `/home/n00928095/R218_UPSTREAM_WORK/p7_tree` 分支 `oscar-int2/launcher-commit-boundary` commit `74e0a67b2`（2 文件：launcher cpp md5 `c2ca87a9…` + 契约测试），基＝m-port tip `81295d899`；**已推 fork `22834cabc`**（树逐字节同，供溯源）。**PR 归属＝#19570 后续提交 `96ef95c9a`（终 tip）**（与 vendored r152 同文件，避免同文件冲突 PR；#19570 已 ready、20 线程已解）。与 capfix 分支 `oscar-int2/capfix-int2-spec @ db6398286` 正交。

**P6.e 状态变更：OPEN → 修复候选已验证（本节）**——「默认异步=INT2 中层读路径」缺陷的载体从「未归因的中层污染」定谳为「launcher 直调越过 torch_npu 任务队列提交边界」；修复保持默认异步、零设备同步、每调用 0.32–16µs。待主 Agent 裁定合并后即可关闭。


---

## 4. 任务 4 — 2.00× 容量对账（可复算）

### 4.1 实测事实

| 量 | INT2 | BF16 | 来源 |
|---|---|---|---|
| Available KV cache memory | 21.04 GiB | **21.04 GiB** | serve 日志 `worker.py:748` |
| NPU KV cache size | 306,432 tokens | 153,216 tokens | `kv_cache_utils.py:2464` |
| 比值 | **2.0000×** | 1× | 与 uint8/bf16 元素宽度比完全相同 |

（日志：`/tmp/serve_int2base.log`、`/tmp/serve_bf16a.log`，容器 `r218-main-verify`。）

### 4.2 引擎记账 vs 物理记账

引擎侧：`Attention.get_kv_cache_spec`（`vllm/model_executor/layers/attention/attention.py:671-678`）构造
`FullAttentionSpec(block_size=128, num_kv_heads=8, head_size=128, head_size_v=128, dtype=uint8)`；
`AttentionSpec.unpadded_page_size_bytes = num_heads × num_states × (head_size + head_size_v) × dtype_size`
（`vllm/v1/kv_cache_interface.py:528-536`）→ **8 × 128 × 256 × 1 = 262,144 B/block = 2,048 B/token/层**。
`num_blocks = 21.04 GiB / (262,144 × 36) = 2,394` → 306,432 token。

物理侧（`attention_v1.py:276-290` 的 `get_kv_cache_shape` = `(2, nb, 128, nkv, 128//4)`）：

| 组成部分 | 每 block | 每 token/层 | 总量（2394 block, 36 层） | 出处 |
|---|---|---|---|---|
| INT2 packed K/V `uint8` | 65,536 B | 512 B | **5.26 GiB** | `get_kv_cache_shape` |
| 四组 scale/zero 缓存 bf16 `[nb,128,8]` | 8,192 B | 64 B | **0.66 GiB** | `int2/quantcache.py:267-307` |
| HP 环 bf16 `[36,2,ms,1028,8,128]`，ms = max(32, 4, 33) = 33 | —（与 block 无关） | — | **4.66 GiB** | `attention_int2.py:206` + `slotstate.py:188` |
| 合计 | | **576 B** | **10.58 GiB** | |
| 未使用（同预算内） | | | **10.46 GiB（49.7%）** | |

**对账结论**：2.00× 不是 INT2 的真实容量收益，只是 dtype 宽度比。引擎按 `head_size=128`（每 token 每层 2048 B）记账，而物理 packed 只需 512 B + 64 B scales = 576 B → **引擎记账是物理的 3.56×**。BF16 的 4096 B/token/层是准确的，所以相对 BF16 只显示 2×。HP 环（bf16 三层环）不在这份 spec 里，靠剩余空间吸收，因此**从 21.04 GiB 里并未扣除**（证据：INT2 与 BF16 报告的可用内存完全相同 21.04 GiB，说明 profile 阶段未计入 HP 分配）。

### 4.3 真实可服务并发（可复算）

- 现值：306,432 token = 149.6 × 2048（引擎自报 "Maximum concurrency for 2,048 tokens per request: 149.62x"）。
- 物理密度上限（**预留** HP 环）：(21.04 − 4.66) GiB / (576 B × 36) ≈ **0.85M token** = 现值的 **2.77×** = BF16 的 **5.53×**。
- 若不预留 HP（HP 落入剩余空间）：21.04 GiB / (576 × 36) ≈ **1.09M token** = 现值的 **3.56×** = BF16 的 **7.11×**。

### 4.4 最小修复（独立分支已设备验证，2026-10-24 05:35Z）

主线的 `AttentionSpec` 已有一等字段 `state_content_bytes`（`vllm/v1/kv_cache_interface.py:502-507`，专为"packed 布局"设计），因此修复不需要改 vLLM：

1. 在 vllm-ascend 的 spec 收集处（`worker/v1/model_runner.py:7022 get_kv_cache_spec`、`worker/v2/attn_utils.py:200`）对 INT2 层把 spec 重写为 packed 记帐：
   `state_content_bytes = 2 × (head_size // 4) + 4 × dtype_size(model_dtype)`（Qwen3-8B = 64 + 8 = **72 B**）
   → page = 8 × 128 × 72 = **73,728 B/block**（当前 262,144 B）。
2. 在 `worker/worker.py:determine_available_memory`（`worker.py:719-724` 已有 `R150_MAX_KV_GB` 上限的先例）**扣除 HP 环字节**，避免把 4.66 GiB 环挤爆。
3. 注意：vLLM 的 `AttentionBackend.customize_spec` 目前只在 sliding-window 分支被调用（`attention.py:628-650`），full-attention 分支不调，所以必须由 vllm-ascend 自己的 runner 做后处理；`max_memory_usage_bytes` 随之变小，纯 full-attention 模型无影响，混合模型需复查 hybrid planner。

**状态：修复已验证；产品结论仍 OPEN**。主 Agent 于 2026-10-24 05:08–05:35Z 在独立分支
`oscar-int2/capfix-int2-spec`（fork `d1db5264`，本地 `d67b3a0b1`，补丁 sha256
`8289c8bf…`）完成设备实测：在 `attn_utils.get_kv_cache_spec` 发布 packed
`state_content_bytes=72`，并在 worker 预算中扣除 HP 环 4.64 GiB 后：

- `Available KV cache memory: 16.40 GiB`；`NPU KV cache size: **849,280 tokens**`
  （修复前 306,432 = **2.77×**；BF16 153,216 = **5.54×**）；
  物理校验 849,280 × 576 B × 36 = 16.40 GiB；
- 新增 7 条 UT（打包页/边界/HP 几何），上游镜像内全量 `tests/ut/oscar` = **142 passed**；
- blocking 诊断姿态：中层 24/24 + 通用 17/17 = **41/41**；默认异步 1080 tok 仍 12/12 坏
  （负对照，容量修复不改变异步缺陷）。

未合入 `m-port-full-ut`、未开上游 PR；正式（默认异步关闭后）姿态复跑前，"内存收益"
作为产品结论保持 OPEN。详见 `MAIN_SERVICE_VERIFY_20261024.md` §7。

### 4.5 HP 环预留核对（2026-10-24 二轮，CPU 源级；capfix `d67b3a0b1`）

**(a) `_oscar_int2_hp_ring_bytes` 异常时 warning + return 0 —— 有意的 fail-open，确认。**
`worker/worker.py:642-680`：整个几何计算包在 `try/except Exception` 中，失败时
`logger.warning(..., exc_info=True)` 后 **return 0** → `determine_available_memory`
里 `if _hp_bytes:` 不扣减（`worker.py:757-763`），KV 预算与**修复前行为完全一致**。
意图：预留只是记账修正（把环从"隐式吃剩余空间"改为"显式扣减"），任何内省失败
（hf config 形状意外、oscar 配置未加载）都**不应阻断启动**。残余风险如实记：打包页
后池可以吃满整个预算，若该函数静默失败，环稍后分配可能启动期 OOM——这正是旧行为
在 INT2 打包页下的问题。**建议（仅建议，不改码，修复保持独立可追溯）**：失败时回落
保守常量（至少 `layers×2×(mns+1)×(prefix+recent)×nkv×hd×2` 的最小几何）或加一个
fail-closed 开关 env；现有 `exc_info=True` 告警已可被日志监控捕获。

**(b) 几何对照表（worker 预留 vs 实际分配，逐项）**

| 项 | worker 预留（`worker.py:642-680`） | 实际分配（`attention_int2.py:200-207` + `int2/slotstate.py:76-116,188-200`） | 一致 |
|---|---|---|---|
| layers | `hf.num_hidden_layers` | `_tt_hp_bufs` 每层一分配（36 层全走 HP） | ✓ |
| nkv | `hf.num_key_value_heads`（缺省回退 heads） | backend `num_kv_heads`（同源 hf） | ✓ |
| head_dim | `hf.head_dim` or `hidden//heads` | `head_size`（同源） | ✓ |
| dtype 字节 | `get_dtype_size(model_config.dtype)`（bf16=2） | 环 buffer dtype＝调用侧 query/kv dtype（bf16 服务） | ✓ |
| ms | `max(R109_TT_MAX_SEQS 默认4, 4, mns+1)`（`:652`） | `max(_TT_MAX_SEQS 同env同默认, 4, mns+1)`（slotstate:84） | ✓ 同式同默认 |
| R205_HPFIT=1 | `ms = max(4, min(ms, mns+margin 默认8))`（`:653-656`） | `max(4, min(_tt_mseq, mns+margin 默认8))`（slotstate:100-104） | ✓ 同式 |
| mhp | `prefix+recent+(0 if R199_PRREAD else 4)`（`:657-658`） | `_TT_MAX_HP` 同式（attention_int2:206-207） | ✓ |
| 总字节 | `layers×2×ms×mhp×nkv×hd×dsize` | per-layer `2×[ms,mhp,nk,hd]`（slotstate:192-194）×layers | ✓ |

UT 钉住三组合：默认 `36×2×33×1028×8×128×2 = 5,002,297,344`；`R199_PRREAD=1`→1028→1024；
HPFIT 封顶 `36×2×40×1028×8×128×2`（`tests/ut/oscar/test_int2_kv_spec.py:86-107`）。

**两处如实记录的边界（非缺陷）**：
1. `R144_TT_REQID=1` 分支（slotstate:77-78：`_tt_mseq = max_num_seqs`，**无 +1、无下限 4、无 env cap**）worker 公式**不建模**——此时预留恒 ≥ 实际（多预留一行方向，安全但虚高）。该开关默认 0，生产姿势不启用。
2. HPFIT 失败模式不对称：worker 全函数 try→0（不扣减）；slotstate 内层 try→保持大 env cap（多耗 HBM）。成功路径逐字节同式。
3. 数字勘误口径：§4.2 表的 4.66 GiB 用了 `mhp=1028`（PRREAD 关）；canonical 姿势 `R199_PRREAD=1`（`canonical_env.sh:118`）→ `mhp=1024` → **4.64 GiB**，与 capfix 四条 serve 日志的 `reserving 4.64 GiB` 一致（`MAIN_SERVICE_VERIFY` §7 已有同款注记）。

---

## 5. 立场

- 默认异步正确性 **OPEN**：在拿到 0/N 的最小通用修复（优先 device-side 事件等待）之前，不声称服务级正确性关闭。
- 不以外层 `ASCEND_LAUNCH_BLOCKING=1` 的回归替代正式（默认异步）模式验收；该对照只用于**判定时序相关性**，不作归因证据（尤其不据此归因 CANN）。
- 不声称 main 线可生产：main 集成分支只证明"可启动 + UT 135 全绿 + 复现电池"，正确性与性能口径均未建立。
- 不引用交付树（release 线）的精度/性能数字。

---

## 6. 原始证据位置

| 内容 | 路径 |
|---|---|
| 异步电池原始输出 | `/tmp/r218_async_diag/battery_<tag>.txt`、`<tag>.analysis.txt`、`<tag>.status` |
| 异步驱动 | `verify_scripts/async_diag.sh`、`async_bisect{,2,2b,3,4,5}.sh`、`analyze_battery.py` |
| serve 日志 | 容器 `r218-main-verify:/tmp/serve_<tag>.log` |
| UT 日志 | `ut_matrix2_20261024.{log,tsv}`、`ut_matrix1_20261024.{log,tsv}`、`ut_fixup3_20261024.log`；**二轮（归位后，以此为准）**：`verify_scripts/ut_matrix3_20261024.{log,tsv}` |
| UT 驱动 | `verify_scripts/ut_matrix.sh`、`ut_matrix2.sh`、`ut_fixup3.sh`、**`ut_matrix3.sh`**（审计归位+21/22 适配进分支）；归位两提交 `7a23bec98`（06）/`e5e688038`（19） |
| P6 工具 | `verify_scripts/p6_run.sh`（设备腿驱动）、`p6_compare.py`（qin/midcap 对比+纯 torch 中层参考）、`p6_mdiag_diff.py`（R117 哈希流逐记录对比）；工件落地 `/tmp/r218_p6_host/<tag>/` |
| 预览工作树 | `/tmp/r218_ut_bases`（UT 基座）、`/tmp/r218_mpf_ut_3270309`（分支 `prep-depgrp-05-06`） |
| 集成树 | `/home/n00928095/R218_UPSTREAM_WORK/oscar_port_ut_tree`（`m-port-full-ut`） |
| 请求样例 | 容器 `/tmp/req_900x4.json`、`/tmp/x900x4_req.json`、`/tmp/x1601x1_req.json`、`/tmp/x1080x1_req.json`、`/tmp/l4_req.json`、`/tmp/ragged_req.json` |
| 容量修复 | `R218_UPSTREAM_WORK/int2_capacity_fix.patch`（sha256 `8289c8bf…`）、`acceptance/report_eval/capacity_20261024/`（尺寸日志/24-24+17-17 电池/异步负对照/复算 README）、工作树 `R218_UPSTREAM_WORK/capfix_tree` |
| 容量服务日志 | 容器 `r218-main-verify:/tmp/serve_capfix2_blk.log`、`/tmp/serve_capfix17_blk.log` |

复现最小用例：

```bash
# 容器内已就绪的 1080-token 请求文件 /tmp/x1080x1_req.json
flock /tmp/r218_npu7.lock -c \
  'R218_DIAG_FILES=x1080x1 R218_DIAG_REPS=12 bash verify_scripts/async_diag.sh x1080x1 int2exp'
# 对照（仅差一个环境变量）
flock /tmp/r218_npu7.lock -c \
  'R218_DIAG_FILES=x1080x1 R218_DIAG_REPS=12 bash verify_scripts/async_diag.sh x1080x1_blk int2exp ASCEND_LAUNCH_BLOCKING=1'
```

---

## 7. 需要主 Agent 决策 / 与 B 线可能的冲突

1. **是否新开一个 main 线 "platform INT2 dtype registration" 上游单元**（§2 第 1 项）；它依赖 #19577 先合并才有可评审对象。
2. **容量修复是否要做进本轮**：需 main 线设备实测（~10 分钟 serve + 电池）确认 306,432 → ~0.85M 且正确性不变；会改变 `page_size_bytes` 的所有消费者，建议单独一轮、单独分支。
3. **设备/文件占用**：本轮全程 NPU 7 + `/tmp/r218_npu7.lock`，每次 leg 后已停服（NPU 7 回落到 3.4 GB 基线）。若 B 线也要 NPU 7，请沿用同一 flock；若 B 线要求独占，请指示切换。
4. **异步 OPEN 的对外口径**：建议在验收结论中明确写"默认异步存在 INT2 中层退化缺陷（最小复现 1080 token 单请求 5/12），未关闭"，避免被 blocking 绿灯掩盖。

---

## 8. 主 Agent 复核（2026-10-24 04:45Z）

复核方式：不采信子 Agent 自述，逐项对本地 ref / 原始日志 / 容器日志 / 源码与算术重算。

| 复核项 | 结果 |
|---|---|
| fork 分支 ref | 本地 `origin/oscar-int2/prep-unit-*` 17 个 + `prep-depgrp-05-06` + `m-port-full-ut` 全部存在且 SHA 与 §1.3 表逐项一致。事后 `ls-remote` 两次遇 GitHub 网络抖动（超时/HTTP2），改由 **GitHub API** 逐项复核成功：`refs/heads/oscar-int2/prep-unit-*` 17 个 SHA 与表一致、`m-port-full-ut=81295d899`、tag `r218-prep-depgrp-05-06-blocked-on-01-03` → `90340bb70`（commit 对象）。<br>**另发现**：上游 PR #19569 的 head `oscar-int2/m-pr-03` 已推进到 `7ab5c7d36`（2026-10-23T09:58:55Z，父 `2d50a2e26`，仅改 `vllm_ascend/oscar/rotation.py`：声明 `_from_env_signature` 修 mypy attr-defined），超出本报告与旧账本记录的 `8f08f1931`；其余三个 PR head（`cbcc277db`/`cf66c61e1`/`936c58970`）与记录一致。**本会话已复验**：`git fetch` 到 `7ab5c7d36`（线性后代：`8f08f1931`→`2d50a2e26` ruff style→`7ab5c7d36` 一行声明），`pytest --noconftest tests/ut/oscar` = **13 passed**；diff 仅 `rotation.py`/`test_rotation.py`。 |
| UT 数字 | `ut_matrix2_20261024.log/tsv` 与 §1.2 表逐行一致（05=37、06=16p/4f、0709=72、08=43、10=71、12=61、13=45、14=48、15=64、16=77、17=91、18=106、19=123、20=123）；`ut_fixup3_20261024.log`：11=**76 passed**、21=**135 passed**、22=**135 passed**。 |
| 六个修复的代码 | `18d56c698` 的 diff 与 §2 表一致（`attention_v1.py` 两 hunk、`quantcache.py` 跨步写、`bridge.py` CANN 根、`slotstate.py` +1 行、dtype 注册、worker uint8）；commit 带 `Co-Authored-By`。 |
| 01–04 不受影响 | `m-pr-01..04` 的变更文件集合与六个修复文件**无交集**（逐一 `git diff --name-only` 核对）。 |
| 异步原始数据 | `/tmp/r218_async_diag/*.analysis.txt` 与 §3.2 表逐项一致；`x1080_pymid` 11/12、`x1080_wsync` 9/12、`x1080_hpsafe` 8/12、`x1080_qsync0` 12/12、`x900x4` 0/6、`bf16a` 0/24。**§3.1 的 1080+blocking 对照当时缺少原始文件**：主 Agent 于 04:28–04:32Z 在 NPU 7/flock 内补跑 `x1080x1_blk`，结果 **0/12**（`battery_x1080x1_blk.txt`、`x1080x1_blk.analysis.txt`、`x1080x1_blk.status`），该对照现已成立。 |
| 容量对账 | 容器日志复核：INT2 `Available KV cache memory: 21.04 GiB`、`NPU KV cache size: 306,432 tokens`（149.62×2048）；BF16 同预算 `153,216`（74.81×2048）= 恰 2.0000×。`unpadded_page_size_bytes=262,144`（实测 `FullAttentionSpec(128,8,128,128,uint8)`）；packed K/V 65,536 B/block + 4×scale/zero 8,192 B/block；HP 环 `[36,2,33,1028,8,128]` bf16 = 4.66 GiB（`_TT_MAX_HP = 128+896`，ms=max(4,33)）。算术全部复现：5.26+0.66+4.66=10.58 GiB，闲置 10.46 GiB。主线 `state_content_size_bytes` 实测存在（默认 256 B/token，packed 目标 72 B），`state_content_bytes` 为可覆写字段。 |
| "死开关" | `R161_BATCHED_MID` 仅被 `oscar/config.py` 解析后无消费者；`R152_FUSED` 在 `vllm_ascend/` 无读取点。与 §3.2 一致。 |
| 依赖评审方式 | 复核 A 的结论成立：仓库内无 stacked/依赖声明机制；`main2main` 仅 CI 标签。05+ 不开上游 PR 的决定**采纳**。 |

### 决策（主 Agent）

1. **dtype 注册单元**：本轮不新开上游 PR；待 01（#19577）接受后，与重建的 21/22 一起作为"main 胶水"最小差异提交（A 的 §2 映射采纳）。
2. **容量修复**：已完成独立分支设备验证（`oscar-int2/capfix-int2-spec` @ `d1db5264`；
   306,432 → 849,280 tok，41/41 blocking 正确）；**不并入本轮集成分支、不开上游 PR**，
   产品结论保持 OPEN，待默认异步关闭后正式姿态复跑（§4.4）。
3. **设备**：NPU 7 现空闲、锁已释放；本轮主 Agent 仅用 04:28–04:32Z 一段补跑，不触碰其他卡/容器。
4. **对外口径**：采纳 §5 与 §7.4——默认异步 **OPEN**，blocking 仅作时序判别，不归因 CANN，不标生产可用。

## 9. 主 Agent 复核·第 3 波（2026-10-24 15:2xZ，对 A 设备轮与 P2/P3 交付）

复核方式同 §8：独立重算/重载原始数据，不采信自述。

| 复核项 | 结果 |
|---|---|
| §3.5 撤回依据 | 源级核对 `middle_candidate.py`：`:81-82` 进 C++ 准备分支条件、`:542/:504/:530/:563` 三个 launch 入口与报告一致。撤回成立。 |
| p6 证据清点 | `/tmp/r218_p6_host` 106 文件/445MB；p6k 96 个环行张量（r00–r05 × l08–l23）；配对腿 jsonl 齐。 |
| 写侧无罪（独立重算） | 主 Agent 用独立脚本按 mid 重置切 12 rep×828 记录：**src_k/src_v/src_ks/curblk_k 在全部 12 rep、全部 828 记录与 blocking 逐哈希一致**（含 8 个输出坏 rep；量化输入观测的二次确认。⚠第 4 波裁定：src 一致不能宣称"写侧无罪"，存储写越界/内存副作用未排除——写入者审计第 4 波进行中）。 |
| NaN 形态（独立重载） | 直接 `torch.load` p6k 张量：r02_l14 NaN 行 963–1023（61 行/62,464 元素）、r03_l08 883–1023（141 行/144,384）、r05_l23（319,488）；**prefix 行 [0,128) 全部零 NaN**；hk/hv 同数。recent 窗限定＋单调增长证实；×~18 层与 §3.6 结论 5 的 1.09M→5.02M 量级相符。 |
| p6a 口径辨析 | `p6a_mdiag_async.analysis.txt`＝`total=12 bad=8`（1 个轻度 fox + 7 个 `!!!!`），blocking 0/12——**8/12 为输出级判据，成立**。⚠注意：朴素 ring_k/ring_v 全张量哈希对比会得 11/12 分歧（rep2–4 有散布性分歧但输出正确；环内容含槽位布局敏感区，良性漂移会虚增分歧数）。§3.6 结论 1「前 4 rep 全部 828×2 条完全一致」在朴素哈希口径下**仅 rep1（首个）完全一致**——该句按输出级/精细对齐口径理解，引用时以本条为准；不影响结论 2–8 的观察本体；其中"NaN 跨代累积"的**归因**已被第 4 波 §10 推翻（首事件环干净、prefill 自写、步内瞬态）。 |
| 容器 pristine | 容器 `/workspace/oscar-vllm-ascend` HEAD=`81295d899`、`middle_exec.py` md5=`9ea86ce17611`、tracked 无改动；NPU 7 `proc-mem` 无进程、HBM 3455MB 基线（窗口结束后短时 60GB 占用为外部容器负载，非本会话，未触碰）。 |
| P2/P3 fork 产物 | GitHub API 复核 prep-unit-06=`048e14aa3`、19=`d6eaad09c`、21=`db15c9224`、22=`eab326066` 与 A 报告逐项一致（其余 11 个未逐项复验，方法同 §8 已验证）。 |
| P4 对外交互 | #19577 依赖评审一次性询问在（2026-10-24T12:48:52Z 评论）；CANN #6553 open、2 评论、assignee 在，无本会话越权操作。 |

### 决策与遗留（第 3 波）

1. **MAIN_SERVICE_VERIFY §6.2 替换文本已由主 Agent 应用**（更正撤回＋新定位＋口径降级）；r5 包内该文件仍是 05:40 版，包 README 已声明以本文件＋PR_ADVANCE §3.5/§3.6 为准，**不重打包**（r5 已发布并校验；下一版包再同步）。
2. 异步缺陷保持 OPEN：NaN 种子来源两个候选（外部核/工作区越界写 vs 环读侧放大）均未闭合；下一轮建议从环分配邻接关系＋中层 op 工作区越界审计入手（A 建议，主 Agent 采纳）。
3. p6 纯 torch 参考对 MIDCAP2 实操作数的正式跑未做（窗口预算），工具 `p6_compare.py` 就绪——遗留项，非阻塞。
4. capfix 维持独立分支未合入，产品结论 OPEN 不变。

## 10. 子 Agent A · 第 4 波终报（2026-10-25 00:2xZ；T1/T2/T4/T5）

设备窗口（全部 NPU 7，锁日志 `/tmp/r218_npu7.lock.log` 连续 START/END 记录）：
- W6 (23:35–23:45Z): caps 腿 + wtrace 补丁（heredoc 嵌套损坏→p6o 未探针跑成基线 11/12 bad）；END 已记，树还原 9ea86ce1，HBM 3455MB。
- W6b (23:47–23:52Z): docker cp 修法重打 WTRACE2 补丁（md5 870d13bd），p6o2_w2_async **bad=11/12——轻探针不再掩盖故障**（当日未探针基线同为 11/12；p6k 12/12、p6m 0/12 的差异只按"探针同步点数影响竞态"陈述，不作边数断言）。END 已记：双模式 kill 确认（pgrep 空）、HBM 3456MB 回落、树还原 9ea86ce1（bind-mount 双侧 md5）。

### T1 — 三分类（`verify_scripts/p6_t1_ringclass.py` + p6k 12/12 腿）
- **A 有效数据损坏**：NaN 块恒为 [X,1024) 尾接、payload 一律 **0x7FFF**（= f32 0x7FFFFFFF/INT32_MAX 截断成 bf16，非算术 canonical NaN 0x7FC0）、按 rep 每 rep 每层 **+80 行** 增长（963/883/803/723，l16-23 更深，l15 跨界）。**全部落在合法 recent 读集 [128,1024) 内（rep02-05: in=1065/2345/3625/4905，outside=0）——污染确定进入注意力**。
- **B 未使用槽位差异**：未捕获（仅 slot 0 有 dump；mhp=1024 无余量行）。**C 合法重绑**：有限行跨 rep 合法漂移（wave-3 已录性质；prefix 区逐字节同）。
- **MIDCAP2 独立参考**（`p6_compare.py --ref`，修 GQA 映射 + lane-interleaved unpack 后）：async/blk 两模式 kernel vs 纯 torch fp64 参考 cos=0.999927/0.999994 —— **中层算子数值无罪**（撤回类推不适用：按撤回规则②它仍是候选写入者）。

### T2 — 写者审计（定位到机制层，未到指令级；如实）
新证据链（`/tmp/r218_p6_host/p6o2_w2_async/`，分析 `analysis/wtrace2_onset_analysis.txt`，原始 dump `r218_wtrace_dumps/`，9936 条 `r218_wtrace.jsonl`）：
1. **首事件**：rep1/step4/L30，q/kr/vr **同时** 全 0x7FFF（kr==vr==5abbd4b74175、q==9a887382f507）；前 5 个层调用（L25-29，onset01.pt stash）payload 级全健康无局部污染；**该时刻 L8 环全 [1024,8,128] 零 NaN 行——环读/环写在首事件处被排除**。污染经隐层流（前一层 attn/mid/merge/MLP）进入 L30 的 QKV。
2. q 与 kr/vr 无一例单独坏（0 条不对称）→ 一次 hidden 全 0x7FFF 同时打穿三视图；kr_ptr 在步内跨层复用（36 调用仅 3-10 个地址）证实 scratch 复用体制，但同调用内 q/kr/vr/hk 无指针碰撞。
3. 步边界结构：rep1/step4 L30-35 → steps5-15 L31-35 → step16 L20-35 → steps17+ L21-35（平台至 rep8）→ rep8/step7 起 L4-35；step5/L00 即恢复健康（decode 每步从新 token embedding 重算 hidden，NaN 不跨 token 边界留存）→ 每步瞬态级联。
4. 环普查（rep 首捕获步）：r00-r08 全 0（新请求 1082-token prefill 全量覆写环行）；**r09=74 行 [950,1023]、r10=154、r11=234（+80/rep，锚定 1023 最recent侧，层 8/15/16 完全同构）→ 第 9+ rep 的环尾 NaN 是各自 prefill 自己写的**（后期 prompt token hidden 已污），不是跨代残留（rep1-8 的 prefill 都干净覆写过）。
5. 载体层直接证据：MIDCAP2 async 捕获 #2 于 **torch.npu.synchronize() 全量同步后** lse_h 全 −9999（`csrc/oscar/int2_op_launch_lse_fast_r152.cpp:137` 的 `lse.fill_(-9999)` 前置哨兵）、out_h=3.2e36 垃圾，且池载体本身是 `torch.zeros`（`middle_candidate.py:95-99`）→ **哨兵被写入而算子结果写从未落地=一次真实的 missing-write，enqueue 却报成功**（返回元组 (r=GetWorkspaceSize 状态, ws, lr=launch 状态, g_ws_hits)，消费方只看 r）；此事件在健康跑中亦出现（p6m vs p6n：lh 34% 记录 async/blk 不一致而其余逐位同）——即污染种子。
6. 已识别异步路径共享态风险（file:line）：全局缓存工作区 `g_ws` 跨全部层/调用共享（同文件 ~157-165 + warm_ws）；池化输出载体 `_r112_opool` 跨 36 层共享；launcher rc 语义不含 lr。ASCEND_LAUNCH_BLOCKING=1 串行化 launch 是控制腿从不失败的结构性差异（**假设，不作 CANN 归因**）。
**未定位到**：产生 0x7FFFFFFF 位型的具体写入指令/流序违反。**已排除（首事件处）**：环维护写路径、环读路径、同调用指针混叠、局部/尾部污染渐进、跨代环残留（phase-1）。撤回规则①③落实：quantize 散写侧未经首事件检验不称无罪；无 CANN 归因、无独立边数断言。
- 无修复 → T3 未触发（capfix 5.54× 维持不进产品结论）。

### T4 — HP 环预留 fail-safe（capfix 分支，未合入）
`worker.py _oscar_int2_hp_ring_bytes` 异常路径 warning+return 0（fail-open）改为**保守上界回退**（ms 保留 +1 且忽略 HPFIT 收缩；mhp 恒保 +4；prefix/recent 读 R109_TT_* 同 config.py 缺省）＋ 几何不可推导时 RuntimeError fail-closed。提交 `d1ebaa718`；容器内 UT 首跑暴露测试假体缺绑定方法 → `db6398286`（测试假体挂 MethodType）。**验证：tests/ut/oscar 全目录 --noconftest 146 passed（含 4 条新 fail-safe 用例）**（容器 /usr/local/python3.12.13 同时有 acl+numba；注意 PYTHONPATH 必须前缀拼接而非整体替换，否则丢 CANN site-packages）。分支头现为 db6398286。

### T5 — 上游 PR 复查（2026-10-24 晚）
四 PR（#19577@9ce844dc5 / #19568@29291d83e / #19569@ece725142 / #19570@9f9f37244）均 draft/open、head 无变化、无新外部评审意见、checks 6 通过（ci-gate 为 maintainer 标签门）→ 无可处理反馈；LEDGER §七已更新三态列（上游已提交×4、准备好=m-port-full-ut@81295d899+17 prep-unit+capfix、#19552 closed）。未重复 dependency-review 提问（10-24T12:48Z 已问）；05+ 新上游 PR 维持等待 maintainer 回复。

## 11. 第 5 波收尾（2026-10-25，主 Agent）

### 上游 PR — 四 PR 全部 ready for review（无未完成作者事项）
- **#19577**（01，**main 基**；2026-10-25 复核远端 baseRefName=main，release 基首投 #19552 已取代关闭）：ready（0 未决线程；此前 DCO/标题已处理）。
- **#19568**（02, main 基）：ready；2 线程已回复＋resolve；标题改
  `[Attention][Feature] oscar: add the INT2 KV encoder (per-token-head affine, pure Torch) [2/22]`。
- **#19569**（03, main 基）：ready；2 线程已回复＋resolve（引用既有修复提交）。
- **#19570**（04, main 基，本轮评审修复）：**新提交 `314f9186e`**（fork 分支 `oscar-int2/m-pr-04`，
  9f9f37244→314f9186e）落实 20 线程全部整改：
  ① 全 raw pybind 入口补 `DeviceGuard`＋`NPUStreamGuard`（r152：launch_lse_fast/warm_ws/
  middle_prep 全变体/middle_op_v3/scatter_int2/r144_read_counter；r98：launch_lse；含
  oscar_middle_prep 专项缺 NPUStreamGuard 点）；
  ② clip_idx 钳位 [1,D]；③ mid_len from_blob→torch::tensor；④ std::system(mkdir)×2→
  std::filesystem::create_directories（error_code 出参，注入面清零）；⑤ g_ws/wsh
  torch::empty try-catch（析构 acl 句柄后 rethrow，含 middle_prep 同型点）。
  验证：双环境 cpp_extension 编译＋import 通过（torch_npu 2.10.0.post7 nightly 容器 +
  CANN 9.0.0 runner）；六路 oscar_quant_kv vs 纯 Torch 逐位复验 all_bit_equal=true
  （NPU 7 under flock，evidence ts 2026-10-25T01:45:24Z）。20 线程全部回复＋resolve。
- 状态：四 PR 均 `OPEN + ready`；checks 通过（ci-gate 为 maintainer 标签门）。剩余为维护者
  评审（外部等待）。

### B 线产物验收＋发布（v4）
- B 产物核验：`SHA256SUMS` 233/233 OK；`p6_compare.py` 修复版 sha
  `fe2fce54440fb46f7ad99698d5f2b53177a7e46bc0691ffe756bcd7b36f4b6ba`（＝主 Agent 实跑版）；
  `ref_reproduction_20261025.txt`（命令/退出码/完整输出，4 捕获 CPU 复现全 0）＋
  `layout_sweep_20261025.py`；`PACKED_MANIFEST`/`RAW_MANIFEST` 拆分。
- **P6 v4 包发布**：`r218_p6_async_evidence_20261025r2.tar.gz`
  （sha256 `d986fdef9825d9ebeda64d12a786c2ee1f1b615acafa218945622278d9d35135`，74 内容文件；
  v3 的 71 项中替换缺陷版脚本，＋ref_reproduction/layout_sweep/RAW_MANIFEST/README v4 版本块；
  解包往返校验 73/73 OK）。**v3（`92ac574b…`）SUPERSEDED**。文章材料入口
  `ARTICLE_MATERIALS_ENTRY.md` §5/§8/§9 已同步 v4＋四 PR ready 状态。

## 12. 上游提交完整台账（2026-10-25 第 5 波主 Agent 终版）

### 已提交（6 个正式上游 PR，全部 main 基）

| 单元 | PR | head | 依赖声明 | 状态 |
|---|---|---|---|---|
| 01 配置面 | [#19577](https://github.com/vllm-project/vllm-ascend/pull/19577) | `9ce844dc5` | ∅ | ready；DCO/pre-commit/main/cpu-ut 绿 |
| 02 KV 编码器 | [#19568](https://github.com/vllm-project/vllm-ascend/pull/19568) | `29291d83e` | ∅ | ready；同上 |
| 03 旋转加载器 | [#19569](https://github.com/vllm-project/vllm-ascend/pull/19569) | `ece725142` | ∅（config 12 行归 01） | ready；同上 |
| 04 vendored launchers | [#19570](https://github.com/vllm-project/vllm-ascend/pull/19570) | `96ef95c9a` | ∅（运行期 cpp_extension 构建） | ready；加固 314f9186e＋**异步边界修复**（§3.7 根因定谳，三分对照 11/12→0/12，60/60+sweep 20/20+UT139+capfix 849,280tok 复验）全 CI 绿 |
| 05 helpers 重定位 | [#19728](https://github.com/vllm-project/vllm-ascend/pull/19728) | `7f26e73ec` | #19577+#19569（分支含依赖内容；正文附增量 diff 链接） | open；测试 37 passed（含依赖单元），ruff/mypy 清洁 |
| 06 ctx import hub | [#19729](https://github.com/vllm-project/vllm-ascend/pull/19729) | `93ba08606` | #19577 | open；测试 20 passed；main 适配（attention_cp 元数据、剔除 release 专属 kvcomp/flashcomm2 再导出） |

注：#19552（01 的 release 基首投）已由 #19577（main 基）取代关闭。ci-gate fail＝维护者标签门（非代码失败），四 ready PR 同。

### 未提交（逐项：依赖对象 / 阻塞依据 / 解除条件 / 已备内容）

| 单元 | 依赖 | 阻塞依据 | 解除条件 | 已备 |
|---|---|---|---|---|
| 07 slotstate＋09 bmupdate | 1,3,5,6 | 依赖 5/6（#19728/29 刚投，未合入）；两者 import 互指不可分，须同一 PR | 05/06 任一被接受或维护者确认叠堆评审；即合入后 rebase 到 main | v4 链 `4d53a162`(+1355)/`007705a9`(+1970)；m-port 树适配版（slotstate 8 行适配） |
| 08 bmresolve | 1,3,5 | 同上（无 ctx 依赖） | 同上 | `6a61b97f`(+237)，port 树逐字节同 |
| 10 ring mixin＋12 quantcache | 1,2,3,5,6 | 10 运行时依赖 12，须同 PR；12 引 02 编码器（已投） | 同上 | `2bc31f88`(+798)/`fc6a77f3`(+588)；quantcache 22 行适配 |
| 11 staging / 13 bridge / 14 middlecand / 15 middlebatched / 16 middleexec+OGA / 17 decode / 18 prefill | 1,3,5,6（17 为 1,6） | 同上；均纯增量＋自有测试绿（11=4/13 无自有测试乘 19 审计/14=3/15=2/16=3/17=2/18=2） | 同上 | v4 链各 commit＋port 树逐字节同（13 bridge 33 行适配） |
| 19 后端组装 | 1,2,3,5..18 | import 全部 12 个 mixin；差异会重复整个系列 | 05-18 合入 | `9ebddc05`(+1134) |
| 20 v1 接线 | 19＋main 移植 | v4 版是 release 整文件重写（main 无意义）；适配版 2ee7126a1 | 19 合入 | m-port-full-ut 内适配版（+326） |
| 21 kv_int2 注册 | 19＋main 移植 | 惰性挂 19；modelslim 已随上游 #14030 移 quantization/configs/ | 19 合入 | 5dd2239af（+321） |
| 22 worker 生命周期＋池帽 | 21＋main 移植 | model_runner_v1 在 main 不存在（#18863 移 worker/v1/）；接线实测 :1111/:6551/:6698 | 21 合入 | 7b7eafa92（+552） |
| capfix 容量记账 | m-port-full-ut＋01 | worker.py:663 `from vllm_ascend.oscar.config import get_oscar_config`（=01）；改动落点在 22 移植引入的 INT2 块内 | 22 合入＋#19577 合入；且异步修复已进（#19570 96ef95c9a）——正式姿态验证已完成（p9：849,280 tok＝BF16 5.54×，不升格产品结论） | fork `oscar-int2/capfix-int2-spec@db6398286`（146 passed）；patch `8289c8bf…` |

**叠堆评审机制现状**：2026-10-24 12:48Z 已在维护者线程询问依赖评审方式，无人工回复（仅 bots）。05/06 已按「依赖声明＋增量 diff 链接＋自含可测 head」形式投递，作为该机制的事实探针；07-18 视其反响随后续波投递（配方已验证：port 树适配版文件＋m-pr 叠基＋ruff 0.14/mypy --check-untyped-defs/pytest --noconftest 三清＋gh api blob 推送）。

### GitCode 镜像
22 单元 v4 链 Draft 仍在 GitCode（gcw_S4YvZ8l6/vllm-ascend MR 1-22），与上表一一对应，作为内部评审镜像保留。
