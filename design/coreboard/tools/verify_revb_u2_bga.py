from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMATIC = ROOT / "kicad" / "stm32h743-coreboard-revb" / "stm32h743-coreboard-revb.kicad_sch"
SYMBOL_LIBRARY = ROOT / "kicad" / "stm32h743-coreboard-revb" / "coreboard-revb-memory.kicad_sym"
PINMAP = ROOT / "pinmap" / "pinmap-revb.md"
BOM = ROOT / "bom" / "purchase-list-revb.csv"


def require(text: str, needle: str, source: Path) -> None:
    if needle not in text:
        raise AssertionError(f"{source.name} missing: {needle}")


def current_u2_instance(schematic: str) -> str:
    match = re.search(
        r'\(symbol\s+\(lib_id "coreboard-revb-memory:IS42S16160J_6BLI_BGA54"\).*?\n\t\)',
        schematic,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("U2 does not use the Rev-B BGA54 symbol instance")
    return match.group(0)


def main() -> int:
    schematic = SCHEMATIC.read_text(encoding="utf-8")
    symbol = SYMBOL_LIBRARY.read_text(encoding="utf-8")
    pinmap = PINMAP.read_text(encoding="utf-8")
    bom = BOM.read_text(encoding="utf-8")
    u2 = current_u2_instance(schematic)

    require(u2, "IS42S16160J-6BLI", SCHEMATIC)
    require(
        u2,
        "Package_BGA:Alliance_TFBGA-54_8x8mm_Layout9x9_P0.8mm",
        SCHEMATIC,
    )
    require(u2, "42_45S83200J_16160J-462626.pdf", SCHEMATIC)
    require(
        u2,
        "256Mb Synchronous DRAM, 16M x 16 b x 4 Banks",
        SCHEMATIC,
    )
    if "Memory_RAM:IS42S16400J-xC" in u2:
        raise AssertionError("U2 still uses the incompatible 64 Mb TSOP symbol")
    if "Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm" in u2:
        raise AssertionError("U2 still uses the incompatible TSOP-II-54 footprint")

    for ball, signal in {
        "G1": "A12",
        "F2": "CLK",
        "F3": "CKE",
        "F7": "~{CAS}",
        "F8": "~{RAS}",
        "F9": "~{WE}",
        "E8": "DQML",
        "F1": "DQMH",
    }.items():
        require(symbol, f'(number "{ball}"', SYMBOL_LIBRARY)
        require(symbol, f'(name "{signal}"', SYMBOL_LIBRARY)

    require(pinmap, "FMC_A12", PINMAP)
    require(pinmap, "PG2", PINMAP)
    require(bom, "IS42S16160J-6BLI", BOM)
    require(bom, "TFBGA54", BOM)
    print("PASS: Rev-B U2 uses the verified IS42S16160J-6BLI BGA54 identity and documents the A12 path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
