"""TBD-1 独立阻抗复算（screening 级；SPEC §11.1 screening_or_external_required）。

模型族：
- HJ：Hammerstad & Jensen (1980) 微带准静态闭式（本件主模型）
- IPC-2141：计划现口径（对照连续性）
- 修正项：梯形蚀刻（有效宽度 w+Δw_eff）、阻焊（方向性注记，不定量建模）
- 差分：Zdiff=2·Z0·(1-0.48·e^(-0.96·s/h))（与计划同族，仅换 Z0 模型）

输入全部显式来自 stackup-basis.json（JLC04161H-7628，双源核验）。
输出 JSON → stdout（生成器模式，重定向落盘）。
"""
import json
import math
import sys

# 叠层（stackup-basis.json）：F.Cu 信号，In1=GND 平面
H_MM = 0.2104          # PP 7628×1 介质厚
ER = 4.4               # 7628 Er（jlcpcb.com/impedance 官方页）
T_MM = 0.035           # 外层 1oz 铜厚
# JLC 计算器建模口径（user-guide 文章；用于敏感性对比，不进主模型）
MASK_T_MM = 0.6 * 0.0254   # 阻焊铜上厚 0.6mil
MASK_ER = 3.8


def hj_z0(w, h=H_MM, er=ER, t=T_MM):
    """Hammerstad-Jensen 微带 Z0（含梯形蚀刻有效宽度修正）。"""
    # 有效宽度（Hammerstad 1975 梯形修正）
    if w >= t * math.pi * 2:
        w_eff = w + t / math.pi * (1 + math.log(2 * h / t))
    else:
        w_eff = (w + t / math.pi
                 * (1 + math.log(4 * math.pi * math.sqrt((w / h + 1.4) ** 2)
                                 / (t / h))))
    u = w_eff / h
    f = 6 + (2 * math.pi - 6) * math.exp(-((30.66 / u) ** 0.7528))
    z_air = 376.73 / (2 * math.pi) * math.log(
        f / u + math.sqrt(1 + (2 / u) ** 2))
    # εeff（HJ 1980）
    a = 1 + (1 / 49) * math.log((u ** 4 + (u / 52) ** 2)
                                / (u ** 4 + 0.432)) \
        + (1 / 18.7) * math.log(1 + (u / 18.1) ** 3)
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    e_eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)
    return z_air / math.sqrt(e_eff)


def ipc2141_z0(w, h=H_MM, er=ER, t=T_MM):
    """计划现口径：Z0=87/sqrt(Er+1.41)·ln(5.98h/(0.8w+t))。"""
    return 87 / math.sqrt(er + 1.41) * math.log(
        5.98 * h / (0.8 * w + t))


def zdiff(w, s, z0_fn=hj_z0, h=H_MM):
    return 2 * z0_fn(w) * (1 - 0.48 * math.exp(-0.96 * s / h))


def width_for_z0(target, z0_fn, lo=0.05, hi=3.0):
    for _ in range(200):
        mid = (lo + hi) / 2
        if z0_fn(mid) > target:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


def width_for_zdiff(target, s, z0_fn, lo=0.05, hi=3.0):
    for _ in range(200):
        mid = (lo + hi) / 2
        if zdiff(mid, s, z0_fn) > target:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


