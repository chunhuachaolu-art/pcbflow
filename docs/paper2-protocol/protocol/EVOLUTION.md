# Evaluation Protocol Evolution: v1 → v1.1 / v1.2 / v1.3 → v2

- artifact: paper2-protocol EVOLUTION record (PAPER-P2-3 release package)
- declared date (human constant, not machine wall-clock): 2026-09-12
- sources: the two shipped protocol files (byte copies), the dev-repo
  prep-records that registered each intermediate amendment, and the Paper 2
  terminology specification (paper-terminology-r1, 2026-09-11) from which the
  registered hashes below were taken and re-verified at packaging time.
- rule observed by the whole chain: a frozen protocol file is never edited;
  every revision is either a new version file or an amendment registered in a
  round prep-record, with the predecessor's bytes preserved and hash-pinned.

The shipped files:

| file | sha256 (verified at packaging) | role |
|---|---|---|
| `evaluation-protocol-v1.md` | `22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e` | development/calibration rounds governance (R1–R22 historical caliber), frozen 2026-09-06 |
| `evaluation-protocol-v2.md` | `365b67ef247ff2d664c620971fff21efc4ed684e55a2e99625823321669e0712` | independent frozen-holdout evaluation protocol, frozen 2026-09-10 |

---

## v1 — evaluation-protocol-v1 (frozen 2026-09-06)

