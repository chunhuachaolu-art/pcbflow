"""FF-REVC-0005 rail 源 v2 生成器（fd3 冻结源最小修改变换）。

只动：decision_basis/VCAP1/VCAP2/EMMC_VSEL/VBAT.supply/FB_NODE.supply/
caveats；其余字段随 fd3 文件逐字节保留（canonical json 序列化）。
stdout 重定向落盘（Mimosa 生成器模式）。
"""
import io
import json
import sys

SRC = "out/revc-fd3/approvals/sources/bom-power-derive.json"


def main():
    src = json.load(open(SRC, encoding="utf-8"))

    src["decision_basis"] = (
        "FF-REVC-0005 会话批准（2026-08-30 用户裁决：无实测条件；资料级即本链"
        "终态，实测升级项关闭）：以数据手册+网表证据将 fd3 五条缺源轨尽量落位"
        "——EMMC_VSEL demand 落 sourced（DS12110 Table 50 FT_xx Ilkg ±250nA "
        "max，PDR_ON=FT 型输入）；VCAP1/2 定性为内部稳压器储能端（DS12110 "
        "§6.3.2/Table 15+Table 114，BOM 行 17=2.2µF×2，引脚 81/125）；VBAT "
        "供给=查证性缺源（BOM 行 11 超级电容无厂商型号，不虚构）；FB_NODE 定"
        "性为控制传感节点。其余口径与 fd3 逐字节一致。")

    r = src["rails"]

    r["VCAP1"]["supply"]["basis"] = [
        "非独立供电轨（definitive）：VCAP=内核 LDO 储能端，DS12110 §6.3.2"
        "「VCAP external capacitor」（rev Y p106/Table 15；rev V p211/"
        "Table 114）；内核电流含于 U1 总 IDD，无独立额定可源，不重复拆分记账"
        "（fd3 口径沿留）"]
    r["VCAP1"]["demand"]["class"] = "not_applicable_internal_regulator"
    r["VCAP1"]["demand"]["basis"] = [
        "内核电流无独立钉源（DS12110 §6.3.2：VCAP 仅规定外部储能电容，BOM "
        "行 17=2.2µF×2 各 2.2µF，引脚 81/125）→消费方回退 width-derived 上界"
        "（fd2 政策）；不虚构拆分——definitive 分类非怠查"]
    r["VCAP2"]["supply"]["basis"] = list(r["VCAP1"]["supply"]["basis"])
    r["VCAP2"]["demand"]["class"] = "not_applicable_internal_regulator"
    r["VCAP2"]["demand"]["basis"] = list(r["VCAP1"]["demand"]["basis"])

    r["EMMC_VSEL"]["demand"] = {
        "value_a": 2.5e-07,
        "class": "sourced",
        "basis": [
            "板上实义=PDR_ON 高阻输入（网名 EMMC_VSEL 为历史残留，板上无 "
            "eMMC）；引脚类型 I/FT（DS12110 LQFP176 引脚表）→Ilkg ±250nA "
            "max（DS12110 §6.3.15 Table 50，rev Y p316）取上限 250nA="
            "2.5e-7A 为规划需求",
            "板面连接 refs=U1.2+J1.26：电平由载板经 J1.26 定义（SoM 口径），"
            "板上无上下拉——载板设计评审披露：PDR_ON 接 VSS 将禁用 PDR 监督"
            "且 VBAT 功能不再可用（DS12110 §3.5.2 电源监督）"],
    }
    r["EMMC_VSEL"]["supply"]["basis"] = [
        "载板定义电平（J1.26 出向臂）：板上无源件、无独立供给额定（fd3 口径"
        "沿留，不虚构）；漏电负载侧已落 sourced（见 demand）"]

    r["VBAT"]["supply"]["basis"] = [
        "查证性缺源（definitive）：超级电容 0.22F/5.5V（BOM 行 11）无厂商"
        "型号（purchase-list-revb.csv，hash f5a09e01；2026-08-30 查证）→无"
        "放电额定钉源，不虚构；信息性续算沿留：ΔV≈3.0−1.71=1.29V（充至 "
        "3.3−Vf，H743 VBAT 最低工作 1.71V）→t=C·ΔV/I_RTC≈0.22×1.29/"
        "2.32µA≈34h"]

    r["FB_NODE"]["supply"]["basis"] = [
        "非功率轨（definitive）：FB 凯尔文控制传感节点，margin 语义不适用"
        "（fd3 口径沿留）；R10 453k 自 3V3 馈入与 R11 100k 下拉为同一分压"
        "电流两侧视角（Vref=0.6V，ti.com TPS62085 页 fd3 已注册："
        "0.6×(1+4.53)=3.3V 核对 ✓）；不虚构供给"]

    src["caveats"] = [
        "本表为资料级（数据手册/网表可查证）规划估计；实测升级项已由用户裁决"
        "关闭（2026-08-30：无实测条件，资料级即本链终态）——fd3 的「NEXT 待"
        "人工 #4 保留实测复算」条款随之终结",
        "供给 sourced 评级仅覆盖『元件额定值直录』；系统级输入预算（USB "
        "0.5A→2.5W）对各 3V3 侧轨的约束已按链合成计入 derived 供给",
        "fd2 需求口径（5V_USB sourced 0.5A/11 轨 width-derived）为历史登记，"
        "fd3 起按本表 consumption 口径；fd2/fd3 冻结件不回写——本表消费经 "
        "--bom-power-file 指向本件（FF-REVC-0005）",
        "本表不改变 structures.json power_tree 的任何字段（① 权威不动，"
        "SPEC §18）",
    ]

    out = io.StringIO()
    json.dump(src, out, ensure_ascii=False, indent=1)
    sys.stdout.write(out.getvalue())


if __name__ == "__main__":
    main()
