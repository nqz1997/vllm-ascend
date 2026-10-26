# R218 wave-7 服务回归补篇（ADDENDUM，2026-10-26 04:5xZ）——附于 ARTICLE §11 之后引用

> 本篇为 §11 的增补与更正层，全部出自现有输出（零设备重跑）。归档件：
> delivery/r218_wave7_final/{PAIRED_ANALYSIS.txt, ANSWER_CHECK_LOOP_ANALYSIS.txt}。

## A. 逐请求答案检查（保留 bad 指标，另列答案/确定性）
- bad（无 choices 或 '!!!'）：INT2 0/24+0/39+0/60；BF16 0/21+0/60。
- 答案一致率（同输入贪心，choice0 逐 token 全同 INT2 vs BF16）：45/60（75%）；
  分歧 15/60 全部首 token 岔开、0 措辞渐变（双峰）。
- 电池为合成机械探针（fox 重复句/Hello），无语义答案/ground truth；答案级精度由
  冻结组合评测组独立回答（核心六道 INT2≈BF16）。

## B. 分歧结构：逐提示稳定（关键更正与新增证据）
- 15 条分歧＝恰 5 个提示 × 3 rep 全体（rep 间模式一致）；同 5 提示 BF16 三 rep 全 FieldType
  ⇒ INT2 argmax 翻转为逐提示确定性，非随机扰动样本。
- 替代循环 token 仅 3 种：backstage ×6、subrange ×6、itemList/modules 混杂串 ×2；
  均不在 BF16 全部 201 样本输出分布内（BF16 吸引子集＝{FieldType}）。
- **更正**：撤回此前"BF16 l4/s4/reuse 两态翻转"口径——两"态"仅在 24-token 截断边界
  差 1 token（长度截断伪差），BF16 实际 7/7 文件单一吸引子。

## C. 重复尾定性
- 循环本身＝基线行为：BF16 201/201 样本同为单 token 循环（finish_reason=length）。
- 非 ASCII 14/201（全部分歧样本内；choice0 口径 8/15）＝循环 token 含非 ASCII 字节
  （如 'rô'），非额外损坏；非 ASCII 本身不构成错误判据。
- 未闭合项：翻转的 logit 边际量化。logprobs 配对探针已备（/tmp/lp_probe.sh：4 提示
  ×2 模式、temp=0、logprobs=5、max_tokens=6、flock 全程持有），当前被非本会话容器
  负载占用设备（dev6/7 各 ~52GB、宿主侧无持有者）阻塞；设备空出即执行，约 6 分钟。

## D. 42↔39 请求清单核对
- 5 代驱动脚本（w7_legs.sh..5.sh）w7wB 文件列表恒为同一 13 文件 ×3＝39；
  "14 文件×3=42"仅系 HANDOFF 散文笔误（13 误写 14），非中途改计划、无缺项；
  n8 不在 w7wB 列表，但在 fin_tree 电池于同树双模式覆盖 ≥3 rep。

## E. 最终树全树 diff（非仅 9 blob）
- a7da582bd 全树（4583 blob）vs 本地基线 30f7f2005（4584 含 1 gitlink）：路径集全同
  （唯一差＝csrc/third_party/catlass 子模块指针类型差，非删除）；blob 差恰好 8 文件
  ＝7 个运行时 overlay（remote==被测工作树字节）＋tests/ut/oscar/test_kv_int2.py
  （I001 导入排序）。无意外删除/遗漏运行文件。
