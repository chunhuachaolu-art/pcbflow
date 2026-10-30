"""V4.2 model seat experiment package (inspector seat + intent-level constraint seat).

Taskbook: exec/V4.2-MODEL-SEAT-EXPERIMENT-TASKBOOK-2026-09-13.md (frozen,
ADJUDICATION-2026-09-12.md §13 R35/R36).

Scope discipline (taskbook §2.2): pcbflow/v4exp/ and every other listed
read-only module are imported read-only; nothing here mutates frozen v4exp
semantics or files.  M0 probe deliverables in this package:

- mirror.py : P0-a -- v4exp solver mirror with cost-bias / hard-keepout
  injection hooks; byte-parity with v4exp.router.solve_board when both
  hooks are empty (parity enforced over the full reuse scenario set);
- leg.py    : P0-b -- subnet re-solve leg: fixed non-deleted nets as
  existing copper + re-solve deleted nets (B8 route_one_added semantics
  ported to the synthetic domain).

Tested-model (GLM-5.3-Flash) plumbing is orchestration-side only: network
I/O never enters solver/validator core paths, and no key material may be
written into any artifact under out/.
"""

SCHEMA_NAMESPACE = "pcbflow.v4_2"
