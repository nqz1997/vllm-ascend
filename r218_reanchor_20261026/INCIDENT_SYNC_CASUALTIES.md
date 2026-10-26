# Re-anchor incidents and composition disclosure (2026-10-26, dev5)

## What happened
The bfad514b0 tarball sync into the bind tree (comm-based stale-file removal +
tar overwrite, .so/op_api/pycache/.pth protected) deleted three classes of
bind-tree-only files that the runtime needs but no git tarball carries:

1. `vllm_ascend/_build_info.py` — build-generated (setup.py `gen_build_info`).
   The merged tip's `device/device_config.py` imports it at serve boot.
   Absence → `ImportError` at boot, both modes NOT-READY (chain2 legs 06:27/06:36Z).
   NOT a PR defect: upstream CI generates it during build (verified against
   setup.py by workspace-2e).
2. `vllm_ascend/ops/layernorm.py` container shim (old sha 6f17ab3d755dd973,
   bytes unrecoverable — bind tree is not a git repo). Recreated as
   `[R218-CT-SHIM v2]` sha 5712c8db26e38e2a: try `npu_add_rms_norm_bias`,
   on RuntimeError fall back to `torch_npu.npu_add_rms_norm`, (x, residual)
   tuple contract kept. Semantics per wave-7 HANDOFF.
3. `csrc/oscar/` overlay sources (launcher + LSE bridge):
   `int2_op_launch_lse_fast_r152.cpp`, `int2_op_launch_lse_r98.cpp`.
   Restored from fork branch `oscar-int2/launcher-commit-boundary`
   (blob shas b04e7e1e…/812be373…; file sha256[:16] daf02231224ce5b0 /
   8f8011133d1a34cc). Source mtimes aged below the cached JIT .o so the
   precompiled wave-7 extensions load with no rebuild:
   launcher .so d8a7fe617ea361ef prints the exact wave-7 banner
   `r113.orch.v9+r145v3+r218p7bound`; bridge .so b01928f62653b52b.
   HANDOFF's "launcher 41bce535" referred to the (now unrecoverable) bind-tree
   cpp bytes; the executed .so is the same build wave-7 ran.

## Non-regressions (checked, not assumed)
- `[R160-OVL]/[R161-OVL]` module-load soft failures: identical lines exist in
  the wave-7 w7wA/B/C serve logs — those modules were never in the fin-tree
  bind tree. Posture matches wave-7 exactly.
- `csrc/build/op_api/lib` "MISSING" in the first composition record was a
  dir-vs-file check artifact; the dir contains libcust_opapi.so (sha 99b884b5).
- chain2's "ranchor rc=0" was a shell gotcha: `echo "$(date -Is) rc=$?"` —
  the command substitution clobbers `$?`. Real rc was 1 (set -e abort at the
  collection `tail`). Nothing was published from it.

## Composition split of the two runs
- **Run A (fallback composition)** — csrc/oscar still absent: launcher/bridge
  load failures printed, execution on the ATen default path. ranchor 24/24
  bad=0 both modes; six-prompt gradeable INT2 3/6 (needle_mid1 `ZEBRA.` lost
  suffix, needle_mid2 `MATH.`, needle_mix1 `QUICKBROWNFOX…` attractor-style),
  BF16 6/6. Kept as a fallback-robustness data point only (survival clean,
  answers degraded) — NOT the serve-regression anchor.
- **Run B (full composition, serve-regression anchor)** — launcher r152 +
  r98 bridge + rotation + OPP active; identity banners:
  `[R112-FAST] Extension loaded: r113.orch.v9+r145v3+r218p7bound`,
  `[R218-QBOUND] entry=oscar_middle_prep slot=1 ACTIVE`,
  `[R218ID] sha=9eb603e3b10ea866` (= merged-tip attention_v1, acceptance
  version bfad514b0 / tree 6a8b6c444c…), `[R218ROT] LOADED`; BF16 leg =
  `[R218ID]`-only opt-out. ranchor 24/24 bad=0 both modes; six-prompt
  gradeable INT2 6/6 + BF16 6/6, INT2 outputs textually matching BF16 on the
  needle items. Run-A answer failures are therefore composition-sensitive,
  not a tip-content defect.

## Battery-file caveat
`battery_ranchor_{int2,bf16}.txt` are append-mode across runs; the "total=48"
analysis lines = runA 24 + runB 24. EPOCH_RECOUNT.txt classifies every row by
`created` epoch: 48 runA + 48 runB rows, 0 unclassified, 0 bad anywhere.
