# SELFVERIFY-LOG — paper2-protocol release candidate (PAPER-P2-3)

- declared date (human constant, not machine wall-clock): 2026-09-12
- packager: PAPER-P2-3 worker (Wave 3)
- scope: packaging-time self-verification of
  `artifact-release/paper2-protocol/` — a local release *candidate* copy.
  **No external publishing/upload/push action was performed.**
- red lines observed: PR-1 (frozen originals untouched — verified below),
  PR-2 (release-copy discipline: no frozen reader-raw readings, no GT, no
  machine paths shipped), PR-4 (outbound scan re-run over the release
  directory, §7).

## 1. Protocol copies: byte-identical to frozen originals (PR-1)

| release copy | sha256 | equals dev-repo original |
|---|---|---|
| `protocol/evaluation-protocol-v1.md` | `22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e` | YES (also matches the hash registered in evaluation-protocol-v2 §0.2 and the terminology spec §6) |
| `protocol/evaluation-protocol-v2.md` | `365b67ef247ff2d664c620971fff21efc4ed684e55a2e99625823321669e0712` | YES (matches terminology spec §6) |

The originals at `out/v3-tl2/calibration/evaluation-protocol-v{1,2}.md`
were re-hashed after all packaging work: unchanged. `EVOLUTION.md` cites
only verified hashes (`r11-prep 9074df2d…`, `r12-prep d393cf27…`,
`r24-prep 760af49f…`, `protocol-v2-registration 36cc86a7…` — all measured
at packaging time).

## 2. Rubric: chain replay against the registered base chain (fail-closed)

Command: `python rubric/replay_r13_r16.py` (dev-repo layout default),
`--out` report sha256:

```
ebd4320b8d9cd26467ba1e39cc7dba53eca44c39509cc007d63a5fca76db2a83  (local replay report; internal, not shipped)
```

Result: **PASS, exit 0** —

- keyword tables in the release JSON == classifier code constants (fail-closed check);
- per-round family counts equal for all 4 rounds x 5 families; registered
  contact chain reproduced: **r13=8, r14=15, r15=5, r16=10**;
- grand family totals equal; abstain-flag total **132/132**;
- per-instance (abstain, flags): **24/24** equal to the registered
  aggregates AND **24/24** equal to the four `calibration-run-r13..r16.json`
  combined-instance records;
- per-flag family assignment: **132/132** equal to the frozen typology file
  `abstain-typology-r13-r16.json` `per_flag` (this check requires the
  internal frozen file and auto-skips, with a note, when it is absent).

## 3. Example chain: double-run byte-identity

Two independent process runs of
`render/example/run_example_chain.py --out-dir …` (board = corpus bm1,
kicad-cli 10.0.5), then `--compare run1 run2`:

| file (deterministic set) | sha256 (run 1) | run 1 vs run 2 |
|---|---|---|
| `bm1-top.png` | `18582b25ca36f0410d2f5752957396d48758204fa53e4bc4670c7630dfb590de` | IDENTICAL |
| `bm1-bottom.png` | `1e10abe7751eaa078dba89103e13b8c3b98cfb36fdbe85a4561df7ba28d20b2d` | IDENTICAL |
| `reader-input-manifest.json` | `c05549107247189dc5b181e9e2d3461d92bcce05dbe1bfee430fb82f6109dad3` | IDENTICAL |
| `demo_reader_raw.json` | `bf74c28407b6441904c33f02c3a7f29bd3cdd1f63cafa47430cafe89aca568ed` | IDENTICAL |
| `rubric_classification.json` | `9ab273ba9443583f5afd69ad23328436e72138f7140d52627d010dafcf189767` | IDENTICAL |
| `chain_manifest.json` | `b87471b795f5546954811a0899c6692260f2040b9142953c5f7c0847124c72a7` | IDENTICAL |

Run-local provenance files (`*.pdf`, `*.render-evidence.json`) were NOT
cross-run asserted, per the preregistered determinism scope: kicad-cli PDF
bytes are not cross-run deterministic (rasterization onward is); this is
the same scope registered in the dev repo since r4/r14b. The two run PDFs
indeed differed in bytes while both produced identical PNGs — recorded, not
treated as failure.

Classification within the chain: **8/8** synthetic demo flags matched their
preregistered families (existence_blackdot 2, contact 1, existence_other 2,
semantic_confusion 1, other 2). The reference outputs shipped under
`render/example/reference-output/` are the run-1 deterministic set plus the
two render-evidence files (sha256:
`214f8f65562f04cbd3d1ac287bc7e19c8479e33e965e9f0e6b73427978e813a5`,
`13d1217108447f89a735d4192d27ef2fbdc9a1f6bb7179ad76fc1638bff998ec`).

