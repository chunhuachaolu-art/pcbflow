"""pcbflow.v4_1.precheck -- advisory 预检器 v4_1（候选链入口）。

替代 P3 预检的 pad=min(w,h)/2 近似（根因锚 rollback.json §diagnosis）：
本预检用精确焊盘几何（geometry.PadGeom Minkowski 核）+ 逐网 net class
clearance 矩阵（netclasses.NetClassTable）。

保守化方向=漏报 0（任务书 §3 E1：宁可误报不可漏报——P3 事故是漏报方向
错误）：

1. 保守带 CONSERVATIVE_BAND_MM（默认 0.01mm）：pred < required + band
   即判违例；band 内合法侧判例按误报入台账（不静默）；
2. circle w!=h 畸形取 max 轴直径（超集）；
3. custom 基元（backlog 未实现）以基元顶点包围盒超集建模并显式登记；
4. THT 焊盘（*.Cu）在全部铜层上均为障碍（P3 近似只登记 F.Cu=漏报源，
   本版修复）；
5. via 跨度层展开为全障碍层。

候选链接口：

- check_segment(net, layer, width, ax, ay, bx, by)：单段新几何；
- patch_final_segments(parsed, patch)+check_patch(...)：P3 候选 patch
  dict（pcbflow-p3revc-patch-1：text_ops.modify/insert_segment）落地后
  的全段终态预检（不只查插入段——被改端点的旧段同样复查）。

advisory 地位（R6 继承）：恒不能清 DRC 旗/改门；kicad-cli 唯一 authority。

已知边界（显式登记不静默）：zone/铺铜填充不建模（任务书 E2/E6 范畴，
track-vs-zone 违例不可见=已登记 limitation）；同批 protected 网互不约束
（批 DRC 兜底，P3 同口径）。

零 IO、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

import math

from . import (CONSERVATIVE_BAND_MM, DECLARED_DATE)
from .geometry import (GeomError, GeomItem, PadGeom,
                       clearance_between_items)

__all__ = ["PrecheckBlocked", "AdvisoryPrecheckV41", "patch_final_segments",
           "build_geom_items"]

_PRECHECK_SCHEMA = "pcbflow.v4_1.precheck/1"

_LIMITATIONS = [
    "zone/铺铜填充不建模（track-vs-zone clearance 违例不可见；E2/E6 域，"
    "登记为 limitation 非 silence）",
    "同批 protected 网互不约束（批 kicad-cli DRC 兜底；P3 同口径）",
    "custom 基元 backlog：以基元顶点包围盒保守超集建模",
]


class PrecheckBlocked(ValueError):
    """预检 fail-closed（解析/规则不可用时不渲染 clean/violation）。"""


def build_geom_items(parsed):
    """路径 A 解析产物 -> GeomItem 列表（track/via/pad）。"""
    items = []
    copper = set(parsed["copper_layers"])
    for s in parsed["segments"]:
        items.append(GeomItem.from_track(
            s["net"], s["layer"], s["width"],
            s["x1"], s["y1"], s["x2"], s["y2"],
            src={"uuid": s["uuid"]}))
    for v in parsed["vias"]:
        items.append(GeomItem.from_via(
            v["net"], v["size"], v["layers"], v["x"], v["y"],
            src={"uuid": v["uuid"]}))
    for p in parsed["pads"]:
        if not p["layers"]:
            continue  # 非铜层 pad 不进 clearance 模型（两路径同口径）
        pad = PadGeom(
            p["shape"], p["x_mm"], p["y_mm"], p["w_mm"], p["h_mm"],
            p["rotation_deg"], radius=p["corner_radius_mm"],
            pad_id=p["pad_id"], net_id=p["net_id"], layers=p["layers"],
            primitive_pts=p["primitive_pts"])
        layers = set(p["layers"]) & copper
        items.append(GeomItem.from_pad(pad, layers,
                                       src={"pad_id": p["pad_id"]}))
    return items


def patch_final_segments(parsed, patch):
    """patch dict -> 落地后终态段列表（插入段+被改端点旧段，全部复查）。

    支持 pcbflow-p3revc-patch-1 的 text_ops：modify（uuid 端点替换）与
    insert_segment。找不到 uuid / 端点不匹配 -> PrecheckBlocked（fail-closed）。
    """
    ops = patch.get("text_ops") or {}
    by_uuid = {s["uuid"]: dict(s) for s in parsed["segments"]}
    final = []
    for mod in ops.get("modify") or []:
        uid = mod.get("uuid")
        if uid not in by_uuid:
            raise PrecheckBlocked("modify 引用未知 uuid（fail-closed）: %r"
                                  % (uid,))
        seg = dict(by_uuid[uid])
        rc, nc = mod["replace_coord"], mod["new_coord"]
        hit = False
        for (a, b) in (("x1", "y1"), ("x2", "y2")):
            if abs(seg[a] - rc[0]) <= 1e-6 and abs(seg[b] - rc[1]) <= 1e-6:
                seg[a], seg[b] = nc[0], nc[1]
                hit = True
                break
        if not hit:
            raise PrecheckBlocked(
                "modify replace_coord 不匹配段端点（fail-closed）: uuid=%r "
                "coord=%r" % (uid, rc))
        by_uuid[uid] = seg
        final.append(seg)
    ins = ops.get("insert_segment")
    if ins is not None:
        final.append({
            "uuid": "(inserted)",
            "net": ins["net"], "layer": ins["layer"],
            "width": ins["width"],
            "x1": ins["start"][0], "y1": ins["start"][1],
            "x2": ins["end"][0], "y2": ins["end"][1],
        })
    if not final:
        raise PrecheckBlocked("patch 无可预检几何（fail-closed）: %r"
                              % (patch.get("patch_id"),))
    return final


class AdvisoryPrecheckV41:
    """advisory 预检器 v4_1（精确几何 + 逐网 clearance 矩阵）。"""

    def __init__(self, geom_items, net_table, protected_nets=(),
                 conservative_band_mm=CONSERVATIVE_BAND_MM):
        self.items = list(geom_items)
        self.net_table = net_table
        self.protected = set(protected_nets)
        self.band = float(conservative_band_mm)
        if self.band < 0.0 or not math.isfinite(self.band):
            raise PrecheckBlocked("保守带非法（fail-closed）: %r"
                                  % (conservative_band_mm,))
        if net_table is None:
            raise PrecheckBlocked(
                "net class 表缺失（fail-closed not_available——须 blocked，"
                "不得隐式假定 clearance）")

    # ------------------------------------------------------------ 单段

    def _foreign_items(self, net, layer):
        for it in self.items:
            if it.net == net or it.net in self.protected:
                continue
            if layer not in it.layers:
                continue
            yield it

    def check_segment(self, net, layer, width, ax, ay, bx, by):
        """单段新几何预检 -> 机器可读结果（纯函数式）。"""
        try:
            cand = GeomItem.from_track(net, layer, width, ax, ay, bx, by)
        except GeomError as exc:
            raise PrecheckBlocked("候选几何非法（fail-closed）: %s" % exc)
        violations = []
        min_clear = None
        pairs = 0
        for it in self._foreign_items(net, layer):
            res = clearance_between_items(cand, it)
            if res is None:
                continue
            pairs += 1
            required = self.net_table.required_clearance(net, it.net)
            pred = res["clearance_mm"]
            overlap = res["overlap"]
            if overlap:
                eff = pred  # 负值（核距 0 - 双半径），必判违例
            else:
                eff = pred
            if min_clear is None or eff < min_clear:
                min_clear = eff
            hard = overlap or pred < required - 1e-12
            band = (not hard) and pred < required + self.band - 1e-12
            if hard or band:
                violations.append({
                    "item_kind": it.kind,
                    "item_ref": it.src.get("uuid") or it.src.get("pad_id"),
                    "item_net": it.net,
                    "layer": layer,
                    "pred_clearance_mm": None if overlap
                    else round(pred, 6),
                    "required_mm": round(required, 6),
                    "overlap": overlap,
                    "flag_class": "hard_violation" if hard
                    else "conservative_band",
                    "conservative_approximation": it.conservative_approximation,
                })
        verdict = "violation" if violations else "clean"
        return {
            "schema": _PRECHECK_SCHEMA,
            "declared_date": DECLARED_DATE,
            "engine": "v4_1_exact_minkowski_core",
            "parser": "A_tree_sexpr_min",
            "candidate": {
                "net": net, "layer": layer,
                "width_mm": round(float(width), 6),
                "a": [round(float(ax), 6), round(float(ay), 6)],
                "b": [round(float(bx), 6), round(float(by), 6)],
            },
            "verdict": verdict,
            "violations": sorted(violations, key=lambda v: (
                v["flag_class"] != "hard_violation",
                v["pred_clearance_mm"] if v["pred_clearance_mm"] is not None
                else -1.0, v["item_ref"] or "")),
            "min_foreign_clearance_mm": None if min_clear is None
            else round(min_clear, 6),
            "checked_pairs": pairs,
            "conservative_band_mm": self.band,
            "limitations": list(_LIMITATIONS),
        }

    # ------------------------------------------------------------ via/pad 候选

    def check_via(self, net, layers, size, x, y):
        """via 候选预检（对异网 track/via/pad；层跨度全生效）。"""
        try:
            cand = GeomItem.from_via(net, size, layers, x, y)
        except GeomError as exc:
            raise PrecheckBlocked("候选 via 几何非法（fail-closed）: %s"
                                  % exc)
        return self._check_candidate(cand)

    def check_pad(self, pad, copper_layers):
        """pad 候选预检（pad-vs-track/via/pad；THT 全铜层生效）。"""
        try:
            cand = GeomItem.from_pad(pad, copper_layers)
        except GeomError as exc:
            raise PrecheckBlocked("候选 pad 几何非法（fail-closed）: %s"
                                  % exc)
        return self._check_candidate(cand)

    def _check_candidate(self, cand):
        """通用候选复核（候选可以为 track/via/pad 核表示）。"""
        violations = []
        min_clear = None
        pairs = 0
        for it in self.items:
            if it.net == cand.net or it.net in self.protected:
                continue
            if not (cand.layers & it.layers):
                continue
            res = clearance_between_items(cand, it)
            if res is None:
                continue
            pairs += 1
            required = self.net_table.required_clearance(cand.net, it.net)
            pred = res["clearance_mm"]
            overlap = res["overlap"]
            if min_clear is None or pred < min_clear:
                min_clear = pred
            hard = overlap or pred < required - 1e-12
            band = (not hard) and pred < required + self.band - 1e-12
            if hard or band:
                violations.append({
                    "item_kind": it.kind,
                    "item_ref": it.src.get("uuid") or it.src.get("pad_id"),
                    "item_net": it.net,
                    "layer": sorted(cand.layers & it.layers)[0],
                    "pred_clearance_mm": None if overlap
                    else round(pred, 6),
                    "required_mm": round(required, 6),
                    "overlap": overlap,
                    "flag_class": "hard_violation" if hard
                    else "conservative_band",
                    "conservative_approximation": it.conservative_approximation,
                })
        return {
            "schema": _PRECHECK_SCHEMA,
            "declared_date": DECLARED_DATE,
            "engine": "v4_1_exact_minkowski_core",
            "parser": "A_tree_sexpr_min",
            "candidate_kind": cand.kind,
            "candidate_net": cand.net,
            "verdict": "violation" if violations else "clean",
            "violations": sorted(violations, key=lambda v: (
                v["flag_class"] != "hard_violation",
                v["pred_clearance_mm"] if v["pred_clearance_mm"] is not None
                else -1.0, v["item_ref"] or "")),
            "min_foreign_clearance_mm": None if min_clear is None
            else round(min_clear, 6),
            "checked_pairs": pairs,
            "conservative_band_mm": self.band,
            "limitations": list(_LIMITATIONS),
        }

    # ------------------------------------------------------------ patch

    def check_patch(self, parsed, patch):
        """P3 候选 patch 预检（终态全段复查；blocked 传播不吞）。"""
        segs = patch_final_segments(parsed, patch)
        per_seg = []
        any_viol = False
        blocked = []
        for s in segs:
            try:
                r = self.check_segment(s["net"], s["layer"], s["width"],
                                       s["x1"], s["y1"], s["x2"], s["y2"])
            except PrecheckBlocked as exc:
                blocked.append(str(exc))
                continue
            per_seg.append({
                "uuid": s["uuid"], "verdict": r["verdict"],
                "min_foreign_clearance_mm": r["min_foreign_clearance_mm"],
                "violations": r["violations"],
            })
            any_viol = any_viol or r["verdict"] == "violation"
        if blocked:
            return {
                "schema": _PRECHECK_SCHEMA,
                "declared_date": DECLARED_DATE,
                "engine": "v4_1_exact_minkowski_core",
                "patch_id": patch.get("patch_id"),
                "net_id": patch.get("net_id"),
                "verdict": "blocked",
                "blocked_reasons": blocked,
                "per_segment": per_seg,
                "limitations": list(_LIMITATIONS),
            }
        return {
            "schema": _PRECHECK_SCHEMA,
            "declared_date": DECLARED_DATE,
            "engine": "v4_1_exact_minkowski_core",
            "patch_id": patch.get("patch_id"),
            "net_id": patch.get("net_id"),
            "verdict": "violation" if any_viol else "clean",
            "per_segment": per_seg,
            "limitations": list(_LIMITATIONS),
        }
