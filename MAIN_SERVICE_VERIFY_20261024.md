# main 服务验证记录（2026-10-24，NPU 7）

对象：`nqz1997/vllm-ascend` 分支 `oscar-int2/m-port-full-ut`（main 基 `dde85f6b8`）。
本文件只记录 **main 移植版** 的服务级验证；不引用交付树（release 基）的精度/性能数字。

## 1. 环境（上游验证组合，宿主未改动）

| 项 | 值 |
|---|---|
| 镜像 | `swr.cn-north-12.myhuaweicloud.com/atlas_inference/vllm-ascend:nightly-ci-main-a2-openeuler` |
| 镜像 digest | `sha256:8eaf0b4fd652097a6db123bda845abdaf6d1f3c3e3c68429b470f677c5920f8b`（image id `b08f059e942e`） |
| CANN | 9.2.0（镜像自带 `/usr/local/Ascend/cann-9.2.0`） |
| torch / torch_npu | 2.10.0+cpu / 2.10.0.post7 |
| vLLM | 0.31.0，源码 `/vllm-workspace/vllm` @ `db9527a4`（tag `v0.31.0`） |
| Python | 3.12.13 |
| 容器 | `r218-main-verify`：`--privileged`，`-v /usr/local/Ascend/driver:ro`、`-v /usr/local/dcmi:ro`、`-v /home`、`-v <worktree>:/workspace/oscar-vllm-ascend`；`ASCEND_RT_VISIBLE_DEVICES=7` |
| 设备 | NPU 7：启动前核实无进程（`npu-smi` 空）；未触碰其他用户负载 |
| 宿主 | 未修改驱动、系统 OPP、CANN；未伪造宏、未删除版本校验 |

## 2. 构建与 import

- `pip install -e . --no-build-isolation --no-deps` → **EXIT 0**；
  产物 `vllm_ascend_C.cpython-312-aarch64-linux-gnu.so`（torch 2.10.0 + CANN 9.2 编成）。
- `import vllm` 触发 vllm_ascend 平台插件加载成功；`vllm_ascend.attention.int2.ctx`
  `__all__` 46 项（import 适配后的期望值）。
- 隔离 UT（host venv_main，CPU）：`pytest --noconftest tests/ut/oscar/test_int2_*.py`
  → **15 文件 / 98 passed**；6 文件运行时适配提交 `18d56c698` 后复跑仍 **98 passed**。
  口径：这是隔离 UT，不等于全仓测试。

## 3. BF16 冒烟（同镜像、同容器、同参数）

命令：`vllm serve Qwen3-8B --max-model-len 2048 --max-num-seqs 32 --gpu-memory-utilization 0.60
--trust-remote-code --enforce-eager`（默认 BF16 KV）。

- 启动成功；`NPU KV cache size: 153,216 tokens`，`Maximum concurrency ... 74.81x`。
- greedy `"The capital of France is"` → `" Paris. The capital of Italy is Rome. The capital of Germany is Berlin."`

## 4. INT2 服务

启动脚本：`R218_UPSTREAM_WORK/verify_scripts/serve_int2.sh`（+ `canonical_env.sh`）。
姿态与交付线生产口径一致：

- vendor 链 `oscar_r144_v133c_grp : oscar_r133_v1 : custom_opp_r116v2 : oscar_r106_candidate`；
  候选内核 `.o` md5 **`c8a8d47a63be7ad79abce43de005f238`**（= 交付冻结门）。
- 运行时扩展：`[R112-FAST] Extension loaded: r113.orch.v9+r145v3`（launcher
  `int2_op_launch_lse_fast_r152.cpp`，与交付树逐字节同）＋ `[R108-LSE] r98.lse.v1`。
- 源码身份横幅：`[R218ID] file=.../attention_v1.py sha=704cf4e0c3a7fa5a`。
- `NPU KV cache size: 306,560 tokens`；同 `gpu-memory-utilization=0.60` 下为 BF16 的
  **2.00×**（容量观察，非验收指标）。

### 4.1 功能回归（`ASCEND_LAUNCH_BLOCKING=1`，串行化发射）