def main():
    out = {
        "artifact_kind": "impedance_recalc_screening",
        "model": {
            "primary": "Hammerstad-Jensen (1980) 准静态微带 + 梯形蚀刻有效宽度",
            "diff": "Zdiff=2·Z0·(1-0.48·e^(-0.96·s/h))（计划同族，仅换 Z0）",
            "crosscheck": "IPC-2141（计划现口径，连续性对照）",
            "not_modeled": "阻焊加载（JLC 口径含阻焊 Er=3.8/铜上 0.6mil；方向="
                           "略降 Z0 约 1-3Ω，定性登记不定量）；共面参考效应",
            "accuracy_note": "HJ 对 w/h≥0.1 准静态 ±1~2%；screening 级（SPEC "
                             "§11.1），非板厂签核值",
        },
        "stackup": {"h_mm": H_MM, "er": ER, "t_outer_mm": T_MM,
                    "code": "JLC04161H-7628",
                    "ref": "out/revc-fd1/approvals/sources/stackup-basis.json"},
        "cases": [],
    }
    cases = out["cases"]

    def add_case(**kw):
        cases.append(kw)

    # C1: 50Ω 单端 L1——目标宽度（两模型）
    add_case(
        case="C1_50ohm_single_ended_F_Cu", target_ohm=50,
        hj_width_mm=width_for_z0(50, hj_z0),
        hj_z0_at_plan_0p2=round(hj_z0(0.2), 2),
        ipc2141_width_mm=width_for_z0(50, ipc2141_z0),
        ipc2141_z0_at_plan_0p2=round(ipc2141_z0(0.2), 2))

    # C2: 90Ω 差分——s=0.2（计划口径）与 s=0.223（板面最近平行边距）
    for s, tag in [(0.2, "s=0.2（计划 adopted 口径）"),
                   (0.223, "s=0.223（板面 F.Cu 最近平行边距实测）")]:
        add_case(
            case="C2_90ohm_diff_%s" % tag.split("（")[0].replace("=", "_")
                .replace(".", "p"),
            target_ohm=90, spacing_mm=s, spacing_note=tag,
            hj_width_mm=width_for_zdiff(90, s, hj_z0),
            hj_zdiff_at_w0p2=round(zdiff(0.2, s, hj_z0), 2),
            ipc2141_width_mm=width_for_zdiff(90, s, ipc2141_z0),
            ipc2141_zdiff_at_w0p2=round(zdiff(0.2, s, ipc2141_z0), 2),
            board_actual_w_mm=0.2)

    # C3: 板面实跑几何（w=0.2/s=0.223）HJ 判定 vs 90±15%
    zd_board = zdiff(0.2, 0.223, hj_z0)
    add_case(
        case="C3_board_actual_verdict", board_w_mm=0.2,
        board_s_mm=0.223, hj_zdiff_ohm=round(zd_board, 2),
        tolerance_pct=15, lo_ok=round(90 * 0.85, 1),
        hi_ok=round(90 * 1.15, 1),
        within_tolerance=bool(90 * 0.85 <= zd_board <= 90 * 1.15))

    # C4: 板厂口径标定（JLC 官方计算器实测锚点，2026-08-30 浏览器实测
    # jlcpcb.com/pcb-impedance-calculator，JLC04161H-7628 Standard 档）
    jlc_se_w = 14.12 * 0.0254   # 50Ω SE L1 → 0.3586mm
    jlc_diff_w = 11.44 * 0.0254  # 90Ω DIFF L1 s=8mil → 0.2906mm
    jlc_diff_s = 8 * 0.0254      # 0.2032mm
    add_case(
        case="C4_jlc_anchors",
        source="jlcpcb.com/pcb-impedance-calculator（含阻焊+梯形建模）",
        se_50ohm={"jlc_width_mm": round(jlc_se_w, 4),
                  "hj_width_mm": width_for_z0(50, hj_z0),
                  "hj_z0_at_jlc_w": round(hj_z0(jlc_se_w), 2),
                  "ipc2141_z0_at_jlc_w": round(ipc2141_z0(jlc_se_w), 2)},
        diff_90ohm={"jlc_width_mm": round(jlc_diff_w, 4),
                    "jlc_spacing_mm": round(jlc_diff_s, 4),
                    "hj_width_mm": width_for_zdiff(90, jlc_diff_s, hj_z0),
                    "hj_zdiff_at_jlc_w": round(
                        zdiff(jlc_diff_w, jlc_diff_s, hj_z0), 2),
                    "ipc2141_zdiff_at_jlc_w": round(
                        zdiff(jlc_diff_w, jlc_diff_s, ipc2141_z0), 2)})

    # C5: 标定外推——板厂模型偏差 δ 应用于板面几何
    # δ = JLC 口径 − HJ（在 JLC 锚点几何上）；板面估值 = HJ + δ
    delta_diff = (90 - zdiff(jlc_diff_w, jlc_diff_s, hj_z0))
    delta_se = (50 - hj_z0(jlc_se_w))
    add_case(
        case="C5_calibrated_board_estimate",
        method="δ=JLC锚点Z−HJ锚点Z（同叠层同模式单点标定）；板面估值=HJ+δ",
        delta_diff_ohm=round(delta_diff, 2),
        delta_se_ohm=round(delta_se, 2),
        board_diff_est_ohm=round(zd_board + delta_diff, 2),
        board_diff_est_lo_no_mask=round(zd_board + delta_diff, 2),
        note="JLC 模型含阻焊（铜上 0.6mil/Er3.8）+梯形蚀刻；δ 为负（JLC 偏低）"
             "→板面估值下移；板面 0.2/0.223 估值≈%.1fΩ（±15pct 上限 103.5）"
             % (zd_board + delta_diff))

    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
