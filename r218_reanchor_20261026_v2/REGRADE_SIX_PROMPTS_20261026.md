# Six-prompt regrade with complete inputs and pre-registered rule (2026-10-26)

Regrade of the EXISTING outputs (no rerun, no rule change). Trigger: external
review correctly noted the original "PASS" is case-insensitive substring
containment — a **keyword hit**, not strict answer correctness (ctrl_fox1:
expected `brown`, INT2's first answer is `the dog.`).

## Pre-registered rule (verbatim, unchanged)
- Inputs: 6 JSON request files in `gradeable_inputs/` (temp=0, max_tokens=24,
  greedy; needle prompts ask for an access codeword / gate key / vault token,
  answer stem "… is"; ctrl prompts ask "What color is the fox"/"What animal
  does the fox jump over", stems "The fox is"/"The fox jumps over the").
- Expected values: `gradeable_inputs/expected.json` (`expected_contains` only).
- Grader: `gradeable_inputs/grade.py` — `PASS = expected_contains.lower() in
  text.lower()`; `repetitive = len(set(text.split())) < 4`; finish recorded.
- File SHA256s recorded in MANIFEST (grade.py + 7 json).
- Original printed results preserved verbatim in
  `gradeable_runB/GRADE_RESULT.txt` and `gradeable_runA/GRADE_RESULT.txt`.
  Nothing below replaces or loosens them; the layered views are ADDITIVE.

## Layered regrade — run B (full composition, serve-regression anchor)

| metric | INT2 | BF16 |
|---|---|---|
| keyword hit (original rule) | 6/6 | 6/6 |
| first-token correct (unambiguous prompts: 4 needles + ctrl_fox1) | 4/5 | 5/5 |
| needle target-identifier hit (containment, 4 items) | **4/4** | 4/4 |
| needle identifier as first token | 4/4 | 4/4 |
| needle full output == BF16 (exact text) | **3/4** | — |
| ctrl full output == BF16 | 0/2 | — |

Per-prompt first tokens (INT2/BF16): mid1 `ZEBRA-47.`/`ZEBRA-47.` · mid2
`MANGO-88.`/`MANGO-88.` · mix1 `QUARTZ-12.`/`QUARTZ-12.` · mix2
`TULIP-35.`/`TULIP-35.` · ctrl_fox1 **`the`(→"the dog.")/`brown.`** ·
ctrl_fox2 `quick`/`lazy`.

- **ctrl_fox1 (the reviewed case):** INT2 keyword-hit only; under the
  question "What color is the fox… A: The fox is", the first answer
  ` the dog.` is wrong; `brown` appears later in the continuation. BF16's
  first token is ` brown.` — correct. The original "PASS 6/6" must be read
  as **关键词命中率 (keyword hit rate), not 严格答案正确率 (strict answer
  correctness)**.
- **ctrl_fox2 criterion note:** stem is "The fox jumps over the" — `lazy
  dog` is the natural continuation, so BF16's first token `lazy` is not an
  error even though `expected_contains` is `dog`; first-token-vs-`dog` is
  not a fair strict criterion for this item. Both modes keyword-hit.
- **needle_mix2 (the 1/4 full-text difference):** identifier and first token
  identical; continuations diverge after "TULIP-35. " — INT2 repeats the
  on-target phrase (`The vault token is TULIP-35. The vault token is TUL…`),
  BF16 switches to the pangram filler. INT2 output is internally repetitive
  but on-target.

## Layered regrade — run A (fallback composition, robustness datapoint)

| metric | INT2 | BF16 |
|---|---|---|
| keyword hit | 3/6 | 6/6 |
| needle identifier hit | 1/4 (TULIP-35 only; `ZEBRA.` lost suffix, `MATH.`, `QUICKBROWNFOX…`) | 4/4 |
| full output == BF16 | 0/6 | — |

## Reading discipline
- All "6/6 PASS" statements in earlier materials = keyword hits. Strict
  first-answer view for run B: INT2 4/5 vs BF16 5/5 on unambiguous prompts
  (INT2 misses ctrl_fox1 only); needle retrieval view: identifier 4/4,
  full-text equality 3/4.
- Run A's degradation is a **composition-difference observation** (fallback
  vs full composition on the same tree); it does not by itself establish
  "not a tip defect" — that inference would require showing the tip itself
  behaves identically under both compositions, which was not tested.
