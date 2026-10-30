# -*- coding: utf-8 -*-
"""失败证书 v5.failcert.v1（任务书 §3.6）：三态、独立复核器。

- UNSAT：unsat_core 必填、unknown_boundary 禁填；每条目须过独立复核器逐条重算。
- UNKNOWN：unknown_boundary 必填、unsat_core 禁填；如实报 achieved/boundary/budget。
- 虚报（UNKNOWN 写成 UNSAT）= 证书欺诈。
独立复核器 verify() 是确定性重算入口，cert.check.procedure 登记其入口名。
"""
from . import canonical, schema_loader
from .metrics import capacity

CERT_VERSION = "v5.failcert.v1"
VERIFY_PROCEDURE = "v5.failcert.verify"


class CertError(ValueError):
    pass


def _load_cert_schema():
    return schema_loader.load_schema("failcert.v1.schema.json")


def build_unsat_cert(board_provenance, scope_nets, unsat_core, region=None):
    cert = {
        "cert_version": CERT_VERSION,
        "board_provenance": board_provenance,
        "status": "UNSAT",
        "scope": {"nets": list(scope_nets)},
        "unsat_core": list(unsat_core),
        "check": {"procedure": VERIFY_PROCEDURE},
    }
    if region:
        cert["scope"]["region"] = region
    finalize(cert)
    return cert


def build_unknown_cert(board_provenance, scope_nets, achieved, blocked_at, budget, region=None):
    cert = {
        "cert_version": CERT_VERSION,
        "board_provenance": board_provenance,
        "status": "UNKNOWN",
        "scope": {"nets": list(scope_nets)},
        "unknown_boundary": {
            "achieved": achieved,
            "blocked_at": blocked_at,
            "budget": budget,
        },
        "check": {"procedure": VERIFY_PROCEDURE},
    }
    if region:
        cert["scope"]["region"] = region
    finalize(cert)
    return cert


def finalize(cert):
    """落盘前校验（含跨字段互斥），通过后填 recheck=PASS。"""
    validate(cert)
    cert["check"]["recheck"] = "PASS"
    return cert


def validate(cert):
    schema_loader.validate(cert, _load_cert_schema(), schema_loader.default_registry(), "")
    status = cert.get("status")
    if status == "UNSAT":
        if not cert.get("unsat_core"):
            raise CertError("UNSAT 证书 unsat_core 必填且非空")
        if "unknown_boundary" in cert:
            raise CertError("UNSAT 证书禁止填写 unknown_boundary")
    elif status == "UNKNOWN":
        if "unsat_core" in cert:
            raise CertError("UNKNOWN 证书禁止填写 unsat_core（虚报不可行=证书欺诈）")
        ub = cert.get("unknown_boundary")
        if not ub or not all(k in ub for k in ("achieved", "blocked_at", "budget")):
            raise CertError("UNKNOWN 证书 unknown_boundary 必填 achieved/blocked_at/budget")
    else:
        raise CertError("未知状态 %r" % status)
    return cert


def _recompute_entry(entry):
    """逐条重算 unsat_core 条目。结构化 data 承载可复算式，文本 arithmetic 供人读。

    支持的 constraint：
      capacity: data={"occupancy_terms":[...], "capacity_mm":X}
                重算 sum(terms) + 0.5×(n−1) > X 是否成立
      width:    data={"planned_mm":w, "required_min_mm":m}
                重算 w < m 是否成立
    """
    data = entry.get("data", {})
    constraint = entry.get("constraint")
    if constraint == "capacity":
        terms = data["occupancy_terms"]
        n = len(terms)
        total = sum(terms) + capacity.NET_NET_SPACING * (n - 1) if n else 0.0
        cap = data["capacity_mm"]
        return (round(total, 10) > cap + 1e-9,
                "Σ(%s)+%.1f×%d=%.2f > %.1f" % ("+".join(str(t) for t in terms),
                                                capacity.NET_NET_SPACING, n - 1,
                                                total, cap))
    if constraint == "width":
        w, m = data["planned_mm"], data["required_min_mm"]
        return (w < m - 1e-9, "%.2f < %.2f" % (w, m))
    raise CertError("不可复核的 constraint: %r" % constraint)


def verify(cert):
    """独立复核器：schema + 跨字段 + 逐条 unsat_core 重算。返回 {"recheck":"PASS","entries":[...]}。

    任何条目复核不过 → CertError（证书不合规 = 失败证据门不过，S-V5-5 计数）。
    """
    validate(cert)
    results = []
    if cert["status"] == "UNSAT":
        for i, entry in enumerate(cert["unsat_core"]):
            holds, expr = _recompute_entry(entry)
            if not holds:
                raise CertError("unsat_core[%d] 复算不成立: %s" % (i, expr))
            results.append({"index": i, "recomputed": expr})
    else:
        ub = cert["unknown_boundary"]
        ach = ub["achieved"]
        if ach.get("nets_connected", 0) > ach.get("nets_total", 0):
            raise CertError("achieved.nets_connected > nets_total")
        results.append({"index": 0, "recomputed": "achieved<=total"})
    return {"recheck": "PASS", "procedure": VERIFY_PROCEDURE, "entries": results}


def cert_bytes(cert) -> bytes:
    return canonical.canonical_json(cert)
