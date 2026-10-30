"""从钉死的本地 CubeMX DB XML 转写 STM32H743IITx（LQFP176）AF 全表。

源包（out/revc-fd1/approvals/sources/mcu-af-table.json）钉的 GitHub
STM32CubeH7 db/mcu/IP 路径在官方仓库不存在（db/ 只随 CubeMX 软件分发，
GitHub API contents 404 证据）；本脚本改从本机官方 STM32CubeMX 安装库的
同一 CubeMX XML 源转写（已拷贝到 out/revc-af/sources/ 并记 hash），偏差
登记于 af-verification.json / PHASE-REPORT-13。

stdout 输出 canonical JSON（mcu-af-table-full.json 本体），进度/统计走
stderr；无 wall-clock（元数据在 run manifest 与核验记录里）。

用法：python scripts/gen_af_table.py > out/revc-af/mcu-af-table-full.json
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET

PCBFLOW = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PCBFLOW)

from pcbflow import hashing  # noqa: E402

SOURCES = os.path.join(PCBFLOW, "out", "revc-af", "sources")
CHIP_XML = "STM32H743IITx.xml"
MODES_XML = "GPIO-STM32H747_gpio_v1_0_Modes.xml"
_AF_RE = re.compile(r"GPIO_AF(\d+)")
_PIN_BASE_RE = re.compile(r"(P[OA-I][0-9]{1,2}_?C?|[A-Z]+[0-9]+)")


def localname(tag):
    return tag.split("}")[-1]


sha256_file = hashing.sha256_file  # REPAIR-P3 W-4 正身收编（等价验证在案）


def parse_chip(path):
    root = ET.parse(path).getroot()
    attrs = {k: root.get(k) for k in ("RefName", "Family", "Line", "Package",
                                      "DBVersion")}
    pins = []
    for el in root.iter():
        if localname(el.tag) != "Pin" or el.get("Position") is None:
            continue
        raw = el.get("Name")
        # 部分引脚名带功能注记（PC14-OSC32_IN (OSC32_IN)、PA13 (JTMS/SWDIO)），
        # 仅对带注记（含 '(' 或 '-'）的名字归一化为基本名；电源等其余名保持
        # 原样（VDD33_USB 不得截成 VDD33）；原始名保留 name_chip_xml 供追溯
        name = raw
        if "(" in raw or "-" in raw:
            head = raw.split(" (")[0].split("-")[0]
            m = _PIN_BASE_RE.match(head)
            if m:
                name = m.group(1)
        signals = []
        eventout = False
        for s in el.iter():
            if localname(s.tag) != "Signal" or not s.get("Name"):
                continue
            signals.append(s.get("Name"))
            if s.get("Name") == "GPIO" and "EVENTOUT" in \
                    (s.get("IOModes") or "").split(","):
                eventout = True
        # DS12110 AF 表把 EVENTOUT 列为 AF 列内容；芯片 XML 里它只出现在
        # GPIO 伪信号的 IOModes 属性，转写为显式 AF15 条目（RM 约定 AF15）
        if eventout:
            signals.append("EVENTOUT")
        pins.append({"position": int(el.get("Position")), "name": name,
                     "name_chip_xml": raw, "type": el.get("Type"),
                     "signals": sorted(signals)})
    ip_gpio = next(el for el in root.iter()
                   if localname(el.tag) == "IP" and el.get("Name") == "GPIO")
    ionb_el = next(el for el in root.iter() if localname(el.tag) == "IONb")
    attrs["io_nb"] = int(ionb_el.text)
    attrs["gpio_ip_version"] = ip_gpio.get("Version")
    return attrs, pins


def parse_modes(path):
    """(port, pin) → {signal: af_number}；同信号多 AF 值记最小并计数告警。"""
    root = ET.parse(path).getroot()
    af_map = {}
    multi = []
    for gp in root.iter():
        if localname(gp.tag) != "GPIO_Pin":
            continue
        pname = gp.get("Name")
        for ps in gp.iter():
            if localname(ps.tag) != "PinSignal":
                continue
            sig = ps.get("Name")
            afs = []
            for pv in ps.iter():
                if localname(pv.tag) == "PossibleValue" and pv.text:
                    m = _AF_RE.search(pv.text)
                    if m:
                        afs.append(int(m.group(1)))
            if not afs:
                continue
            if len(set(afs)) > 1:
                multi.append((pname, sig, sorted(set(afs))))
            af_map.setdefault(pname, {})[sig] = min(afs)
    return af_map, multi


def main():
    chip_path = os.path.join(SOURCES, CHIP_XML)
    modes_path = os.path.join(SOURCES, MODES_XML)
    meta, pins = parse_chip(chip_path)
    af_map, multi_af = parse_modes(modes_path)

    positions = sorted(p["position"] for p in pins)
    if positions != list(range(1, 177)):
        raise SystemExit("chip XML positions != 1..176: %d pins" % len(pins))

    pins_out = []
    no_af = 0
    for p in sorted(pins, key=lambda r: r["position"]):
        pmap = af_map.get(p["name"], {})
        sigs = []
        for s in p["signals"]:
            af = pmap.get(s)
            if s == "EVENTOUT" and af is None:
                af = 15
                sigs.append({"signal": s, "af": af,
                             "af_basis": "chip_xml_iomodes_af15"})
                continue
            if af is None:
                no_af += 1
            sigs.append({"signal": s, "af": af})
        pins_out.append({"position": p["position"], "name": p["name"],
                         "type": p["type"], "signals": sigs})

    table = {
        "schema_version": "1.0",
        "artifact_kind": "mcu_af_table_full",
        "spec_ref": "SPEC v1.3 §8.4（pin-swap）/§13.2 V2（文本双源核验）；"
                    "源包 out/revc-fd1/approvals/sources/mcu-af-table.json "
                    "transcription_plan 步骤①",
        "transcriber": "tools/pcbflow/scripts/gen_af_table.py",
        "mcu": {
            "ref_name": meta["RefName"], "family": meta["Family"],
            "line": meta["Line"], "package": meta["Package"],
            "db_version": meta["DBVersion"], "io_nb": meta["io_nb"],
            "gpio_ip_version": meta["gpio_ip_version"],
            "pin_count": len(pins_out),
        },
        "source_files": [
            {"file": CHIP_XML, "sha256": sha256_file(chip_path),
             "role": "primary_machine_official（封装/引脚/信号描述符）"},
            {"file": MODES_XML, "sha256": sha256_file(modes_path),
             "role": "primary_machine_official（AF 编号定义）"},
            {"note": "来源路径、取回方式与源基准偏差登记见 af-verification.json"},
        ],
        "pins": pins_out,
    }
    data = hashing.canonical_json_bytes(table)
    sys.stdout.buffer.write(data)

    print("pins=%d io_nb=%d signals_no_af=%d multi_af_signals=%d "
          "sha256=%s" % (len(pins_out), meta["io_nb"], no_af, len(multi_af),
                         hashlib.sha256(data).hexdigest()[:16] + "…"),
          file=sys.stderr)
    if multi_af:
        print("multi-AF (min taken): %s" % multi_af[:10], file=sys.stderr)


if __name__ == "__main__":
    main()
