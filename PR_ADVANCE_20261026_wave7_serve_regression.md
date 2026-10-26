# 最终集成树 serve 回归结果（NPU 7，2026-10-26 02:22–02:54，sister session 腿）

## 结果
- **INT2 默认异步**（fin_tree_int2）：**60/60 无 bad**（20 文件×3 reps：ragged/l4/l4mix/mix2/n2/n3/n4/n5/n8/h1/h2/h3/h4/h8/div2/div3/div4/long1/long2/reuse——含混合长度批、TND packed-varlen、槽复用/请求生命周期）
  - ⚠ battery_fin_tree_int2.txt 首行 500 是 02:02 崩溃轮（middle_candidate TypeError）残留 append，非本轮（analysis total=61 bad=1 的 bad=该残留；本轮 60 全清）
  - 另有 w7wA（并行腿）24/0 绿（6×4 中电池）
- **BF16 默认路径**（fin_tree_bf16）：**60/60 无 bad**

## 身份
- 树=/tmp/mpr19_wt → bind oscar_port_ut_tree；[R218ID] attention_v1 sha=81f6adc06cca333e（含懒建属性修复 30f7f2005＋并行会话细化）
- launcher=int2_op_launch_lse_fast_r152.cpp sha256 41bce535…（#19570 修复版，预编译）；R218-QBOUND entry=oscar_middle_prep ACTIVE
- r98 bridge=r98.lse.v1；OPP=R144_OPP_PATH 冻结链（grp c8a8d47a）
- **容器披露**：layernorm.py 容器 shim sha 6f17ab3d…（CANN 9.2.0 无 aclnnAddRmsNormBias→npu_rms_norm 回退；非 PR 内容）；VLLM_BATCH_INVARIANT=1
- 02:02 轮崩溃根因=mixin 懒建属性 `=None` 注解（hasattr 恒真）→ 已修（worktree 30f7f2005）并传播 #19742→9f74292dfa、#19746→332cbb62a1；quantcache/slotstate/worker/dtype-patch 四适配已传播 #19734→080e4cdc0a、#19735→ad99bad433（PR 19-22 分支头已恢复为你们的 f743c2d143/41d0cd64d5/3da02b4fa2/8211bd7ec0——我此前 force-push 覆盖了你们 ruff-format 清洁头，抱歉，已还原）

→ 腿全绿：19-22 可转 ready（你们的分工项）。
