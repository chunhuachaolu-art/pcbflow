# STM32H743 Core Board — Rev-C (`stm32h743-coreboard-revc`)

> **Archive note (2026-10-30).** This board is published as part of the
> [pcbflow final archive](../../README.md) under `design/coreboard/`.
> Paths in this README are relative to this directory. The citation and
> DOI are the pcbflow archive's (see `../../CITATION.cff`); the separate
> per-board DOI mentioned in §7 was not minted. `reports/` holds the
> routing/placement specs the pcbflow compiler reads, plus the Rev-C delivery report and the lessons-learned record.


Open-source release of the **STM32H743 SoM core board, revision C**:
KiCad 10 project (schematic + PCB + project config + symbol/footprint
libraries), generated netlist, public bill of materials, and pin-map
design documentation.

> **Status banner (read this first):** this board is released as an
> **auditable dry-run + replay design**, with
> **`production_signoff_ready = false`**. It has **not** been sent to a
> board house, **not** been fabricated, **not** been assembled, and
> **not** been brought up. Do **not** treat it as a
> production-validated board. Details in §2.

---

## 1. Board overview

| Item | Value |
| --- | --- |
| MCU | STMicroelectronics **STM32H743IIT6**, LQFP176, Cortex-M7 @ up to 480 MHz |
| Form factor | 70 × 70 mm SoM-style core board, 4-layer (F.Cu / In1.Cu GND / In2.Cu power / B.Cu) |
| Expansion | 4 × 2.54 mm 2×20 headers: J1 storage (QSPI/SDMMC), J2 comms (RMII), J3 display+audio (RGB565 LTDC / SAI2 / I2C), J4 debug+system (CAN/ADC/SWD/power) |
| On-board SDRAM | 16-bit / 16 MB, IS42S16160J-6BLI (TSOP-54), FMC @ up to 100 MHz |
| USB | FS Type-C device (USBLC6-2SC6 ESD protect, CC 5.1k pulldowns, polyfuse) |
| Display | RGB565 LTDC, 16-bit high-aligned (R3–R7 / G2–G7 / B3–B7) |
| Ethernet | RMII (REF_CLK 50 MHz supplied by carrier-board PHY) |
| CAN | FDCAN1 (FDCAN2 dropped — LQFP176 mux conflict, no solution) |
| Power | 5 V in → TPS62085 buck (3.3 V @ 3 A class) + LP5907 LDO for VDDA; supercap VBAT backup chain (BAT54J + 220R + 0.22 F) |
| Clocks | HSE 25 MHz, LSE 32.768 kHz |
| Debug | SWD (J4), USART1 console, USER button (PC13), user LED (PG9), power LED |

Repository layout:

```
kicad/stm32h743-coreboard-revc/   KiCad 10 project (sch, pcb, pro,
                                  2 symbol libs, 1 footprint lib,
                                  fp/sym-lib-tables, revc.netlist)
bom/                              public BOMs (Rev-C build + Rev-B record)
pinmap/                           pin-map & design-reference docs (zh)
tools/                            verification script (see §8 scope note)
LICENSE (layering), LICENSE.BOARD (CERN-OHL-P-2.0),
LICENSE.SCRIPTS (Apache-2.0)
```

---

## 2. Design status — what is and is not claimed

**What this release IS:**

- A complete, self-contained, **openable** KiCad 10 project (verified
  with kicad-cli 10.0.5; ERC/DRC reproduce, see §3).
- A board whose routing/verification history went through an
  **auditable dry-run + replay closure**: a pre-registered protocol
  with deterministic net selection, batched restricted edit actions,
  **paired DRC baselines** (baseline vs challenger on a snapshot whose
  SHA-256 is pinned at every step), a **mandatory rollback drill**
  (mutate → assert changed → restore → assert byte-identical → re-run
  DRC), and fail-closed gates (any gate failure = whole batch rolled
  back). Every DRC number quoted in §3 is reproducible from the files
  in this repository with the stated commands.

**What this release is NOT:**

- **`production_signoff_ready = false`.** No fab submission, no
  fabrication, no assembly, no bring-up, no electrical test, no
  board-house DFM review has happened. The 220
  severity-error / 55 unconnected DRC baseline in §3 is the honest
  current state of the artwork — it is published as-is for
  reproducibility, not as a clean-production claim.
- Consequently: **do not order boards from these files and do not use
  this as a production-validated reference** without doing your own
  full verification loop first.

