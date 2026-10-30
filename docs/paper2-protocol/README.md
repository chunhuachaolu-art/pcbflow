# paper2-protocol — visual evaluation protocol templates, abstention rubric, and render reproduction kit

Reusable methodology artifacts extracted from a multimodal PCB-review
evaluation program ("reader" rounds: rendered board images are blind-read by
independent reader instances that emit advisory flags and explicit
abstentions). This package contains:

1. **protocol/** — the two frozen evaluation-protocol files (byte copies of
   the dev-repo originals) plus `EVOLUTION.md`, the registered change record
   of the whole version chain (v1 → v1.1 / v1.2 / v1.3 → v2).
2. **rubric/** — the abstention-typology rubric: keyword tables JSON **and
   the priority adjudication algorithm as executable code**, plus a chain
   replay script that re-derives the registered r13–r16 counts
   (fail-closed).
3. **render/** — a standalone, dependency-declared reproduction of the
   render instrument (kicad-cli → PyMuPDF compose → dpi-640 raster →
   board-bounds crop), the color rules/legend, and a minimal runnable
   example chain (render → blind-read format → rubric classification) with
   **no model calls**.

License: **Apache-2.0** (license decision recorded 2026-09-12; see
`LICENSE`). The example board and its renders are additionally subject to
the upstream board license — see "Dataset caliber and provenance" below.

---

## 1. Scope of applicability (read this first)

This kit is for **multimodal advisory evaluation**: a vision reader looks at
a render, emits flags (typed, with a confidence and a frame box) and may
explicitly **abstain** when it cannot responsibly confirm what it sees. The
methodology's product is calibrated *advisory evidence about the reader* —
flag yield, abstention behavior, self-consistency — not a verdict about the
board.

It is **not an authority** instrument. Hard boundaries inherited from the
protocols:

- Advisory flags and box hits are **not DRC, not electrical, not physics,
  not manufacturing conclusions** (protocol v1 §6 / v2 §5: visual results
  are never written as DRC/solver/production facts).
- `seed_match_rate` must never be reported as precision/FPR; unmatched flags
  are `unmatched/unadjudicated`, not false positives, until a human
  adjudicates them (v1 §2, v1 §6, v2 P2-5/P2-7).
- Letter verdicts (supported/reject/…) are *preregistered descriptive
  criteria hits per round*, not causal proofs and not gates; they never
  override the joint pass gate, and passing tentative thresholds never
  auto-promotes anything (v1 §3, v2 P2-8).
- Rubric families describe *stated abstention reasons in the corpus
  language the rubric was frozen on* (Chinese development-round
  reader-raw). Applying them to other corpora/languages is a descriptive
  extrapolation and requires the shipped chain replay against the
  registered base chain first — see below.

## 2. Layout

```
paper2-protocol/
├── README.md                          this file
├── LICENSE                            Apache-2.0
├── protocol/
│   ├── evaluation-protocol-v1.md      frozen protocol v1 (byte copy, sha256 22dc7337…)
│   ├── evaluation-protocol-v2.md      frozen protocol v2 (byte copy, sha256 365b67ef…)
│   └── EVOLUTION.md                   v1 → v1.1/v1.2/v1.3 → v2 change record
├── rubric/
│   ├── abstain-rubric-r13-r16.json    keyword tables (verbatim from the frozen
│   │                                  typology file) + registered chain counts +
│   │                                  algorithm spec
│   ├── abstain_classifier.py          THE priority adjudication algorithm (r25 lesson:
│   │                                  wordlists alone do not reproduce registered counts)
│   └── replay_r13_r16.py              chain replay vs registered r13–r16 base chain (fail-closed)
├── render/
│   ├── render_reproduce.py            fitz pipeline (kicad-cli → compose → raster → bounds → crop)
│   │                                  + optional r14b recolor stage
│   ├── requirements.txt               Python dependencies + external tool note
│   ├── color_legend.md                color rules and reader legend (default palette; r14b recolor)
│   └── example/
│       ├── run_example_chain.py       minimal deterministic chain: render → blind-read
│       │                              format → rubric classification (no model calls)
│       └── reference-output/          outputs of one reference run (byte-reproducible set)
└── SELFVERIFY-LOG.md                  packaging-time self-verification record
```

## 3. Minimal dependencies

- Python ≥ 3.10 with `pip install -r render/requirements.txt`
  (PyMuPDF, Pillow, numpy).
- `kicad-cli` (KiCad ≥ 7 command line; reference renders and the shipped
  example were produced with **kicad-cli 10.0.5**). Locate via
  `--kicad-cli`, env `KICAD_CLI`, or `PATH`. Version is recorded, not
  asserted (`--expect-version` opts in).
- The rubric parts need only Python ≥ 3.10 standard library.

## 4. Reproduction steps

### 4.1 Rubric chain replay (the methodological core)

```bash
cd rubric
python replay_r13_r16.py            # dev-repo layout: finds the corpus itself
python replay_r13_r16.py --registered-only   # corpus-free consistency check
```

The replay implements the registered rule: *before the rubric is applied to
any new corpus, replay it on the registered base chain (development rounds
r13–r16: 48 reader files, 132 abstain flags) and require every count to
equal the registered value — fail closed, never loosen a keyword.* The
replayed values at packaging time: contact chain **8/15/5/10**, per-round
family tables equal, per-instance (abstain, flags) **24/24** equal to both
the registered aggregates and the four run records, per-flag family
assignment **132/132** equal to the frozen typology.

Important (r25 lesson, why code ships): a naive keyword recount over a
corpus does **not** reproduce the registered counts. The registered numbers
come from the mutually exclusive priority adjudication implemented in
`abstain_classifier.py` (implementation order: existence_blackdot →
contact → existence_other(explicit) → semantic_confusion →
existence_other(generic fallback) → other; the JSON records both this order
and the historical registration order, and the deviation between them is
itself preregistered).

The r13–r16 reader-raw corpus and run records are internal frozen readings
and are **not redistributed** (see §7). Without them you can still run
`--registered-only`, and classify your own texts:

```bash
cd rubric
python abstain_classifier.py "黑点性质不明，无法确认是否为关注现象"
# -> ('existence_blackdot', {...matched keyword hits...})
```

### 4.2 Example chain (deterministic, no model calls)

```bash
cd render/example
python run_example_chain.py --out-dir RUN_DIR [--board PATH] [--kicad-cli PATH]
python run_example_chain.py --compare RUN_DIR_1 RUN_DIR_2
```

Default board: PCBBenchmarks subset board **bm1** (dev-repo corpus path
`datasets/pcbbenchmarks-r1/raw/bm1/bm1.routed.kicad_pcb`). The chain:

1. **render** — reproduces `bm1-top.png` / `bm1-bottom.png` with the frozen
   instrument parameters (dpi 640, 40 pt compose margin, +120 px crop).
   The board is copied into the run dir first (kicad-cli drops a
   `.kicad_prl` sidecar next to its input; never render in place — this is
   the dev-repo "S40 incident" and the reason for the copy step).
2. **blind-read format** — emits `reader-input-manifest.json` (the exact
   reader input/output contract: one image per instance; reader-raw JSON
   schema with the five-key flag projection `flag_id / category /
   confidence / abstain / frame_box_pct` + `location_evidence`; the v1.2
   tool rule) and `demo_reader_raw.json` with **8 synthetic hand-written
   flags** (clearly marked; not model output, not any round's frozen
   reading) that exercise every rubric family and both priority-ordering
   traps (blackdot-before-contact; silk-context contact word).
3. **rubric classification** — classifies the demo flags, **fails closed**
   unless all 8 match their preregistered expected families.

`--compare` byte-compares the deterministic output set of two independent
runs. Preregistered determinism scope: everything from rasterization onward
(PNGs, all JSON) is byte-identical across runs; **kicad-cli PDF bytes are
not** (run-local metadata) and are recorded as provenance only. See
`SELFVERIFY-LOG.md` for the packaging-time double-run result.

## 5. Known limitations (stated honestly)

- **Instance heterogeneity / inter-dispatch instability.** The registered
  record shows the *same physical feature* can be abstained on by some
  reader dispatches and judged normal by others (e.g. the blackdot family
  alternated between abstain and judged-normal across dispatches for four
  consecutive rounds). Single-instance readings are demonstrably unstable
  (the r8→r10 abstention-rate swing that motivated v1.1); the multi-instance
  calibers (v1.1/v1.3) measure but do not eliminate this. Any reproduction
  should expect inter-instance spread, which is why aggregation and split
  reporting are mandatory.
- **Tool behavior self-selection.** Before the v1.2 rule, readers
  self-selected image preprocessing (8/12 dispatches crop/zoomed in
  r10/r11), which was the largest cross-round comparability confound. v1.2
  pins the instrument for *readers inside this program*; it cannot pin the
  tool behavior of arbitrary third-party models reproducing this kit. Any
  cross-program comparison must register and disclose the tool rule of its
  own readers.
- **Blackdot-family near-absence outside the development domain.** The
  rubric's blackdot vocabulary was frozen on development-round Chinese
  reader-raw where a recurring "black dot" render artifact existed. On
  other corpora (including the dev program's own holdout corpus) the family
  may have no counterpart at all; unhit abstention reasons fall into the
  residual class `other` and keywords are never extended post hoc
  (registered extrapolation caveat). Family *shares* from this rubric
  should not be read as universal defect taxonomies.
- **Render instrument variance.** kicad-cli PDF bytes are not
  cross-run-deterministic (raster output is); renders depend on kicad
  version; the default palette leaves bottom-view white ambiguity (white
  ink vs void white) that measurably feeds abstentions — the optional r14b
  recolor addresses it for bottom views but was developed probe-specific
  and is not part of the default pipeline (`color_legend.md`).
- **English corpora.** The rubric keyword tables are Chinese (the corpus
  language). The *algorithm* is language-independent; the *tables* are not.
  Reusers in other languages must freeze and register their own tables and
  run the analogous chain replay; this package gives the method, not a
  universal dictionary.

## 6. What is deliberately NOT in this package

- No frozen reader readings (`reader-raw` files), no GT files, no evidence
  excerpts — PR-2: release copies only; frozen readings stay in the working
  repo. The release carries registered *aggregate counts* only.
- No model, prompt, or agent definitions — the paper's model-involving
  layers are disclosed separately (see the paper's model-disclosure
  artifact); everything in this package is deterministic.
- No publication/upload action has been performed by packaging; this is a
  local release *candidate* directory only.

## 7. Dataset caliber and provenance

- The example board is **bm1** from the PCBBenchmarks board-level CC-BY-SA
  subset (dev-repo corpus `datasets/pcbbenchmarks-r1/`, retained with its
  license text; upstream: an Arduino-Mega-like benchmark board whose design
  files are Creative Commons Attribution Share-Alike — attribution Arduino,
  see `bm1.license.txt` in the source corpus). The example renders
  (`reference-output/*.png`) are derivatives of that board and are therefore
  shared under the same CC-BY-SA terms; all *code and protocol/rubric text*
  in this package is Apache-2.0. If your distribution cannot carry CC-BY-SA
  content, delete `render/example/reference-output/*.png` and re-run the
  chain on your own board.
- The registered rubric base chain (r13–r16) was produced on the dev
  program's internal Rev-C development boards — not on bm1; the corpus is
  not redistributed. The registered counts ship as aggregates in
  `rubric/abstain-rubric-r13-r16.json`.
- The dev-repo dataset tree is byte-frozen; the example chain verified
  zero writes into it at packaging time (file count and whole-tree
  aggregate hash unchanged; `SELFVERIFY-LOG.md`).
- Dataset splits mentioned nowhere here imply nothing about model training:
  this kit involves no training and no model calls.

## 8. Citing the version chain

When reusing the protocol templates, cite the version you executed plus the
amendments (see `protocol/EVOLUTION.md`). The two protocol files are frozen;
if your execution differs, register your amendment the same way the lineage
does — append-only, per-round preregistered, predecessor bytes preserved.