Demo-flag status is marked `synthetic: true` in the shipped
`demo_reader_raw.json`: hand-written format examples; **no frozen reader
reading and no model output is shipped in this package.**

## 4. Render instrument port validation

- `png_board_pixel_bounds` (standalone numpy/PIL port in
  `render_reproduce.py`) vs the dev reference
  `pcbflow.calibration.png_board_pixel_bounds`: **equal dict results** on
  both the full composed page (8195x6003; bounds 2653,2326,5379,3676) and
  the cropped PNG of the example render.
- In-script determinism self-check (raster → bounds → crop rerun,
  byte-compared): `det_rerun=True` for every view of every run.
- Optional r14b recolor stage smoke test (bm1 bottom): 236 white-fill
  drawings rebuilt from PDF vectors → orange 93,107 px; void white → green
  2,550,483 px; orange/green intersection 0; board-interior residual white
  0; color-distance assertion pass (>150 vs every canvas base color).
  Deterministic rerun byte-identical. (Not part of the default chain; see
  `render/color_legend.md` for scope.)

## 5. Dataset zero-write verification

Whole-tree audit of `datasets/` before and after all render runs:

| | file count | whole-tree aggregate sha256 |
|---|---|---|
| before | 778 | `7d3d2a353140f413d556542f1caa1914ca3c00a390fd88093c0634a7fadc058b` |
| after | 778 | `7d3d2a353140f413d556542f1caa1914ca3c00a390fd88093c0634a7fadc058b` |

**Unchanged** (aggregate = sha256 over the sorted
`relpath|size|file-sha256` stream). `find datasets -name "*.kicad_prl"` →
**0 files**: kicad-cli's sidecar landed next to the in-run *copy* of the
board (by design), is recorded per view in
`kicad_prl_sidecars_in_workdir` of the render-evidence files, and never
touched the dataset tree. No file inside `datasets/` was created, modified,
or deleted (S40-incident guard held).

## 6. Exit-gate checklist

- [x] Three content classes present: protocol/ (v1+v2 copies + EVOLUTION),
      rubric/ (JSON wordlists + algorithm + chain replay), render/
      (pipeline + deps + color legend + runnable example with reference
      outputs);
- [x] Example chain runs and is deterministic (double-run byte-identical
      deterministic set; §3);
- [x] Chain replay equals registered counts (132/132, 24/24, 8/15/5/10; §2);
- [x] PR-4 outbound scan over the release directory: zero unhandled
      findings (§7);
- [x] Frozen originals byte-preserved; datasets byte-preserved (§1, §5);
- [x] No reader-raw frozen readings, no GT, no machine paths, no
      credentials shipped (§7 scan + PR-2 review);
- [x] License file present: Apache-2.0 (decision recorded 2026-09-12);
      example PNGs additionally CC-BY-SA-derived, disclosed in README §7
      with a removal instruction for CC-BY-SA-free distributions.

## 7. PR-4 outbound scan (S2 scanner re-run over the release directory)

Scanner: `out/v4-exec/redaction-scan-r1.py` (the S2 scanner, unmodified)
invoked in scan-only mode with the release directory as the sole root
(path base = workspace root so the classification mapping applies).
Payloads are written OUTSIDE the release directory, to `out/v4-exec/`
(the payload embeds the ruleset literals and is therefore itself internal,
exactly like the S2 artifact `paper-redaction-scan-r1.json`).

Registered exit criterion (S2-consistent): **zero findings of the
must-fix classes** — absolute paths, username, hostname, machine drive
paths, credential keywords, credential values, PEM keys, git author
handle, email PII; zero `critical` severity. The two high-entropy
fingerprint classes (`HIGH_ENTROPY_HEX64`, `HIGH_ENTROPY_B64_48`) are
**pre-dispositioned benign** for this package: this release deliberately
publishes sha256 evidence hashes (self-verification and chain anchors),
and the S2 ruleset itself notes 64-hex hits on evidence-hash content are
expected benign.

Final-scan conclusion: **PASS — zero unhandled findings.** (Exact per-rule
counts and the full findings payload: internal artifact under
`out/v4-exec/`, registered as `paper2-3-pr4-rescan`; not shipped for the
ruleset-literal reason above.)

---
Packaging complete. Release candidate awaits reviewer (master-reviewer
re-run of the example chain) before any distribution decision. No external
release action has been taken.
