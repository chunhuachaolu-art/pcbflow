"""A4-INTENTPACK-R1 (REP-R1) engineering package: B-arm structured intent
pack generator + A-arm extraction + self-verification.

Frozen contracts (read-only inputs to this package):
- out/v4.2-rep-r1/PACK-SPEC-REP-R1.md  v1 2026-09-30 (pack format authority)
- out/v4.2-rep-r1/PREREG-REP-R1.md     v1 2026-09-30 (template texts §12,
  blinding/forbidden-token lists §11)
- pcbflow/v4_2/inspector.py            (judge contract, blind, assign_pids)
- pcbflow/v4_2/gt.py                   (frozen solver entry incumbent_run)

This module never writes outside out/v4.2-rep-r1/ and imports the modules
above read-only.  Deterministic: no wall-clock, no randomness, no host
paths inside any produced content (same input -> same output bytes).
"""

from pcbflow.v4_2_rep.packgen import (
    FORBIDDEN_TOKENS,
    FROZEN_USER_BYTES,
    MAX_SEGMENTS,
    SEGMENT_CODES,
    USER_BYTE_LIMIT,
    USER_BYTE_TARGET,
    arm_a_tasks,
    build_pack,
    build_user_text,
    generate_all,
    parse_user_text,
    replay_occupancy,
    rle_decode,
    rle_encode,
    scenario_sid_paths,
    verify_pack_text,
)

__all__ = [
    "FORBIDDEN_TOKENS", "FROZEN_USER_BYTES", "MAX_SEGMENTS", "SEGMENT_CODES",
    "USER_BYTE_LIMIT", "USER_BYTE_TARGET", "arm_a_tasks", "build_pack",
    "build_user_text", "generate_all", "parse_user_text", "replay_occupancy",
    "rle_decode", "rle_encode", "scenario_sid_paths", "verify_pack_text",
]
