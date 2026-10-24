# 上游 PR 状态（2026-10-23 10:30Z）

权威 22 项台账见 `PR_SUBMISSION_LEDGER.md`（GitCode 审查栈 `[WIP]` PR 1..22）与
`pr_texts/BRANCHES.md`。**本文件只记录正式上游（GitHub vllm-project/vllm-ascend）的 4 项**
及其检查/评审实况。客户 e2e PR 仍预留（`RESERVED_FOR_CUSTOMER_PR22.md`），不在上游提交。

## 一、四项上游 PR 实况

| # | 标题（缩写） | head → base | head SHA | 提交 | pre-commit | cpu-ut | main | DCO | ci-gate | review |
|---|---|---|---|---|---|---|---|---|---|---|
| [19577](https://github.com/vllm-project/vllm-ascend/pull/19577) | INT2 配置面 / fail-closed / 路径解析（01，取代 #19552） | `oscar-int2/m-pr-01` → `main` | `cbcc277db` | 3 | ✅ | ✅ | ✅ | ❌ | ❌ | Gemini COMMENTED |
| [19568](https://github.com/vllm-project/vllm-ascend/pull/19568) | INT2 KV 编码器（纯 Torch，02） | `oscar-int2/m-pr-02` → `main` | `cf66c61e1` | 4 | ✅ | ✅ | ✅ | ❌ | ❌ | Gemini COMMENTED |
| [19569](https://github.com/vllm-project/vllm-ascend/pull/19569) | 旋转资产加载器（03） | `oscar-int2/m-pr-03` → `main` | `7ab5c7d36` | 5 | ✅ | ✅（重跑 11m38s） | ✅ | ❌ | ❌（待维护者标签） | Gemini COMMENTED |
| [19570](https://github.com/vllm-project/vllm-ascend/pull/19570) | launcher 扩展源码 + 构建取证（04） | `oscar-int2/m-pr-04` → `main` | `936c58970` | 3 | ✅ | ✅ | ✅ | ❌ | ❌ | Gemini COMMENTED ×2 |

全部 **Draft**、base=`main`、head 在 `nqz1997/vllm-ascend`（fork，`maintainerCanModify=true`）。

**ci-gate 失败的唯一剩余原因**（已逐条核对日志）：不是代码问题，而是
`This PR touches source code … precision/full tests are required` → 需**维护者**加
`ready-precise`（推荐）/ `ready-all` / `main2main` 之一，工作流自动重跑。

**DCO 失败**：4 个 PR 的提交均无 `Signed-off-by`（作者身份为 gitcode noreply）。
按既定纪律**不代签**；需本人一次动作（见 §四）。

## 二、本次会话对上游的改动（全部为 CI 修复，无功能改动）

`#19569` 追加 2 个提交（已推送，head `8f08f1931 → 7ab5c7d36`）：

| 提交 | 内容 | 触发原因 |
|---|---|---|
| `2d50a2e26` | `test_rotation.py`：循环变量 `l → li`（E741）；`rotation.py`：日志改惰性 `%` 格式化（G004 ×3）；两文件 `ruff format` | pre-commit 首轮红（ruff check / ruff format） |
| `7ab5c7d36` | 类属性声明 `_from_env_signature: tuple \| None = None` | 第二轮 pre-commit 红：mypy `attr-defined` ×2 |

验证：`ruff check` + `ruff format --check` 全绿（本地 ruff 0.14.0 + 仓库配置）；
`rotation.py` 直调功能验证通过（加载 shape 正确、缺层 fail-closed 报 `ValueError`、日志正常）。
**本地 pytest 未能运行**：本机 vllm 缺失 `vllm.third_party.flash_linear_attention`（旧 core），
→ 由 CI 的 cpu-ut 兜底（该 PR 前两轮 cpu-ut 均为绿）。

注：`/home/n00928095/R218_UPSTREAM_WORK/repo` 里有一份 08:14 留下的**同款未提交修改**
（分支 `m-pr-03-r`，落后于 origin）。已确认早于本次会话、非并行会话；**未动**，以 origin 为准。

## 三、依赖与待推进顺序

* 逻辑贡献 22 项；实际上游 PR **4 个**（01–04），其余 18 项为 GitCode 审查栈。
* 上游依赖：02/03/04 的 base 独立为 `main`（各自最小差异），但**运行时**依赖 01（配置面/路径）。
  05 起（含 07↔09 互环、12 quantcache 被 16/17/18 运行时调用、14→13 懒加载）见
  `DEPENDENCY_MATRIX.md` v2 / `acceptance/runtime_deps_int2.json`（AST self 边 62 条）。
* **05/06 的明确挂起条件（本次更正上版"可独立提交"的措辞）**：代码已备、UT 已过，但运行时依赖
  **05 → {#19577(01), #19569(03)}**、**06 → {#19577(01)}**（`helpers.py` import diag/rotation，`ctx.py` 为
  显式 import hub）。三者上游**均未合入**，若现在以 `main` 为基提交，05/06 在运行时必然失败——这正是
  "必须等未来 PR 修复的半成品"，故**不投**。解除条件二选一并写明依赖：
  (a) #19577 合入后以 `main` 为基提交（首选，无级联重基）；
  (b) 若维护者倾向提前评审，则以 #19577 的分支为 base 堆叠提交，PR 描述显式标注依赖。
  当前默认 (a)。其余项同理按 `DEPENDENCY_MATRIX.md` 逐层推进；**不为凑数拆空壳**。
* 07↔09 已裁定为不可分单元（`_r196_idfill_memo` 反向边），将作为单一 PR。

## 四、必须由本人/维护者处理（其余已自主完成）

1. **DCO**（本人）：确认署名与邮箱后，对 4 个分支末尾提交加签并强推，例如
   `git commit --amend -s --no-edit && git push --force-with-lease`；
   若选择保留 gitcode noreply 身份，需确认 GitHub DCO 接受该 `Signed-off-by`。
2. **ready-precise 标签**（维护者）：任一 PR 加上即触发精度/全量 CI。
3. **CANN 线**：Issue #6553 已提交；SIG/CLA 与功能 PR 待仓核实后推进（见 `cann/`）。
4. **客户 e2e PR**：保持预留，不创建。

## 五、main 移植（m-port-full）实况

* 分支 `oscar-int2/m-port-full` @ `7b7eafa92`（`/home/n00928095/R218_UPSTREAM_WORK/repo`）：
  main 基 `dde85f6b8` + 01..04（main 适配）+ 05..19（零冲突）+ 20/21/22 移植。
* **UT（2026-10-23 14:20Z，隔离 venv）**：15 个 `tests/ut/oscar/test_int2_*.py` 全部通过，
  **98 passed / 0 failed**（`--noconftest`，见下）。运行时：`torch 2.13.0+cpu` +
  `torch_npu 2.13.0` + `vLLM 0.31.0` + `transformers 5.17.0` + `pytest 9.1.1`；
  `torch.npu.is_available()=True`、8 卡可见、`torch.ones(2, device='npu:6')` 实测可分配。
* **为跑通 UT 补的两处 main 适配**（fork 分支内容，**不属于四个上游 PR**）：
  1. CP 元数据 dataclass 在 main 已由 `context_parallel/common_cp.py` 迁到
     `context_parallel/attention_cp.py`；`attention/int2/ctx.py` 与
     `attention/attention_int2.py` 的 import 随之改指 `attention_cp`。
  2. main 不存在 release 线的 `attention/kvcomp_attn/`、`worker/kvcomp_utils.py`、
     `ops/flashcomm2_oshard_manager.py` 与 `attention.utils.enable_cp`；ctx 导入枢纽与
     `attention_int2.py` 去掉这些**未被任何调用点使用**的 re-export（不是删功能，
     main 本就无该功能；eager 姿态未移植的 release 专属 kvcomp 本就是记录在案的差异）。
  补丁：`/home/n00928095/R218_UPSTREAM_WORK/main_port_ut_adaptation.patch`
  （sha256 `24b0c750fc503f2f2889c252f97b4a704f271aa97dcbbc428bbb53f07a9643f1`）。
  **已推 fork 验证分支**：`nqz1997/vllm-ascend` 的 `oscar-int2/m-port-full-ut` @ `268b8ff16`
  （= `m-port-full` 7b7eafa92 + 适配提交）；**未开 PR**（fork 内审查不计上游）。
* **`--noconftest` 的原因（环境限制，非代码缺陷）**：仓库 conftest 会 import
  `vllm_ascend.patch`，其 `ops/gdn.py` 需要 `fla_npu`（独立发行、带 AscendC 编译产物）。
  本机 venv 无该包，CI 镜像自带。UT 文件本身不依赖 conftest fixture。
* **口径警告**：该分支 `requirements.txt` 钉 `torch==2.10.0 / torch-npu==2.10.0.post4`，
  但已发布 vLLM 0.30–0.32 wheel 的元数据要求 `torch==2.13`；本机实际可满足的唯一配对是
  **torch 2.13 + torch_npu 2.13**。vLLM 0.31.0 本身是四个 PR 的 cpu-ut 矩阵版本之一
  （`cpu-ut (vllm@v0.31.0)` 全绿），API 面是受支持组合；但**运行时安装的 torch 与分支
  requirements 的钉住版本不同**，故这是"API 对齐、二进制栈近似"的复现，不等于上游 CI。
  PyPI aarch64 的 torch 2.13 是 CUDA 链接版（缺 `libcublasLt` 无法 import），
  实际用的是 `download.pytorch.org` 的 `2.13.0+cpu`。
* **服务级验证未完成（已实试构建，遇环境版本阻塞）**（不以"UT 绿"替代）：
  `pip install -e . --no-build-isolation --no-deps`（`SOC_VERSION=ascend910b1`，worktree 内隔离）
  在 `csrc/build_aclnn.sh` 阶段失败，根因是**本机 CANN 9.0.0 头文件缺少源码使用的日志宏**
  （`OP_LOGE_FOR_INVALID_SHAPE_WITH_REASON` 等；在 `cann`、`cann-9.0.0`、
  `ascend-toolkit/latest` 三处 `pkg_inc` 中 grep 均为 0 次），失败点
  `csrc/attention/quant_lightning_indexer_v2/op_host/*_tiling.cpp`。这是 CANN 版本不匹配，
  不是权限或磁盘问题。
  另有两处版本约束叠加：① 顶层 `CMakeLists.txt` 硬性要求 `torch 2.10.0`（与分支
  `requirements.txt` 的 `torch==2.10.0 / torch-npu==2.10.0.post4` 一致），而已发布
  vLLM 0.30–0.32 wheel 要求 `torch==2.13`；② `COMPILE_CUSTOM_KERNELS=0` 会同时跳过
  aclnn 与 C++ 扩展（同一开关），实测该模式下 `vllm_ascend._C` 不存在，不能用于服务。
  → **明确外部阻塞**：匹配 main 的镜像（源码构建 vllm + torch 2.10 + 新版 CANN）才能做
  NPU 服务回归；本机无此栈，也未在 1 vCPU 上尝试源码构建 vLLM。服务回归结果出炉前
  **不得引用**已测交付树的精度/性能数字。
* 已测交付树（v4 + 冻结内核 c8a8d47a）的精度/性能结论仍只归属该树
  （见 `CODE_VS_TESTED_MAPPING.md`）。


## 六、2026-10-23 12:30Z 巡检快照（只读核对，无新提交）

| PR | head SHAs | pre-commit | cpu-ut（两矩阵） | main | DCO | ci-gate |
|---|---|---|---|---|---|---|
| #19577 | cbcc277db | pass 3m51s | pass 41m29s / 36m26s | pass 1m04s | fail | fail |
| #19568 | cf66c61e1 | pass 6m11s | pass 13m23s / 13m14s | pass 1m26s | fail | fail |
| #19569 | 7ab5c7d36 | pass 4m02s | **pass 11m38s / 13m14s**（上轮"重跑中"已闭合） | pass 0m47s | fail | fail |
| #19570 | 936c58970 | pass 8m43s | pass 13m15s / 9m49s | pass 0m56s | fail | fail |

- 四项保持 Draft、base=`main`、head=`nqz1997/vllm-ascend`；`mergeable=UNKNOWN` 是 GitHub 对
  Draft 的常态返回，不是冲突证据。
- ci-gate 失败原因与上轮一致：仅差维护者加 `ready-precise` / `ready-all` / `main2main` 之一；
  日志中无代码/测试失败。
- DCO 仍为 4/4 失败（提交无 `Signed-off-by`）。**不由本会话代签**；等本人一次动作。
- 评审：四项均只有 Gemini Code Assist 的 COMMENTED 与各 PR 下的逐条回应（采纳/拒绝+理由），
  无人类 reviewer 意见、无 unresolved thread。fork 内 22 个 GitCode Draft 不计正式上游。
- 后续依赖组 05/06：代码与 UT 在 `m-port-full` 上就绪；按 `DEPENDENCY_MATRIX.md`
  等 #19577/#19569 合入后以 `main` 为基提交（或经维护者同意后以 #19577 分支为 base 显式
  标注依赖）。**不在 fork 分支上开正式上游 PR**。
- 14:35Z 复核：四个 PR 状态与上表一致（`pre-commit`/`main`/两组 `cpu-ut` 全 SUCCESS；
  `DCO` ACTION_REQUIRED；`ci-gate` FAILURE 仅缺维护者 `ready-*` 标签）。cpu-ut 的两个矩阵
  为 `vllm@v0.31.0` 与 `vllm@<main 提交>`，与本机采用的 vLLM 0.31.0 对应。

### 依赖组 05/06 预演（2026-10-23 12:45Z，local only，未推上游）

- 预演分支：`prep-depgrp-05-06`（本地 worktree），基 = `m-pr-01@cbcc277db` + `m-pr-03@7ab5c7d36`。
- 合并 01+03 时出现 **`vllm_ascend/oscar/__init__.py` add/add 冲突**（两个独立 PR 都加了最小
  package marker 以过 python-init 钩子）。解决：保留 #19577 的完整 package 注释，丢弃 #19569
  的 marker（其注释本就写明 "PR 1 owns the full package surface"）。
- 在此基上 `git cherry-pick -x aad3cb760 facebef84`（05 helpers、06 ctx hub）**零冲突**；
  预演 tip `f4d2f2803`。测试仍受旧 vLLM core 阻塞（`is_weak_contiguous`），等匹配运行时。
- 结论：05/06 的**代码面**已就绪，合并路径明确；正式提交仍等 #19577/#19569 合入后以
  `main` 为基，**不在 fork 分支开正式 PR**。

## 七、main 匹配运行时与服务验证（2026-10-24 00:15Z 更新）

**环境改为上游验证组合（官方 nightly 镜像），不再使用本机 CANN 9.0.0 + 自建 venv 的组合**
（后者构建失败：`build_aclnn.sh` 缺 `OP_LOGE_FOR_*_WITH_REASON` 宏，见 §五）。

| 项 | 值 |
|---|---|
| 镜像 | `swr.cn-north-12.myhuaweicloud.com/atlas_inference/vllm-ascend:nightly-ci-main-a2-openeuler` |
| digest | `sha256:8eaf0b4fd652097a6db123bda845abdaf6d1f3c3e3c68429b470f677c5920f8b` |
| CANN / torch / torch_npu | 9.2.0 / 2.10.0+cpu / 2.10.0.post7 |
| vLLM | 0.31.0，源码 @ `db9527a4`（tag `v0.31.0`） |
| 容器 | `r218-main-verify`（驱动/dcmi 只读挂载，NPU 7，宿主未改动） |

- **扩展构建**：`pip install -e . --no-build-isolation --no-deps` → EXIT 0，
  `vllm_ascend_C.cpython-312-aarch64-linux-gnu.so` 产出；`import vllm` 成功。
- **隔离 UT**：`--noconftest tests/ut/oscar/test_int2_*.py` → 15 文件 / 98 passed；
  6 文件运行时适配提交 `18d56c698` 后复跑仍 98 passed。
- **BF16 冒烟**：同容器同参数启动，KV cache 153,216 tokens；greedy 输出正确。
- **INT2 服务**：vendor 链 = `oscar_r144_v133c_grp + R133V + R116V + R106V`，候选内核
  `.o` md5 `c8a8d47a…`（交付冻结门），launcher 扩展 `r113.orch.v9+r145v3`；
  KV cache 306,560 tokens（同 GMU 0.60 下 BF16 的 2.00×）。
  **`ASCEND_LAUNCH_BLOCKING=1` 下 41/41 请求无损坏**（单请求/批量 2-8/ragged/短 middle/
  长度截止/前缀复用）；默认异步发射下 **18/24 损坏**，与 2026-10-20 A1 判定的
  CANN aclnn 发射层竞态同签名（0/50 vs 7/49），不归因于 INT2 算术。
- **结论口径**：main 服务为 **BLOCKED（环境竞态）**，不能标生产可用；不得引用交付树
  精度/性能数字。完整记录见
  `acceptance/report_eval/MAIN_SERVICE_VERIFY_20261024.md`。
- 运行时适配提交：`oscar-int2/m-port-full-ut` @ **`18d56c698`**（`268b8ff16` 之上 6 文件）；
  **已推 GitHub fork 并核对远端 blob 一致**（GitCode 归档仓仍无写凭据，与本分支无关）；
  导出补丁 `R218_UPSTREAM_WORK/main_port_runtime_fixes.patch`
  （sha256 `c227321dc4a7ff10d55d5daad5f9d470971c4ab8fd3a59c20cecaa29b6481da6`）。

## 八、2026-10-24 00:20Z 上游 PR 实况快照（只读）

四个 PR 仍为 Draft；除下列两项外全部检查为 SUCCESS（pre-commit、main、两组 cpu-ut）：

| # | ci-gate | DCO | 标签 |
|---|---|---|---|
| #19577 / #19568 / #19569 / #19570 | FAILURE（需维护者 `ready-*`） | ACTION_REQUIRED（需本人签名） | `module:tests`（#19570 为 `documentation`） |

已在 2026-10-23 各 PR 各留**一条**汇总评论（测试结果 + 请求评审/标签），不重复打扰。
