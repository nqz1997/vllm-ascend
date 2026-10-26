# R218 re-anchor + six-prompt grading incremental evidence — 2026-10-26 (dev5)

Acceptance version: #19767@bfad514b0 (tree 6a8b6c444c6325e553edb9d0ab60b22ccdb2832a,
attention_v1 sha256[:16]=9eb603e3b10ea866). Terminology: "同步上游 main 后的集成 tip".
Device: NPU 5 (found idle; per-device flock; no peer processes touched).

## Contents
- ranchor_runB/   — SERVE-REGRESSION ANCHOR (full composition, see
  INCIDENT_SYNC_CASUALTIES.md): int2 24/24 bad=0, bf16 24/24 bad=0 (per-epoch
  recount; battery files contain runA+runB rows, "total=48" lines are the sum);
  identities with launcher/QBOUND/ROT banners (int2) and [R218ID]-only (bf16);
  runtime_composition.txt (artifacts + disclosed container fixes).
- ranchor_runA/   — fallback-composition run (launcher/bridge absent, ATen path):
  24/24 bad=0 both modes; preserved for robustness record only.
- gradeable_runB/ — six-prompt strict grading, full composition:
  INT2 6/6 PASS, BF16 6/6 PASS (needles ZEBRA-47/MANGO-88/QUARTZ-12/TULIP-35 +
  ctrl brown/dog; temp=0, max_tokens=24, no post-hoc loosening).
- gradeable_runA/ — same six prompts, fallback composition: INT2 3/6, BF16 6/6
  (attractor-style failures; composition-sensitive, not a tip defect).
- lp_margin/      — LP_MARGIN_ANALYSIS.txt (probe margins INT2 0.75–1.25 nat vs
  BF16 0.50–0.63; identical top-5 candidate sets; mechanism = runner-up
  promotion; explicitly NOT a correctness proof).
- INCIDENT_SYNC_CASUALTIES.md — sync casualties, fixes, non-regressions,
  composition split, rc-gotcha, battery-file caveat.

## Bottom line for the two-anchor identity note
- serve-regression evidence for the 8-file battery = merged-tip content
  (banner 9eb603e3) under the wave-7 runtime composition (launcher .so
  d8a7fe617ea361ef, bridge .so b01928f62653b52b, disclosed CT-SHIM v2
  5712c8db26e38e2 + generated _build_info).
- pre-merge anchor a7da582bd (81f6adc0) remains the 13-file lifecycle battery
  anchor. Survival (bad=0) is the structural criterion; answer quality on the
  six-prompt minimal set is reported per prompt, INT2==BF16 under full
  composition, INT2 3/6 under fallback composition.
