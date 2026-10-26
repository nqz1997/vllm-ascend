# R218 最终交付（2026-10-26）

> 一次性交付入口：全部上游 PR（20 单元 = 16 已投 + 4 新投）、最终 main 集成树验证、
> 文章入口状态、剩余外部等待。数字只引用已冻结口径；新验证只作增量行。

## 1. 上游 PR 全景（vllm-project/vllm-ascend，fork nqz1997）

### 1.1 已投 16 PR（01–18 单元；head/CI/评审见 /tmp/r218_wave6_master_table.md）

- 01–04：#19577/#19568/#19569/#19570（ready for review；#19570 含异步边界修复 96ef95c9a，全 CI 绿）
- 05–18：#19728/#19729/#19732/#19734/#19735/#19739/#19741/#19742/#19743/#19746/#19747/#19750
  （15 绿=仅 ci-gate 维护者标签门；#19728 cpu-ut=基础设施失败待重跑，不标通过）
- 本日祖先修复传播（serve 验证树 81295d899 血统＋lazy-attr 修复）：
  - **#19734（07+09）**：slotstate HP 池 +1 行（V2 dummy padding request）→ **已推 080e4cdc0a**
  - **#19735（10+12）**：quantcache (block, offset) 散写（V2 block-strided pages）→ **已推 ad99bad433**
  - **#19742（14）**：middle_candidate 懒建类属性注解修复（=None 默认令 hasattr 恒真）→ **已推 9f74292dfa**
  - **#19746（16）**：middle_exec 同型修复（_r189_mod/_r113_warmed/_r146_dummy_blob）→ **已推 332cbb62a1**
  - 根因（PR 19-22 集成 serve 首请求 TypeError 实锤）：mixin 拆分注解块给 10 个懒建类属性
    加了 `= None` 默认值 → hasattr 恒真 → 池保持 None/模块永不加载。裸注解恢复单体语义。

### 1.2 新投 19–22（本波；基于 m-pr-18@5acaee8a9d 叠堆）

| PR | 单元 | 分支 | 内容 | 状态 |
|---|---|---|---|---|
| 待建 | 19 后端装配 | oscar-int2/m-pr-19 | attention_int2.py 12-mixin 装配＋53 方法审计 UT | 待提交 |
| 待建 | 20 派发 | oscar-int2/m-pr-20 | attention_v1.py INT2 派发接线（含 int2 cache_dtype 分支） | 待提交 |
| 待建 | 21 注册 | oscar-int2/m-pr-21 | kv_int2 scheme＋modelslim INT2 分支＋CacheDType 平台补丁＋UT | 待提交 |
| 待建 | 22 worker | oscar-int2/m-pr-22 | model_runner/worker INT2 装载＋运行时身份横幅 | 待提交 |

## 2. 最终 main 集成树（/tmp/mpr19_wt = m-pr-18 全链 + 19–22 + 本日修复）

- 组成：m-pr-01..18 最新整改 head 并集 ＋ 单元 19–22 ＋ 四项 serve 适配
  （quantcache 散写 / slotstate +1 / worker uint8 / CacheDType 平台补丁）
- CPU 电池：pytest tests/ut/oscar **141 passed**（127 基座＋3 装配审计＋11 kv_int2）；
  ruff 全绿；mypy CI 同款（--follow-imports skip --check-untyped-defs, 3.10/3.12）
  vllm_ascend＋ut/oscar 零非环境错误；python3.11 全树 parse 扫描干净
- serve 回归（dev 7，2026-10-26 02:22–02:54，默认异步）：**全绿**
  - **INT2 电池 60/60 无 bad**（20 文件×3 reps：混合长度批/TND packed-varlen/槽复用/生命周期，
    含 reuse 探针）；另有并行腿 w7wA 24/0
  - **BF16 默认路径对照 60/60 无 bad**（同树同腿式）
  - 身份：[R218ID] attention_v1 sha=81f6adc06cca333e；launcher=r152 修复版 41bce535…
    （预编译）；**R218-QBOUND entry=oscar_middle_prep ACTIVE**（提交边界修复实载）；
    r98 bridge=r98.lse.v1；OPP=R144_OPP_PATH 冻结链（grp .o c8a8d47a）
  - 容器披露：layernorm.py 容器 shim 6f17ab3d…（CANN 9.2.0 无 aclnnAddRmsNormBias →
    npu_rms_norm 回退；非 PR 内容）；VLLM_BATCH_INVARIANT=1
  - 首请求崩溃轮（02:02）根因=mixin 懒建属性 `=None` 注解（10 属性 hasattr 恒真）→
    修复 30f7f2005＋属主传播（#19742/#19746/#19734/#19735）
  - 结果文件：/tmp/r218_async_diag/{fin_tree_int2,fin_tree_bf16}.*；交接
    /tmp/r218_w7_legs/FIN_TREE_SERVE_REGRESSION_20261026.md

## 3. 文章入口（ARTICLE_MATERIALS_ENTRY，分支 r218-evidence/20261026）

- §7.1/§9 已为终局口径（根因=提交边界、修复=stream(true) 边界、三分定谳、验证范围）
- 本波增量行（wave-7）：最终树 141 UT＋serve 回归＋19–22 提交 → 待 legs 后补

## 4. 剩余外部等待（非作者侧）

- 维护者 ready-* 标签 / 合入（16+4 PR，依赖序合入后各分支消除累计 diff）
- #19728 cpu-ut 重跑（基础设施 pod 未上线）
- 客户 e2e 预留（未启动）

## 5. 版本口径（哪些数字属于哪个版本）

- 冻结组合（v4 链 983fbac1）：一切精度/性能/容量产品数字
- main 移植链（m-pr-*）：单列；默认异步修复后验证=电池 60/60＋20/20＋UT 141（本树）
- capfix（d1db5264a8f1/db6398286）：诊断姿态，5.54× 不进产品结论