| 场景 | 结果 |
|---|---|
| 单请求（5 tok，无 middle） | PASS：`" Paris. The capital of Italy is Rome. The capital of Germany is Berlin."` |
| 批量 2/3/4/8（同一短提示） | PASS |
| ragged：6 / 121 / 1001 / 1601 tok 同批 | PASS |
| 短 middle 带：1601 tok（middle ≈ 577 tok） | PASS |
| 批量长上下文：2×1601、4×1601、短+长混合 | PASS |
| 长度截止（`finish_reason="length"`） | PASS |
| 前缀复用：1601 tok 同请求连发两次 | PASS（两次输出逐字相同；日志 `Prefix cache hit rate: 85.7%`） |
| 全量电池（17 种请求形态） | **17/17 无损坏** |
| 中段重负载电池 6×4 请求 | **24/24 无损坏** |
| 合计（BLOCKING=1） | **41/41 无损坏** |

### 4.2 已知缺陷：异步发射下的间歇空注意力（环境级）

同一电池在 `ASCEND_LAUNCH_BLOCKING=0`（默认异步发射）下：**18/24 请求出现损坏输出**
（表现为 `!!!!!!` 类退化文本，按请求随机落行）；`=1` 下 **0/24**（全量电池另 17/17）。
另在异步模式下观察到一次冷启动形态：短请求（5 tok）之后的首个 middle 请求（1601 tok）
单行损坏，下一次同请求即自愈。该签名与 2026-10-20 A1 判定一致（当时 0/50 vs 7/49）：
**CANN aclnn 发射层竞态**，不是 INT2 算子算术错误。本次未在 main 树内修复该环境竞态；
生产化需等待 CANN 侧修复，或以串行化/同步发射作为临时手段（牺牲并发性能）。

> **2026-10-24 04:40Z 更正**：本节与 §5 的"CANN aclnn 发射层竞态"归因**已撤回**。
> 后续二分（§6）显示 BF16 同电池 0/24、无 INT2 中层 0/6、Python 中层路径仍 11/12，
> 故障与本树 INT2 中层读路径绑定；blocking 只能证明时序相关，不能定责 CANN。
> 当前状态 **OPEN**。

### 4.3 运行时适配（已提交）

`oscar-int2/m-port-full-ut` @ **`18d56c698`**（在 `268b8ff16` 之上）：

| 文件 | 适配 |
|---|---|
| `patch/platform/patch_kv_cache_dtype.py` | 接受 `int2_per_token_head`；注册 packed uint8 存储 dtype |
| `worker/worker.py` | INT2 cache dtype → `torch.uint8` |
| `attention/attention_v1.py` | 去掉 release-only kvcomp/hamming 分支；INT2 豁免静态量化配方检查 |
| `attention/int2/quantcache.py` | packed KV 走 (block, offset) 索引写，适配 V2 runner 的块跨距页 |
| `attention/int2/bridge.py` | CANN 根从 `ASCEND_HOME_PATH`/`ASCEND_TOOLKIT_HOME` 解析 |
| `attention/int2/slotstate.py` | b 键 HP 池尺寸覆盖引擎最大批宽 + V2 padding 行 |

补丁导出：`R218_UPSTREAM_WORK/main_port_runtime_fixes.patch`
（sha256 `c227321dc4a7ff10d55d5daad5f9d470971c4ab8fd3a59c20cecaa29b6481da6`）。
分支已推 GitHub fork `nqz1997/vllm-ascend` `oscar-int2/m-port-full-ut` @ `18d56c698`，
远端 blob 与本地一致（`slotstate.py` blob `24ed168d…`）。

## 5. 边界与结论

- **PASS（BLOCKING=1 诊断口径）**：单请求、批量、ragged、短 middle、长度截止、前缀复用均正确；
  BF16 同环境冒烟通过；构建/import/UT 通过。
- **未通过/不可宣称**：默认异步发射下的间歇损坏（18/24 vs 0/24；归因已由 §6 更正为
  INT2 中层读路径 **OPEN**，不再称"环境竞态"）；
  因此不能把 main 服务标为生产可用，也不能引用交付树的精度/性能数字。
- 后续工作：CANN 竞态复测（换镜像/驱动版本）、在 main 树补 warmup 前置（交付线用 R160 热修，
  main 无该 overlay）、把串行化脚注写进 launcher 说明。