---

## 3. Verification baseline (reproducibility)

Tool identity: **kicad-cli 10.0.5** (KiCad 10.0.x; the netlist header
records `Eeschema 10.0.5`). All numbers below were measured with that
toolchain.

### 3.1 Published DRC baseline — standalone-board caliber

The published baseline was taken on the board file **standalone**
(copied into a directory *without* the `.kicad_pro`, so KiCad default
severities apply). The shipped
`kicad/stm32h743-coreboard-revc/stm32h743-coreboard-revc.kicad_pcb` is
**byte-identical** to that baseline snapshot:

`sha256 = dbfea0895301ade8209701ef93545b26ca35ef49a9b7116032d917db79e1a791`

Measured baseline (and what you should get when reproducing):

| Run | violations | breakdown | unconnected items |
| --- | --- | --- | --- |
| `--severity-error` | **220** | 220 error | **55** |
| `--severity-all` | **340** | 220 error + 120 warning | **55** |

Reproduce (verified commands):

```
mkdir drc-run
cp kicad/stm32h743-coreboard-revc/stm32h743-coreboard-revc.kicad_pcb drc-run/
cd drc-run
kicad-cli pcb drc --format json --severity-error --output drc-error.json stm32h743-coreboard-revc.kicad_pcb
kicad-cli pcb drc --format json --severity-all   --output drc-all.json   stm32h743-coreboard-revc.kicad_pcb
```

### 3.2 In-project caliber (project severities, as shipped)

Running DRC **inside** `kicad/stm32h743-coreboard-revc/` (where the
project file `.kicad_pro` sits next to the board and its severity
configuration applies) gives different — lower — totals:

| Run | violations | breakdown | unconnected items |
| --- | --- | --- | --- |
| `--severity-error` | 16 | 16 error | 55 |
| `--severity-all` | 141 | 16 error + 125 warning | 55 |

```
cd kicad/stm32h743-coreboard-revc
kicad-cli pcb drc --format json --severity-error --output drc-error.json stm32h743-coreboard-revc.kicad_pcb
kicad-cli pcb drc --format json --severity-all   --output drc-all.json   stm32h743-coreboard-revc.kicad_pcb
```

Both calibers are the same copper; only the severity classification
differs. The 55 unconnected items are identical in count in both
calibers. (The *membership* of the unconnected set can differ slightly
between any two kicad-cli runs, including two runs on the same input —
this is kicad-cli ratsnest nondeterminism, observed during packaging;
the **count** is stable and is what the baseline pins.)

### 3.3 ERC

```
cd kicad/stm32h743-coreboard-revc
kicad-cli sch erc --format json --output erc.json stm32h743-coreboard-revc.kicad_sch
```

Expected: **0 errors, 1 warning** — U3 (TPS62085) `lib_symbol_mismatch`
(a known, pre-existing symbol/library divergence; it is present in the
baseline and is not introduced by this packaging).

### 3.4 Netlist ↔ board consistency (spot-checked at packaging)

- Netlist: 79 components (72 physical + 7 `PWR_FLAG`), 19 libparts.
- PCB: 72 footprints (matches the 72 physical netlist components),
  192 named nets.
- The **set of 192 net names is exactly equal** between `revc.netlist`
  and the PCB.

### 3.5 BOM

`bom/purchase-list.csv` (Rev-C build) and `bom/purchase-list-revb.csv`
(Rev-B record) ship with public columns only
(`序号 / 类别 / 位号 / 型号 / 封装/规格 / 需求数量`). Supplier,
pricing and internal-note columns were deliberately removed in this
release (they contained procurement data). Part numbers are public
manufacturer part numbers.

---

## 4. Known breakpoints (honest known-issues list)

1. **U1↔U2 layout saturation.** The U1 (LQFP176) ↔ U2 (TSOP-54)
   channel was measured at **1.07 mm** silicon-to-silicon gap while
   ~45 FMC/net buses must cross it — a **structural layout
   constraint**, diagnosed as the root cause of the unfinished routing
   (recorded in the project delivery report; the Rev-C routing
   campaign independently confirmed corridor saturation). This is a
   layout problem, not a tooling gap; fixing it means a re-layout.
2. **55 unconnected items at baseline.** Direct consequence of (1).
   They are part of the published baseline (§3), not hidden.
3. **U3 `lib_symbol_mismatch` ERC warning** (§3.3) — pre-existing.
4. An earlier internal planning note cited "57 unconnected" for the
   headless baseline; the measured, published baseline on the pinned
   snapshot is **55** — use the measured number.

