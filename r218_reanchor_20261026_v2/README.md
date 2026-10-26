# R218 re-anchor + six-prompt grading incremental evidence — v2 (2026-10-26, dev5)

**Current valid version: v2** (supersedes the v1 tarball
`r218_reanchor_evidence_20261026.tar.gz` kept on the branch as history; v1
claims corrected here are listed in REGRADE + LP correction below).
Acceptance version: #19767@bfad514b0 (tree 6a8b6c444c6325e553edb9d0ab60b22ccdb2832a,
attention_v1 sha256[:16]=9eb603e3b10ea866). Terminology: "同步上游 main 后的集成 tip".
Device: NPU 5 (found idle; per-device flock; no peer processes touched).

## What changed in v2 (external review round)
- REGRADE_SIX_PROMPTS_20261026.md + gradeable_inputs/ (complete inputs,
  pre-registered rule, grader) — layered regrade of existing outputs:
  run B keyword-hit INT2 6/6 == BF16 6/6 (keyword hits, NOT strict answer
  correctness); strict first-answer view INT2 4/5 vs BF16 5/5 (INT2 misses
  ctrl_fox1: first answer "the dog." for "what color" — `brown` only appears
  later); needle **target-identifier hit 4/4**, needle **full-output==BF16
  3/4** (mix2 diverges after the identifier: INT2 on-target repetition vs
  BF16 pangram filler); run A keyword 3/6, identifier 1/4.
- LP_MARGIN_ANALYSIS.txt dated correction appended: "top-5 all identical"
  RETRACTED (long1/s4 common=4: ' subrange' vs '[item'); "runner-up
  promotion proven" RETRACTED (no flip instance captured; 8/8 probe
  continuations identical). Divergence mechanism stays OPEN. No new
  experiments.
- Run-A framing corrected: composition-difference observation only; does NOT
  establish "not a tip defect".

## Scope of run B (serve-regression anchor) — limited regression
Run B verifies the **PR framework + the specified precompiled extensions +
container shim + frozen kernels** on the merged-tip content (banner
9eb603e3): launcher .so d8a7fe617ea361ef, bridge .so b01928f62653b52b
(container-cached JIT builds, executed via mtime-aged no-op ninja), OPP
vendor kernels from csrc/build, layernorm CT-SHIM v2 5712c8db26e38e2
(recreation; original bytes 6f17ab3d unrecoverable), generated
_build_info.py ('A2'). It is NOT a full-stack verification of the tip alone.
Provenance UNKNOWNs, recorded as such: the cached .so builds cannot be
byte-linked to a source revision (the bind-tree cpp bytes that produced them
are unrecoverable; the cpp now on disk daf02231224ce5b0/8f8011133d1a34cc
comes from oscar-int2/launcher-commit-boundary and the executed .so loaded
from cache, so source→binary linkage is UNPROVEN).

## Contents
- ranchor_runB/ — anchor: int2 24/24 bad=0 + bf16 24/24 bad=0 (per-epoch
  recount; battery files contain runA+runB rows, "total=48" = the sum);
  identities: [R112-FAST] r113.orch.v9+r145v3+r218p7bound +
  [R218-QBOUND] oscar_middle_prep slot=1 ACTIVE + [R218ID] 9eb603e3 +
  [R218ROT] LOADED (bf16 = [R218ID]-only); runtime_composition.txt.
- ranchor_runA/ — fallback-composition run (launcher/bridge absent): 24/24
  bad=0 both modes; robustness datapoint only.
- gradeable_runB/ — original grade.py output preserved (keyword hits) +
  v2 layered views in REGRADE_SIX_PROMPTS_20261026.md.
- gradeable_runA/ — INT2 3/6 keyword vs BF16 6/6 (composition datapoint).
- lp_margin/ — margins INT2 0.75–1.25 vs BF16 0.50–0.63 nat (observation);
  correction section appended (mechanism OPEN).
- INCIDENT_SYNC_CASUALTIES.md — sync casualties, fixes, non-regressions,
  rc-gotcha, battery-file caveat, corrected run-A framing.

## Two-anchor identity note
- 8-file battery: merged-tip content (banner 9eb603e3) under the limited
  composition above (run B). 13-file lifecycle battery: pre-merge anchor
  a7da582bd (81f6adc0). Survival (bad=0) is the structural criterion;
  answer quality is reported per prompt with the layered views — INT2==BF16
  on keyword hits (6/6), 4/5 vs 5/5 strict first-answer on unambiguous
  prompts, needle identifier 4/4, needle full-text 3/4.