Baseline text, frozen in place since declaration ("frozen from this round on;
later revisions = new version files, no write-back"). Six sections:

1. **Three-set split** — development / calibration / frozen evaluation
   (holdout explicitly *not established*, TBD behind human approval);
   "same board, different renders ≠ independent boards".
2. **Independent adjudication** — GT-ization of model output outside the
   seeds requires human or independent qualified adjudication; a model may
   never mint "human-confirmed" labels; un-adjudicated stays pending.
3. **Joint pass gate (APR-0011, provisional_supersedable)** —
   `gt_recall ≥ 0.75` AND `seed_match_rate ≥ 0.5` AND `abstain_rate ≤ 0.5`
   AND two consecutive rounds (different render batches) AND GT ≥ 12; joint
   evaluation (any miss = not passed); passing ≠ automatic routing.
4. **Per-round preregistration** — reader protocol (five-key projection +
   location_evidence), model/prompt version, metric version, GT set all
   frozen before blind reading; any post-hoc adjustment demotes the batch to
   development evidence.
5. **Per-view dispatch** — top/bottom blind reads dispatched separately.
6. **Naming constraints** — `seed_match_rate` must never be called
   precision/FPR; box hits are not electrical facts.

Reader instances: **one per view (n=1)**; rounds r3–r10 executed on this
semantics. The r8→r9→r10 abstention-rate swing (0.222→0.727→0.286) later
became the registered evidence that single-instance-per-round readings are
metrically unstable.

## v1.1 — multi-instance aggregation (registered in r11 prep-record, 2026-09-07)

- **Mode**: purely additive ("追加式"), registered as
  `protocol_amendment.amendment_version = "v1.1"` in
  `r11-prep-record.json` (dev repo, sha256 `9074df2d…`); v1 file untouched
  (zero-byte preservation verified in the prep record itself). No new
  protocol file was created — the amendment lives in the round record.
- **Change**: per view, 1 reader instance → **3 independent instances
  (i1/i2/i3)** (user-approved option (a), 2026-09-07). Blind reads per round
  became 12 = 4 view cells (2 board states × top/bottom) × 3 instances.
- **Aggregation caliber introduced**: instance-level records are primary;
  view level aggregates median/min/max; GT matching reports **union
  (≥1 instance) and agreement (≥2/3 instances) side by side, both reported
  honestly, no cherry-picking**; the joint gate is evaluated on a
  representative configuration with per-metric inter-instance ranges
  reported alongside.
- **Scope guard**: reading criteria, renders, GT, thresholds all unchanged;
  `in_calibrated_range` stays False.

## v1.2 — reader tool-behavior rule (registered in r12 prep-record, effective r12)

- **Mode**: additive, dispatch layer only; registered as
  `protocol_amendment.amendment_version = "v1.2"` in
  `r12-prep-record.json` (dev repo, sha256 `d393cf27…` measured at
  packaging time).
- **Motivation (registered)**: r10/r11 measurement showed 8/12 reader
  dispatches self-selected PIL crop-and-zoom preprocessing; the 0/4→8/12
  cross-round swing was the largest comparability confound. The rule pins
  the instrument.
- **Change**: every reader dispatch instruction from r12 on carries the hard
  clause — *reading may only view the original image via the Read tool
  (repeatable); any programmatic image processing (crop, zoom, pixel
  analysis, derived images) is forbidden*. Reading semantics, categories,
  GT, thresholds unchanged; only the input channel is fixed.
- **Longevity**: used unchanged r11-rounds→r22 (ten+ rounds); later
  inherited verbatim into v2's holdout execution caliber (v2 §0.3).

## v1.3 — n-expansion appendix (registered in r24 prep-record, 2026-09-10)

- **Mode**: additive appendix registered in
  `r24-prep-record.json` `protocol_amendment` (dev repo, sha256 `760af49f…`)
  as `multi-instance-protocol-v1.3-n-expansion-appendix`; protocol files
  v1/v1.1/v1.2 all inherited unchanged; v1 file zero-byte preserved
  (re-verified in the record). No new protocol file.
- **Change**: instances per view 3 → **6** (12 reader agents, 24 blind reads
  per round, two serial waves). Aggregation generalized to n=6: union =
  ≥1/6 instance hits; agreement = **≥4/6 majority** (generalization of
  v1.1's ≥2/3); joint-gate representative configuration = the
  flag_count-ascending 3rd-order (lower-median) instance per view.
- **Companion registration in the same record**: guard G1's operational
  restatement for n=6 ("six bottom instances all zero non-abstain courtyard
  flags") — direction unchanged, caliber follows the expansion.

## v2 — evaluation-protocol-v2 (frozen 2026-09-10, new version file)

- **What it is**: the independent evaluation protocol for the *future frozen
  holdout domain*, created as a new file (with
  `protocol-v2-registration.json`, dev repo sha256 `36cc86a7…`), approved
  via the user directive of 2026-09-10 executing the final recommendation
  "complete R20 close, then freeze the evaluation protocol and prepare the
  independent holdout".
- **Supersedes relationship (explicit, §0)**: v2 governs only future holdout
  evaluation; it does **not** retroactively touch any round evidence; v1
  stays byte-preserved and keeps carrying development/calibration rounds
  (including v1 §4 preregistration discipline). v1.1 multi-instance and
  v1.2 tool-behavior calibers are inherited verbatim as holdout execution
  caliber (§0.3) rather than re-versioned.
- **Core content — the P2 nine clauses** (§1, each numbered and frozen):
  P2-1 three sets isolated by board; P2-2 reader blindness to GT; P2-3
  one-to-one matching; P2-4 duplicate flags listed separately; P2-5
  unmatched / unadjudicated / true-false-positive three-way bookkeeping;
  P2-6 metrics reported separately (no single score); P2-7 per-flag human
  adjudication for at least part of results; P2-8 no promotion on tentative
  thresholds; P2-9 missing evidence ⇒ blocked. Any holdout result failing a
  clause cannot count as independent quality evidence.
- **One-time discipline inherited** (§2): holdout boards are
  holdout-candidates from plan registration; no blind reading, no guidance
  iteration may touch their renders before the official run; renders happen
  once, with the pipeline frozen. v2 freezing ≠ holdout start (§4.5) — the
  start is an independent human decision point.
- **Status quo registration** (§3): r19 marginal, r20 reject with the G1
  bifurcation record, r22 regressed with the G2 bifurcation record — letter
  verdicts and mechanism observations kept as separate books, never merged.
- **Boundary declarations** (§4): TL gates unchanged; APR-0011 thresholds
  unchanged; `in_calibrated_range` stays False until formal adoption;
  automatic routing stays blocked; V4-SVG is a separate route.

---

## Lineage summary table

| version | date | carrier | change | registered in (dev repo) |
|---|---|---|---|---|
| v1 | 2026-09-06 | `evaluation-protocol-v1.md` | baseline: three-set split, independent adjudication, APR-0011 joint gate, preregistration, per-view dispatch, naming constraints | the file itself (`22dc7337…`) |
| v1.1 | 2026-09-07 | in-record appendix | n=1 → n=3 instances per view; instance-primary aggregation; union/agreement dual GT recall; representative-config gate | `r11-prep-record.json` `protocol_amendment` (`9074df2d…`) |
| v1.2 | from r12 | in-record appendix, dispatch layer | tool-behavior rule: Read-only original-image viewing, no programmatic image processing | `r12-prep-record.json` `protocol_amendment` |
| v1.3 | 2026-09-10 | in-record appendix | n=3 → n=6 per view; union ≥1/6, agreement ≥4/6; lower-median representative config | `r24-prep-record.json` `protocol_amendment` (`760af49f…`) |
| v2 | 2026-09-10 | `evaluation-protocol-v2.md` | frozen-holdout protocol: P2 nine clauses, one-time discipline, supersedes/boundary declarations; inherits v1.1+v1.2 calibers | the file itself (`365b67ef…`) + `protocol-v2-registration.json` |

**Reading rule for reusers.** v1 and v2 are the only protocol *files*; v1.1,
v1.2 and v1.3 are registered amendments that modify execution caliber without
rewriting any file. When citing "the protocol", cite the file that governs
your domain (v1 for development/calibration practice; v2 for independent
holdout practice) together with the amendment versions your execution
actually used. Reproducing any round's numbers requires the round's own
prep-record criteria, which are versioned per round and never retro-edited.