---

## 5. AI participation disclosure (pointer)

The routing and verification pipeline that produced this board was
heavily **AI-agent-assisted** (LLM-driven routing agents under
deterministic, hash-chained, human-auditable protocols). Per-project AI
usage statistics, protocol details, and the honesty/disclosure
framework are published in the **AI-disclosure sections of the two
papers** that cite this artifact (§7) and in their accompanying
artifact packages — not duplicated here. The design-verification facts
in this README (§3–§4) are all kicad-cli measurements reproducible from
this repository alone.

---

## 6. License

Layered licensing (see `LICENSE` for the full hierarchy statement):

- **Board design files & design documentation** (`kicad/**`, `bom/**`,
  `pinmap/**`): **CERN Open Hardware Licence v2 - Permissive**
  ([CERN-OHL-P-2.0](https://ohwr.org/cern_ohl_p_v2.txt)) — full text in
  `LICENSE.BOARD`.
- **Scripts & repository metadata** (`tools/**`, `README.md`,
  `LICENSE*`): **Apache License 2.0** — full text in `LICENSE.SCRIPTS`.

Third-party datasheets are **not** redistributed (copyright stays with
ISSI/Winbond) — see §8.

---

## 7. Citing this artifact / papers

If you use this board or this artifact, please cite the corresponding
paper (both papers share this single artifact provenance) and the
archived artifact version:

- **Paper 1** — controlled empirical study of LLM participation in an
  SVG-codified PCB routing pipeline (auditable, rollback-able,
  replayable route packages; representation vs planning placement of
  the model in the loop).
- **Paper 2** — measurement-science study of multimodal PCB-defect
  readers (pre-registered blind-read calibration metrology).

BibTeX (DOI placeholders — both DOIs are **pending Zenodo; they will be
minted at the first public release** and substituted here; until then
the placeholder string is authoritative):

```bibtex
@misc{stm32h743-coreboard-revc-artifact,
  title  = {stm32h743-coreboard-revc: open-source STM32H743 SoM core
            board (Rev-C) artifact},
  note   = {CERN-OHL-P-2.0 (board) / Apache-2.0 (scripts);
            DOI: pending Zenodo, minted at first public release},
  year   = {2026}
}
```

---

## 8. Disclosures (packaging decisions you should know about)

1. **Net names and reference designators are real design
   identifiers.** The PCB carries **192 net names** and the schematic
   **509 global labels**; all are functional names (`3V3`, `USB_DM_C`,
   `FDCAN1_TX`, `FMC_BA1`, `BTN_USER`, `LED_USER`, ...). They are kept
   as-is: this is the user's own open-source board design, and the
   names are required for the design to make sense.
2. **Tool identity strings are kept on purpose** (`Eeschema 10.0.5`,
   `generator_version 10.0`, kicad-cli 10.0.5 in verification records)
   as reproducibility evidence for §3.
3. **Board naming convention.** The board name
   `stm32h743-coreboard-revc` is the publication identifier. Title
   blocks carry no company/author/date fields anywhere in this
   release.
4. **Datasheets are linked, not shipped.** The ISSI IS42S16160J and
   Winbond W9825G6KH datasheets are third-party copyrighted documents;
   references inside `pinmap/` and the `Datasheet` fields were
   rewritten to public citations ("obtain from vendor site"). Do not
   expect those files inside this repository.
5. **`tools/verify_revb_u2_bga.py` scope note.** This is the Rev-B era
   U2-BGA verification script, kept as verification-history
   provenance. It references the Rev-B project tree, which is **not**
   part of this release — as shipped it will not run against this
   repository's files. Its content checks (documented in the script)
   all hold against the shipped `pinmap/pinmap-revb.md` and
   `bom/purchase-list-revb.csv`.
6. **Documentation language.** `pinmap/` documents are in Chinese.
   They are design-input records from their writing time (the Rev-B
   working document explicitly says so); where they and the board
   files disagree, **the board files are authoritative**. Internal
   route codenames, internal sign-off dates and workspace paths were
   removed from the release copies; the engineering content was kept.
7. **Session state excluded.** KiCad `.kicad_prl` view-state files,
   routing scratch/sessions, internal reports, archives of superseded
   revisions, and VCS metadata are intentionally excluded from this
   release; KiCad regenerates `.kicad_prl` as needed.