## 6. 异步故障定位更新（2026-10-24 04:40Z，子 Agent A 二分 + 主 Agent 复核）

本节**取代** §4.2 与 §5 中"CANN aclnn 发射层竞态"的归因。

### 6.1 新增证据（全部在同镜像 / main 集成分支 `81295d899` / NPU 7 / flock 内）

| 腿 | 配置 | 请求 | 坏/总 |
|---|---|---|---|
| `bf16a` | BF16 同请求 | ragged/l4/l4mix/long2 ×6 | **0/24** |
| `x900x4` | 4 行 × ~890 token（无 INT2 中层） | ×6 | **0/6** |
| `x1080x1` | B=1 1080 token（中层 56） | ×12 | **5/12** |
| `x1080x1_blk` | 同上 + `ASCEND_LAUNCH_BLOCKING=1` | ×12 | **0/12**（主 Agent 04:28–04:32Z 补跑） |
| `x1601x1` / `_blk` | B=1 1601 token（中层 577） | ×12 | 8/12 / **0/12** |
| `x1080_wsync` | + `R166_WSYNC=1` | ×12 | 9/12 |
| `x1080_hpsafe` | + `R164_PREFILL_SAFE=1` | ×12 | 8/12 |
| `x1080_pymid` | + `R113_MIDDLE_CPP=0`（Python 中层） | ×12 | 11/12 |
| `x1080_qsync0` | + `R113_QUANT_SYNC=0` | ×12 | 12/12 |

原始输出：`/tmp/r218_async_diag/battery_<tag>.txt`、`<tag>.analysis.txt`、`<tag>.status`；
serve 日志：容器 `r218-main-verify:/tmp/serve_<tag>.log`。

### 6.2 结论（OPEN；2026-10-24 晚更正＋定位更新，主 Agent 应用替换）

- 故障**需要 INT2 中层参与**且 B=1 即可复现；BF16 同电池 0/24 → 不是框架/CANN 通用竞态。
- 【更正】原「INT2 C++ 中层算子不是缺口（Python 中层路径 11/12）」**撤回**：
  `R113_MIDDLE_CPP=0` 只把操作数准备从 C++（`oscar_middle_prep`）换回 Python ATen，
  `R112_LSE_FAST=1` 默认未变，自定义算子仍被调用（`middle_candidate.py:542 launch_lse_fast`；
  `R133_GRAPH_V1=1` 时 :504/:530 `launch_lse_v1_own`；R112=0 时 :563 `launch_lse`）。
  该腿仅证明「换 Python 操作数准备不治」；中层算子的排除改由下条定位中的逐字节证据支撑。
- 【更正】原「至少两条独立流序边」降级为**观察**：失败率随同步/量化器开关显著变化
  （`R113_QUANT_SYNC` 0→12/12 vs 1→5/12；`R113_QUANT_CPP` 0→11/24 vs 1→18/24）——
  host sync 确实掩盖至少一条通路，但不能据此断言独立边数。
- 【新定位（设备轮 2，2026-10-24 13:16–14:53Z，详见 `delivery/PR_ADVANCE_20261024.md` §3.6）】
  首个分歧张量＝**HP 环 bf16 行（recent 窗）**：坏 rep 首个 decode step 环行即与 blocking 分歧，
  此刻 `key_rot/value_rot`（环写输入值）、q、INT2 中层页、中层算子输出**全部逐字节相同**；
  张量级形态＝环 recent 窗 [128,1024) **NaN 污染**、每代恒增 1,310,720 元素（跨代残留）；
  INT2 写侧 src_k/src_v/src_ks 12 rep 全程哈希与 blocking 一致（量化输入观测；⚠不能据此排除存储写越界/内存副作用——写入者审计进行中）。
  写→读同步（9/12）、HP 环写生命周期（8/12）排除仍成立；环写机制候选
  `R166_STREAMFIX=ring`（12/12）、`R164_EAGER_SLIDE`（9/12）不治。
- blocking 0/12 只支持"时序相关"，**不据此归因 CANN**；未取得可合入最小修复前，
  默认异步正确性保持 OPEN，不标生产可用。NaN 种子来源（外部越界写 vs 环读侧放大）OPEN。

