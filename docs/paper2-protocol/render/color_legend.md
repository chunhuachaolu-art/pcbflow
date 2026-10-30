# Render color rules and legend (r5 framework pipeline + r14b recolor)

This document records the visual instrument (color) conventions of the
evaluation renders, so that a reproduced render is recognizable against the
rounds the protocol describes. Two configurations exist:

## 1. Default pipeline (kicad default palette, zero overlay)

Used by the official development-round renders from r5 onward (registered in
`render-framing-r5.json` in the dev repo) and by ALL official independent
holdout renders (`s92_holdout_render_r1.py`; dev repo). Colors are whatever
kicad-cli emits for the exported layer set; no post-processing.

Layer sets (frozen constants of the pipeline):

| view   | layers                                    | mirror |
|--------|-------------------------------------------|--------|
| top    | F.Cu, F.Mask, F.Silkscreen, Edge.Cuts, F.Courtyard | no  |
| bottom | B.Cu, B.Mask, B.Silkscreen, Edge.Cuts, B.Courtyard | yes |

Geometry: dpi 640, 40 pt white compose margin, crop = board pixel bounds +
120 px margin on all four sides.

Observed base canvas colors on the development renders (kicad 10 defaults;
recorded in r14b probe evidence):

| name            | RGB           | typical carrier |
|-----------------|---------------|-----------------|
| copper blue     | (77,126,195)  | B.Cu / F.Cu fills and traces |
| mask cyan       | (153,255,248) | B.Mask / F.Mask openings |
| edge gray       | (207,209,205) | Edge.Cuts outline |
| canvas white    | (255,255,255) | background AND white ink (ambiguous) |

## 2. r14b white-disambiguation recolor (optional, bottom views only)

Registered as a single-variable instrument change in
`render-framing-r14b.json` (dev repo) after a probe falsified the first
attempt (r14): on the bottom view, pure white pixels had two distinct
sources that readers could not tell apart, which pushed abstentions:

- (a) white INK vector drawings — pad hole disks (`--drill-shape-opt 2`)
  and pad outlines, a shared drawing family emitted on both B.Cu and
  B.Mask single-layer exports, drawn once on top of copper/mask in the
  combined PDF, no OCG layer marks;
- (b) board-interior VOID white — copper clearance gaps, wing/fan shapes,
  board-frame retreat bands, fiducial ring gaps: absence of ink, not a
  drawing.

Recolor rule (binary mask full replacement, no alpha blending):

| mask (rebuilt from combined PDF vectors)          | target RGB    | semantics                |
|---------------------------------------------------|---------------|--------------------------|
| white fills + white strokes (ink drawings)        | orange (255,165,0) | pad hole disks / pad outlines |
| board bounds x pure white x NOT white ink         | green (0,128,0)    | substrate void white (clearance gaps etc.) |

Preregistered assertion: every target color must have RGB Euclidean
distance > 150 from every canvas base color (verified in code:
`render_reproduce.py --recolor-r14b`).

Legend as used in reader guidance from round r14b/r15 onward (the "5A
instrument annotation"): *orange = white ink drawing (pad-related metal
shapes); green = substrate/void white; all other colors = kicad default
layer palette.* Readers were told the legend but instructed to judge
independently of it (the annotation describes the instrument, not the
verdict).

## Honest scope limitation

The r14b recolor was developed as a Rev-C probe-specific instrument change
and was NOT generalized: official holdout renders deliberately use the
default palette, and the limitation "bottom-view white ambiguity is a
potential abstention-rate upward factor under the default palette" was
preregistered in the holdout framing. This package ships the recolor as a
deterministic optional stage (`--recolor-r14b`), not as part of the default
pipeline, and the example chain runs with the default palette.
