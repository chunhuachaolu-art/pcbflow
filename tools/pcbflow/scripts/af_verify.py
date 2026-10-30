"""AF 转写 V2 双源核验记录（SPEC v1.3 §13.2 V2 摄入加速器）。

对 out/revc-af/mcu-af-table-full.json 做：
  1) stm32-data-generated 逐脚名核对（176/176）；
  2) 板上 U1 锚点核对（源包 sample_rows + GPIO_PXX/unconnected 网名↔引脚名）；
  3) U1 网名识别覆盖率（pcbflow.af_table.identify_net）；
  4) DS12110 PDF AF 表抽样 diff（信号名集合相等=pass；AF 编号列序仅
     report-only 佐证，不进门）。
源基准偏差（GitHub 无 db/ → 本机 CubeMX 安装库）一并登记。

stdout 输出 canonical JSON（af-verification.json），进度走 stderr。
用法：python scripts/af_verify.py > out/revc-af/af-verification.json
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys

PCBFLOW = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PCBFLOW)

from pcbflow import af_table, config, geo, hashing  # noqa: E402

AF_DIR = os.path.join(PCBFLOW, "out", "revc-af")
TABLE_PATH = os.path.join(AF_DIR, "mcu-af-table-full.json")
SOURCES = os.path.join(AF_DIR, "sources")
PACKAGE_JSON = os.path.join(AF_DIR, "sources", "STM32H743II.stm32data.json")
PDF_PATH = os.path.join(AF_DIR, "sources", "DS12110-stm32h743ii.pdf")
SOURCE_PACKAGE = os.path.join(PCBFLOW, "out", "revc-fd1", "approvals",
                              "sources", "mcu-af-table.json")
SAMPLE_PINS = [1, 3, 8, 9, 24, 26, 33, 40, 55, 64, 72, 90, 103, 118, 133,
               144, 157, 166, 172, 176]
_PUNCT_RE = re.compile(r"[^A-Z0-9]+")


def norm(s):
    return _PUNCT_RE.sub("", (s or "").upper())


sha256_file = hashing.sha256_file  # REPAIR-P3 W-4 正身收编（等价验证在案）


def board_u1_pads():
    b = geo.parse_board(config.AUDIT_P3_BOARD)
    pads = [{"num": int(p["num"]), "net": p["net"]}
            for p in b["pads"] if p.get("ref") == "U1"]
    return b, pads


# ---- 1) stm32-data 交叉核对 ---------------------------------------------------
def crosscheck_stm32data(table_pins_by_pos):
    with open(PACKAGE_JSON, encoding="utf-8") as f:
        data = json.load(f)
    pkg = next(p for p in data["packages"] if p["name"] == "STM32H743IITx")
    mism = []
    checked = 0
    for pin in pkg["pins"]:
        pos = int(pin["position"])
        their = pin["signals"][0] if pin["signals"] else None
        ours = table_pins_by_pos[pos]["name"]
        checked += 1
        if their != ours:
            mism.append({"position": pos, "stm32data": their, "table": ours})
    return {"source": "STM32H743II.stm32data.json（embassy-rs/"
                      "stm32-data-generated；机读，自 CubeMX XML 生成）",
            "package": "STM32H743IITx", "positions_compared": checked,
            "mismatches": mism, "pass": not mism}


# ---- 2) 板上锚点核对 ----------------------------------------------------------
def crosscheck_board_anchor(table_pins_by_pos):
    with open(SOURCE_PACKAGE, encoding="utf-8") as f:
        pkg = json.load(f)
    _, pads = board_u1_pads()
    by_num = {p["num"]: p["net"] for p in pads}
    anchors = []
    for row in pkg["board_anchor"]["sample_rows"]:
        got = by_num.get(int(row["pin"]))
        anchors.append({"pin": row["pin"], "expected_net": row["net"],
                        "board_net": got, "pass": got == row["net"]})
    checked = 0
    mism = []
    for p in pads:
        net = p["net"] or ""
        m = re.match(r"^GPIO_(P[A-K][0-9]{1,2}C?)$", net)
        if not m:
            m2 = af_table._UNCONNECTED_RE.match(net)
            if not m2:
                continue
            encoded = m2.group(1)
        else:
            encoded = m.group(1)
        checked += 1
        ours = table_pins_by_pos[p["num"]]["name"]
        if norm(encoded) != norm(ours):
            mism.append({"position": p["num"], "net": net,
                         "encoded": encoded, "table_pin": ours})
    return {"board": "p3-placement-gates-pass 快照（只读）",
            "u1_pads": len(pads),
            "anchor_samples": anchors,
            "gpio_name_consistency": {"checked": checked, "mismatches": mism},
            "pass": all(a["pass"] for a in anchors) and not mism}


# ---- 3) 识别覆盖率 ------------------------------------------------------------
def identification_coverage(table_pins_by_pos):
    _, pads = board_u1_pads()
    kinds = {}
    unidentified = []
    mismatches = []
    identified_signals = []
    for p in pads:
        r = af_table.identify_net(p["net"],
                                  table_pins_by_pos[p["num"]]) \
            if p["net"] else {"kind": "unidentified", "signal": None}
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        if r["kind"] in ("exact", "punct_norm") and r["signal"]:
            identified_signals.append(r["signal"])
        if r["kind"] == "unidentified" and p["net"]:
            unidentified.append(p["net"])
        if r["kind"] == "gpio_mismatch":
            mismatches.append({"position": p["num"], "net": p["net"]})
    return {"pads_total": len(pads), "kinds": dict(sorted(kinds.items())),
            "unidentified_nets": sorted(unidentified), "mismatches": mismatches,
            "identified_signals": sorted(set(identified_signals))}


# ---- 4) DS12110 抽样 diff -----------------------------------------------------
def _find_lqfp176_col(header_row):
    """LQFP176 列号：表头行的包名是逐字反转文本（'671PFQL'），
    反转后含 'LQFP176' 的列即 LQFP176 脚号列。"""
    for ci, cell in enumerate(header_row or []):
        c = norm((cell or "")[::-1])
        if "LQFP176" in c:
            return ci
    return None


def _table_header_col(t):
    for row in t[:3]:
        col = _find_lqfp176_col(row)
        if col is not None:
            return col
    return None


def _find_pdf_row(tables_by_page, position, pin_name):
    """按 LQFP176 脚号列定位行；名字仅做 sanity。名字精确行兜底。"""
    pn = norm(pin_name)
    fallback = None
    for page, t in tables_by_page:
        col = _table_header_col(t)
        for r in t:
            if not r:
                continue
            if col is not None and col < len(r):
                c = (r[col] or "").strip()
                if c.isdigit() and int(c) == position:
                    name_ok = any(norm(cell).startswith(pn)
                                  for cell in r if cell)
                    return {"page": page, "row": r, "pos_col": col,
                            "name_ok": name_ok}
            if fallback is None and any(
                    norm(cell) == pn for cell in r if cell):
                fallback = {"page": page, "row": r, "pos_col": None,
                            "name_ok": True}
    return fallback


def _split_af_tokens(cell):
    toks = []
    for tok in re.split(r"[\n,/;]+", cell or ""):
        tok = tok.strip()
        if tok and tok != "-":
            toks.append(tok)
    return toks


def _canon(n):
    """DS12110 ↔ CubeMX 信号命名等价归一（n 已 norm()）。规则全部显式登记：
    DEBUG_ 前缀省略、LCD_/LTDC_、ETH_RMII_/ETH_MII_（DS 斜杠双名）、RCC_
    前缀、SWPMI1/SWPMI。"""
    x = n
    if x.startswith("DEBUGTRACE"):
        x = x[5:]
    if x.startswith("LCD"):
        x = "LTDC" + x[3:]
    x = x.replace("RMII", "")
    x = x.replace("MII", "")
    if x.startswith("RCC"):
        x = x[3:]
    if x.startswith("SWPMI1"):
        x = "SWPMI" + x[6:]
    return x


def _join_tokens(toks, targets):
    """pdfplumber 换行把信号名截断（'USART2'+'NSS'）：贪心按连续 token 拼
    接回已知信号名；拼不回的原样保留。"""
    out = []
    i = 0
    tset = set(targets)
    while i < len(toks):
        matched = False
        for j in range(min(len(toks), i + 4), i, -1):
            cand = _canon("".join(norm(t) for t in toks[i:j]))
            if cand in tset:
                out.append(cand)
                i = j
                matched = True
                break
        if not matched:
            out.append(_canon(norm(toks[i])))
            i += 1
    return out


def _compare_af_sets(ds_tokens, tbl_names):
    """返回 (variants, conflicts, pdf_extras, table_missing)。

    - 变体：canon 后 fuzzy≥0.85 配对且数字部分相同（纯命名惯例差异）；
    - 冲突：配对但数字不同（SPDIFRX1_IN3/IN4 类，信号序号不同=真差异）；
    - pdf_extra：DS 列了而 CubeMX 没有的信号（DS 超集，登记不判死）；
    - table_missing：CubeMX 有而 DS 该行没列出（转录疑点，判 fail）。"""
    import difflib

    tbl = {_canon(norm(n)): n for n in tbl_names}
    ds = [_canon(t) for t in _join_tokens(ds_tokens, tbl.keys())]
    ds_set, tbl_set = set(ds), set(tbl)
    variants, conflicts = [], []
    rest_ds = sorted(ds_set - tbl_set)
    rest_tbl = sorted(tbl_set - ds_set)
    used = set()
    for d in rest_ds:
        m = difflib.get_close_matches(d, [t for t in rest_tbl
                                          if t not in used], n=1, cutoff=0.85)
        if m:
            t = m[0]
            used.add(t)
            pair = {"pdf": d, "table": t}
            if re.sub(r"[^0-9]", "", d) == re.sub(r"[^0-9]", "", t):
                variants.append(pair)
            else:
                conflicts.append(pair)
    pdf_extras = sorted(set(rest_ds) - {p["pdf"] for p in variants}
                        - {c["pdf"] for c in conflicts})
    table_missing = sorted(set(rest_tbl) - {p["table"] for p in variants}
                           - {c["table"] for c in conflicts})
    return variants, conflicts, pdf_extras, table_missing


def ds12110_sampling(table_pins_by_pos):
    import pdfplumber

    n_pages = None
    tables_by_page = []
    with pdfplumber.open(PDF_PATH) as pdf:
        n_pages = len(pdf.pages)
        for i in range(55, min(101, len(pdf.pages))):
            try:
                tables = pdf.pages[i].extract_tables()
            except Exception as exc:  # noqa: BLE001 单页解析失败不致死
                print("page %d extract fail: %s" % (i + 1, exc), file=sys.stderr)
                continue
            for t in tables or []:
                if t:
                    tables_by_page.append((i + 1, t))
    print("pdf tables collected: %d" % len(tables_by_page), file=sys.stderr)

    per_pin = []
    col_votes = {}
    for pos in SAMPLE_PINS:
        pin = table_pins_by_pos[pos]
        hit = _find_pdf_row(tables_by_page, pos, pin["name"])
        if hit is None:
            per_pin.append({"position": pos, "pin": pin["name"],
                            "verdict": "unresolved", "reason": "row_not_found"})
            continue
        r = hit["row"]
        ni = None
        start = (hit["pos_col"] + 1) if hit["pos_col"] is not None else 0
        for ci in range(start, len(r)):
            c = norm(r[ci])
            if c and c.startswith(norm(pin["name"])):
                ni = ci
                break
        if ni is None:
            per_pin.append({"position": pos, "pin": pin["name"],
                            "verdict": "unresolved",
                            "reason": "name_cell_not_found",
                            "page": hit["page"]})
            continue
        int_cols = {ci: int(c.strip()) for ci, c in enumerate(r[:ni])
                    if c and c.strip().isdigit()}
        hit_pos = any(v == pos for v in int_cols.values())
        for ci, v in int_cols.items():
            if v == pos:
                col_votes[ci] = col_votes.get(ci, 0) + 1
        trailing = r[ni + 1:]
        if len(trailing) >= 5:
            af_cell = trailing[3]
            additional = trailing[4] if len(trailing) >= 5 else None
            method = "strict_super_column"
        else:
            af_cell = max(trailing, key=lambda c: len(_split_af_tokens(c) or [""])) \
                if trailing else None
            additional = None
            method = "longest_cell_fallback"
        ds_toks = _split_af_tokens(af_cell)
        tbl_names = [s["signal"] for s in pin["signals"] if s["af"] is not None]
        if not ds_toks:
            if not tbl_names:
                per_pin.append({"position": pos, "pin": pin["name"],
                                "verdict": "match_empty", "page": hit["page"],
                                "position_in_row": hit_pos, "method": method,
                                "note": "电源/专用脚：双侧 AF 集均为空"})
            else:
                per_pin.append({"position": pos, "pin": pin["name"],
                                "verdict": "unresolved",
                                "reason": "af_cell_empty_table_nonempty",
                                "page": hit["page"],
                                "position_in_row": hit_pos, "method": method,
                                "table_af": tbl_names})
            continue
        variants, conflicts, pdf_extras, table_missing = \
            _compare_af_sets(ds_toks, tbl_names)
        if conflicts:
            verdict = "conflict"
        elif table_missing:
            verdict = "mismatch"
        elif pdf_extras:
            verdict = "pdf_extra"
        elif variants:
            verdict = "naming_variant"
        else:
            verdict = "match"
        per_pin.append({
            "position": pos, "pin": pin["name"], "page": hit["page"],
            "method": method, "position_in_row": hit_pos,
            "pdf_af_tokens": ds_toks,
            "naming_variants": variants, "conflicts": conflicts,
            "pdf_extra_signals": pdf_extras,
            "table_missing_in_pdf": table_missing,
            "additional_column": additional, "verdict": verdict})
    matched = sum(1 for p in per_pin if p["verdict"] in ("match",
                                                         "match_empty"))
    variants_n = sum(1 for p in per_pin
                     if p["verdict"] in ("naming_variant", "pdf_extra"))
    conflicts = [p for p in per_pin if p["verdict"] == "conflict"]
    mismatched = [p for p in per_pin if p["verdict"] == "mismatch"]
    unresolved = [p for p in per_pin if p["verdict"] == "unresolved"]
    return {
        "source": "DS12110-stm32h743ii.pdf（st.com 直连；LQFP176 alternate "
                  "function mapping 表，pages 56-101 扫描）",
        "pdf_pages": n_pages,
        "sampled": len(per_pin),
        "matched": matched,
        "naming_variant_pins": variants_n,
        "conflict_pins": len(conflicts),
        "unresolved": len(unresolved),
        "conflict_detail": conflicts,
        "mismatch_detail": mismatched,
        "unresolved_detail": unresolved,
        "naming_equivalence_rules": ["norm=去标点大写",
                                     "DEBUG 前缀省略（TRACECLK/TRACED*）",
                                     "LCD_↔LTDC_", "ETH_MII_↔ETH_",
                                     "RCC_ 前缀省略", "SWPMI1↔SWPMI"],
        "lqfp176_column_votes": {str(k): v for k, v in
                                 sorted(col_votes.items())},
        "af_number_note": "AF 编号列头为旋转文本，词提取不可得；pass 判据="
                          "信号名集合（等价归一后）相等。EVENTOUT(AF15) 由 "
                          "chip XML IOModes 合成，Modes XML 无独立条目。",
        "pass": not mismatched and not conflicts,
    }


def main():
    with open(TABLE_PATH, encoding="utf-8") as f:
        table = json.load(f)
    by_pos = {p["position"]: p for p in table["pins"]}

    with open(SOURCE_PACKAGE, encoding="utf-8") as f:
        src_pkg_sha = hashlib.sha256(f.read().encode("utf-8")).hexdigest()

    source_files = []
    for fname, role, origin in (
        ("STM32H743IITx.xml",
         "primary_machine_official（封装/引脚/信号描述符）",
         "F:/ST/MX/db/mcu/STM32H743IITx.xml（本机 STM32CubeMX 安装库，只读拷贝）"),
        ("GPIO-STM32H747_gpio_v1_0_Modes.xml",
         "primary_machine_official（AF 编号定义；即源包所记 GPIO-STM32H7xx"
         " AF 定义文件在本 DB 版本（V3.0）的现行名）",
         "F:/ST/MX/db/mcu/IP/GPIO-STM32H747_gpio_v1_0_Modes.xml（同上）"),
        ("STM32H743II.stm32data.json", "machine_derived_crosscheck",
         "https://github.com/embassy-rs/stm32-data-generated "
         "data/chips/STM32H743II.json（raw.githubusercontent 本机不可达，"
         "经 cdn.jsdelivr.net gh 镜像取回，内容=仓库文件）"),
        ("DS12110-stm32h743ii.pdf", "authoritative_human",
         "https://www.st.com/resource/en/datasheet/stm32h743ii.pdf（直连）"),
    ):
        p = os.path.join(SOURCES, fname)
        source_files.append({"file": fname, "role": role, "origin": origin,
                             "sha256": sha256_file(p),
                             "bytes": os.path.getsize(p)})

    record = {
        "schema_version": "1.0",
        "artifact_kind": "af_verification_v2",
        "spec_ref": "SPEC v1.3 §13.2 V2（文本双源核验后才可进入约束或结构"
                    "来源）；源包 out/revc-fd1/approvals/sources/"
                    "mcu-af-table.json transcription_plan 步骤②③",
        "verifier": "tools/pcbflow/scripts/af_verify.py",
        "table": {"path": "tools/pcbflow/out/revc-af/mcu-af-table-full.json",
                  "sha256": sha256_file(TABLE_PATH)},
        "source_package": {"path": "tools/pcbflow/out/revc-fd1/approvals/"
                                   "sources/mcu-af-table.json",
                           "sha256": src_pkg_sha, "frozen": True},
        "sources": source_files,
        "source_basis_deviation": {
            "pinned": "GitHub STMicroelectronics/STM32CubeH7 "
                      "db/mcu/IP/GPIO-STM32H7xx_saif.xml",
            "actual": "本机官方 STM32CubeMX 安装库 F:/ST/MX/db/（同一 CubeMX "
                      "DB XML 源；DBVersion V3.0）",
            "evidence": "官方 Cube 仓库无 db/ 目录（GitHub API contents "
                        "…/db/mcu/IP → 404；db/ 只随 CubeMX 软件分发）；"
                        "AF 定义文件在本 DB 版本名为 "
                        "GPIO-STM32H747_gpio_v1_0_Modes.xml"
                        "（chip XML IP 引用 ConfigFile=GPIO-STM32H7xx）",
            "assessment": "同源同类（CubeMX DB XML），machine_official 角色"
                          "不变；文件名随 DB 版本演进",
            "decision_ref": "AF-13-D1（PHASE-REPORT-13 §口径决策）"},
    }

    print("crosscheck stm32data…", file=sys.stderr)
    record["crosscheck_stm32data"] = crosscheck_stm32data(by_pos)
    print("crosscheck board anchor…", file=sys.stderr)
    record["crosscheck_board_anchor"] = crosscheck_board_anchor(by_pos)
    print("identification coverage…", file=sys.stderr)
    record["identification_coverage"] = identification_coverage(by_pos)
    print("ds12110 sampling…", file=sys.stderr)
    record["ds12110_sampling"] = ds12110_sampling(by_pos)

    ident = record["identification_coverage"]
    ds = record["ds12110_sampling"]
    conflict_signals = sorted({c["table"] for pin in ds.get("conflict_detail",
                                []) for c in pin.get("conflicts", [])})
    conflict_on_board = sorted(set(conflict_signals) &
                               set(ident["identified_signals"]))
    hard_fail = (not record["crosscheck_stm32data"]["pass"] or
                 not record["crosscheck_board_anchor"]["pass"] or
                 ident["mismatches"] or
                 ds["mismatch_detail"] or
                 conflict_on_board)
    divergent = bool(ds.get("naming_variant_pins") or
                     ds.get("conflict_pins"))
    record["verdict"] = {
        "dual_source": "fail" if hard_fail else
                       ("pass_with_divergences" if divergent else "pass"),
        "identification_mismatches": len(ident["mismatches"]),
        "conflict_signals_table_side": conflict_signals,
        "conflict_signals_used_by_board_nets": conflict_on_board,
        "note": "pass 判据：stm32data 逐脚名 0 失配、板锚点 0 失配、识别 0 "
                "锚点违例、DS 采样 0 mismatch 0 unexplained；conflict 类"
                "（等价归一+fuzzy 后仍数字级差异，如信号序号不同）须板上"
                "零使用才不降级为 fail；naming_variant（命名惯例差异）登记"
                "不判 fail。unresolved 如实计数不判 fail（提取失败≠矛盾）",
    }

    sys.stdout.buffer.write(hashing.canonical_json_bytes(record))
    print("verdict=%s ds=%d/%d stm32data=%s anchors=%s" % (
        record["verdict"]["dual_source"],
        record["ds12110_sampling"]["matched"],
        record["ds12110_sampling"]["sampled"],
        record["crosscheck_stm32data"]["pass"],
        record["crosscheck_board_anchor"]["pass"]), file=sys.stderr)


if __name__ == "__main__":
    main()
