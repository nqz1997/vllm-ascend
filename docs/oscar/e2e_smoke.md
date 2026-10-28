# OSCAR INT2 end-to-end smoke (customer e2e)

Minimal customer-facing smoke for the INT2 three-tier KV-cache stack, pinned to
the current PR-stack baseline (MODE B three-tier middle, C++ quantizer write
path, per-token-head affine INT2 KV).

## Run

```bash
MODEL=/path/to/Qwen3-8B \
K_ROT=/path/to/k_rotation_qqt_r_h_pbr.pt \
V_ROT=/path/to/v_rotation_sst_r_h_pbr.pt \
bash tools/oscar_e2e_smoke.sh
```

## What it checks

1. The served stack announces its identity (`[R218ID]` banner in the serve log).
2. Three deterministic prompts return non-empty completions.
3. The serve is launched with the product posture envs (three-tier middle on,
   C++ quantizer + sync + scatter on, rotation assets wired, prefix/recent
   window at the acceptance values 128/896).

## Pass criteria

`SMOKE PASS` on stdout and exit code 0. Any missing banner, empty answer, or
serve crash fails the smoke. This is a smoke, not an accuracy suite; accuracy
and throughput numbers live in the acceptance evidence packs.