详细依赖表、分支/SHA、修复映射与容量对账见
`delivery/PR_ADVANCE_20261024.md`。

## 7. INT2 KV 容量修复：设备验证（2026-10-24 05:35Z）

§4.1/§4.2 的 2.00× 只是 dtype 宽度比；本节给出把引擎记账改成物理打包后字节后的
**实际服务结果**。修复在独立分支，**未合入** `m-port-full-ut`，也未开上游 PR。

### 7.1 分支与代码

| 项 | 值 |
|---|---|
| fork 分支 | `oscar-int2/capfix-int2-spec` @ `d1db5264a8f1`（API 提交；树 `3588297086dc`） |
| 本地等价提交 | `d67b3a0b16b9`（树相同；逐文件 blob 与远端一致，raw 重下 sha256 相同） |
| 补丁 | `R218_UPSTREAM_WORK/int2_capacity_fix.patch`，sha256 `8289c8bf2ceb43d5ba6ec854a76da02440c2ab8475aeef26d896ccfaa59f4ce1` |
| 改动 | ① `worker/v2/attn_utils.py` + `worker/v1/model_runner.py`：INT2 full-attention 层发布 `state_content_bytes = (head_size+head_size_v)//4 + 4*dtype_size`（Qwen3-8B = 72 B），head 尺寸不整除时 fail-closed 保持稠密 spec；② `worker/worker.py`：从 KV 预算中扣除 BF16 高精度环（prefix+recent、`max_num_seqs+1` 行、PRREAD/HPFIT 几何） |
| 测试 | 新增 `tests/ut/oscar/test_int2_kv_spec.py` 7 条（打包页 73,728 B、非 INT2 不变、head 不整除 fail-closed、HP 环 5,002,297,344 / PRREAD 1,024 / HPFIT 封顶）；上游镜像内 `pytest --noconftest tests/ut/oscar` = **142 passed** |

### 7.2 实测（同一 nightly 镜像 / 容器 / NPU 7 / Qwen3-8B，GMU 0.60，`--enforce-eager`）

```
INT2: reserving 4.64 GiB for the BF16 HP ring
Available KV cache memory: 16.40 GiB
NPU KV cache size: 849,280 tokens, Maximum concurrency for 2,048 tokens per request: 414.69x
```

| 量 | 修复前 | 修复后 | 比 |
|---|---:|---:|---:|
| 引擎 KV 预算 | 21.04 GiB | 16.40 GiB（21.04 − 4.64 HP 环） | — |
| 池 token（2K 引擎口径） | 306,432 | **849,280** | **2.77×** |
| 对 BF16（153,216） | 2.0000× | **5.54×** | — |
| 物理 KV 校验 | — | 849,280 × 576 B × 36 层 = 16.40 GiB | 与预算一致 |

`4.64 GiB`（而非 4.66）是因为 canonical 环境 `R199_PRREAD=1`：HP 环为
prefix 128 + recent 896 = 1,024 token（无 +4 margin），ms = max(32,4,33) = 33；
`36×2×33×1024×8×128×2 B = 4.983e9 B`。

**正确性（仅诊断姿态 `ASCEND_LAUNCH_BLOCKING=1`）**：中层电池 **24/24**、
通用 17 形态电池 **17/17**，合计 **41/41** 无损坏。默认异步同最小复现
（1080 tok）仍 **12/12 坏**（小样本负对照）⇒ 容量修复**不改变**异步缺陷，异步仍 OPEN。

### 7.3 边界

- 未测吞吐；不把池 token 当"实测最大可服务并发"（实测活跃 batch 仍为电池规模）。
- V1 runner 的同一 helper 仅有 UT 覆盖，服务腿只走了本栈的 V2 spec 补丁路径。
- 修复改变 `page_size_bytes`/`num_blocks` 的所有消费者；合入前需在正式（默认异步
  关闭后）姿态复跑验收，并与 PR-07/22 的贡献映射对齐。
- 结论：**容量记账修复已验证（诊断姿态）；"内存收益"作为产品结论仍 OPEN**，
  直到默认异步正确性关闭并完成正式姿态复跑。
