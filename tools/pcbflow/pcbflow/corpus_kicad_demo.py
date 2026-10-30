"""TL-5 第四包：KiCad 官方 demo（SRC-KICAD-DEMO）逐 demo 许可审计与合规留存。

审计结论（2026-09-05 S15 会话实测，明细见 out/v3-tl5/source-research-r4.json
与 out/v3-tl5/kicad-demo-license-audit.json）：
- 上游=gitlab.com/kicad/code/kicad 仓库 demos/ 目录（GitHub 镜像
  KiCad/kicad-source-mirror 双 host 同步验证同 commit）；pin commit
  10fd71558f001f74f179127e5f7ef335f9dd3304；归档源=demos 子树 tarball
  （GitLab archive API path=demos，96,489,574B，sha256 1ee5135d…）——
  解包 709 文件与 GitHub 镜像 git tree 枚举（truncated=false）全等 +
  git blob sha1 全量校验零 mismatch + GitLab files API 抽样逐字节一致；
  GitLab 递归 tree API 逐目录存在漏报（如 cm5_minima/LICENSE.txt、
  vme-wren 97≠128）——清单权威=归档解包+GitHub 树，如实入账；
- 仓库根 LICENSE.README（许可映射权威）逐字：
    "Licensed under CC BY-SA 4.0:
     - All the demo files provided in demos/*"
  即 demo 集默认许可=CC-BY-SA-4.0（许可原文=仓库根 LICENSE.CC-BY-SA-4.0）；
- demos/ 下 18 个目录，其中 6 个带目录级许可文件（目录级更具体声明优先
  于仓库映射）：Apache-2.0 ×2（jetson-agx-thor-baseboard、tiny_tapeout）、
  CC-BY-SA-4.0 ×1（openair-max）、CERN-OHL-P-2.0 ×1（royalblue54L_feather）、
  CERN-OHL-S-2.0 ×1（cm5_minima）、CC-BY-NC-SA-4.0 ×1（stickhub）；
- r2 声称修正：r2 记录 "demos/cm5_minima/LICENSE.txt = Boost Software
  License 1.0"，实测该文件原文=CERN Open Hardware Licence Version 2 -
  Strongly Reciprocal（CERN-OHL-S-2.0）——r2 声称与原文不符，本包以
  原文为准（批判性执行：工具验证优先于先前记录）；
- 分类（18 demo）：retain 15（默认 CC-BY-SA-4.0 ×11 + 显式宽松 ×4）/
  not_available 1（simulation：零 .kicad_pcb，纯原理图/仿真模型 demo，
  无板可留）/ blocked 1（stickhub：CC-BY-NC-SA-4.0，NonCommercial=
  禁止性条款）/ copyleft 保守排除 1（cm5_minima：CERN-OHL-S-2.0 强互惠，
  与 pcbench GPL 保守排除同口径——非不合规判定，语料洁净度排除）；
- 留存内容=板文件+工程文件（.kicad_pcb/.kicad_pro/.kicad_sch/.kicad_sym/
  .kicad_mod/.kicad_wks/.kicad_dru/fp-lib-table/sym-lib-table）+许可/
  README 原文；3D 模型（step/stp/wrl/wings）、制造产物（gbr/drl/gbrjob/
  pos/zip）、文档 PDF、图像、杂项二进制不入库（逐目录 skip 计数入账）；
- 板格式=KiCad 8.99–10.99（version token 20241030–20260624），现行
  转换器兼容域（20171130）之外——本包零转换零 profile（如实；真实
  profile 转换属下一包）；
- 分母纪律：evaluated=18 demo（claimed/评估字段）；实际分母=合规留存
  17 板（18 个板文件：multichannel_mixer 同板双态 unrouted+routed）。

split：按 demo 目录（=project_group）整组划分；demo_id 字典序末 3 组=
holdout，validation 空=如实（demo 数少，简分）；holdout frozen_readonly。

生成器纪律：纯函数、零子进程、零自身落盘、零网络、零 wall-clock
（AUDIT_DATE 为声明常量）、零主机路径（编排侧 scripts/s15_kicad_demo.py
读盘/落盘；本模块只装配）。
"""

from __future__ import annotations

import re

from . import corpus, hashing

TRACK = "tl5-kicad-demos-r1"
MODULE_NAME = "pcbflow.corpus_kicad_demo"
DATASET_ID = "kicad-demos-r1"

#: 审计/采集声明日期（人工会话声明，非机器 wall-clock）
AUDIT_DATE = "2026-09-05"

# ---------------------------------------------------------------------------
# 1. 上游与归档源（S15 会话实测常量）
# ---------------------------------------------------------------------------

UPSTREAM_URI = "https://gitlab.com/kicad/code/kicad"
MIRROR_URI = "https://github.com/KiCad/kicad-source-mirror"
PIN_COMMIT = "10fd71558f001f74f179127e5f7ef335f9dd3304"
PIN_COMMIT_SHORT = "10fd7155"
ARCHIVE_URL = ("https://gitlab.com/api/v4/projects/kicad%2Fcode%2Fkicad"
               "/repository/archive.tar.gz"
               "?sha=" + PIN_COMMIT + "&path=demos")
ARCHIVE_SHA256 = "1ee5135d8516d6e8d24d7efd77a08b1b46b4877069eaa893dff8da7421d6fc2b"
ARCHIVE_SIZE_BYTES = 96489574
#: GitHub 镜像 recursive git tree（truncated=false）blobs 数=归档解包文件数
UPSTREAM_FILE_COUNT = 709

#: 仓库根 LICENSE.README 的 demo 许可映射（逐字引文；证据 sha256 由编排侧
#: 对归档解包实测后注入 audit 记录）
LICENSE_README_QUOTE = (
    "Licensed under CC BY-SA 4.0:\n"
    " - All the demo files provided in demos/*"
)
DEFAULT_DEMO_LICENSE_ID = "CC-BY-SA-4.0"

# ---------------------------------------------------------------------------
# 2. 逐 demo 审计事实表（S15 会话实测；decision 由 classify_demo_license
#    从事实重放得出，不手工写结论）
# ---------------------------------------------------------------------------

#: 目录级许可文件识别出的 license id（原文全文随 audit/留存入账）
LICENSE_APACHE = "Apache-2.0"
LICENSE_CCBYSA = "CC-BY-SA-4.0"
LICENSE_CERN_P = "CERN-OHL-P-2.0"
LICENSE_CERN_S = "CERN-OHL-S-2.0"
LICENSE_CC_NC_SA = "CC-BY-NC-SA-4.0"

#: 宽松许可（允许留存与派生分析；CC-BY-SA 同许可传递义务照旧）
PERMISSIVE_DIR_LICENSES = frozenset({
    LICENSE_APACHE, LICENSE_CCBYSA, LICENSE_CERN_P,
})
#: copyleft/互惠家族（识别明确但保守排除，非不合规判定）
COPYLEFT_DIR_LICENSES = frozenset({
    LICENSE_CERN_S, "GPL-3.0", "GPL-2.0", "AGPL-3.0", "LGPL-2.1",
    "LGPL-3.0", "MPL-2.0", "CERN-OHL-W-2.0",
})
#: 禁止性条款（NonCommercial/NoDerivs 明示）
PROHIBITIVE_DIR_LICENSES = frozenset({
    LICENSE_CC_NC_SA, "CC-BY-NC-4.0", "CC-BY-ND-4.0",
})

# 板文件（demos 相对路径）；multichannel_mixer 双态按上游文件名
BOARD_FILES = {
    "complex_hierarchy": ["complex_hierarchy/complex_hierarchy.kicad_pcb"],
    "constraints": ["constraints/constraints.kicad_pcb"],
    "ecc83": ["ecc83/ecc83-pp.kicad_pcb", "ecc83/ecc83-pp_v2.kicad_pcb"],
    "interf_u": ["interf_u/interf_u.kicad_pcb"],
    "jetson-agx-thor-baseboard":
        ["jetson-agx-thor-baseboard/jetson-agx-thor-baseboard.kicad_pcb"],
    "kit-dev-coldfire-xilinx_5213":
        ["kit-dev-coldfire-xilinx_5213/"
         "kit-dev-coldfire-xilinx_5213.kicad_pcb"],
    "microwave": ["microwave/microwave.kicad_pcb"],
    "multichannel": ["multichannel/multichannel_mixer.kicad_pcb",
                     "multichannel/multichannel_mixer-unrouted.kicad_pcb"],
    "openair-max": ["openair-max/One-Air-Max.kicad_pcb"],
    "pic_programmer": ["pic_programmer/pic_programmer.kicad_pcb"],
    "royalblue54L_feather":
        ["royalblue54L_feather/RoyalBlue54L-Feather.kicad_pcb",
         "royalblue54L_feather/nfc_antenna/RoyalBlue54L-NFC-Antenna/"
         "RoyalBlue54L-NFC-Antenna.kicad_pcb"],
    "sonde_xilinx": ["sonde xilinx/sonde xilinx.kicad_pcb"],
    "tiny_tapeout": ["tiny_tapeout/tinytapeout-demo.kicad_pcb"],
    "video": ["video/video.kicad_pcb"],
    "vme-wren": ["vme-wren/vme-wren.kicad_pcb"],
    "simulation": [],
    "stickhub": ["stickhub/StickHub.kicad_pcb"],
    "cm5_minima": ["cm5_minima/CM5_MINIMA_3.kicad_pcb"],
}

#: 目录级许可文件（demos 相对路径；None=无目录级许可→默认仓库映射）
DIR_LICENSE_FILE = {
    "complex_hierarchy": None,
    "constraints": None,
    "ecc83": None,
    "interf_u": None,
    "jetson-agx-thor-baseboard": "jetson-agx-thor-baseboard/LICENSE",
    "kit-dev-coldfire-xilinx_5213": None,
    "microwave": None,
    "multichannel": None,
    "openair-max": "openair-max/LICENSE.txt",
    "pic_programmer": None,
    "royalblue54L_feather": "royalblue54L_feather/LICENSE",
    "sonde_xilinx": None,
    "tiny_tapeout": "tiny_tapeout/LICENSE.txt",
    "video": None,
    "vme-wren": None,
    "simulation": None,
    "stickhub": "stickhub/LICENSE.md",
    "cm5_minima": "cm5_minima/LICENSE.txt",
}

DIR_LICENSE_ID = {
    "jetson-agx-thor-baseboard": LICENSE_APACHE,
    "openair-max": LICENSE_CCBYSA,
    "royalblue54L_feather": LICENSE_CERN_P,
    "tiny_tapeout": LICENSE_APACHE,
    "stickhub": LICENSE_CC_NC_SA,
    "cm5_minima": LICENSE_CERN_S,
}

#: 板 id 归属 override：上游文件名含状态后缀的变体文件归属同板
#: （multichannel_mixer-unrouted.kicad_pcb = multichannel/multichannel_mixer
#:  的 unrouted 态；revision 由 board_revision 给出）
BOARD_ID_OF_FILE = {
    "multichannel/multichannel_mixer-unrouted.kicad_pcb":
        "multichannel/multichannel_mixer",
}

#: 上游目录名（demo_id≠上游名处如实的还原；其余=同名）
UPSTREAM_DIR = {
    "sonde_xilinx": "sonde xilinx",
}

#: 上游文件名明示的板状态（multichannel_mixer 双态；其余=as_shipped）
BOARD_REVISIONS = {
    "multichannel/multichannel_mixer.kicad_pcb": "routed",
    "multichannel/multichannel_mixer-unrouted.kicad_pcb": "unrouted",
}

#: demo_id 字典序末 N 组=holdout（简分规则；demo 数少，validation 空=如实）
HOLDOUT_DEMO_COUNT = 3


def sanitize_demo_id(name: str) -> str:
    """上游目录名 → dataset 目录 id（v3 manifest 路径字符集兼容）。

    仅 "sonde xilinx"→"sonde_xilinx" 需要变换；其余 demo 原名已兼容。
    产生空结果或仍不匹配 ^[A-Za-z0-9._+-]+$ 即 ValueError（fail-closed）。
    """
    s = re.sub(r"[^A-Za-z0-9._+-]+", "_", name).strip("_")
    if not s or not re.fullmatch(r"[A-Za-z0-9._+-]+", s):
        raise ValueError(f"unsanitizable demo id: {name!r} -> {s!r}")
    return s


def demo_board_id(demo_id: str, board_file: str) -> str:
    """板 id="<demo_id>/<板文件 stem（路径安全化）>"；唯一性由表保证。

    状态后缀变体（如 -unrouted）经 BOARD_ID_OF_FILE 归属同板（revision
    区分）；无 override 者=stem 原名。
    """
    if board_file in BOARD_ID_OF_FILE:
        return BOARD_ID_OF_FILE[board_file]
    stem = board_file.rsplit("/", 1)[-1][:-len(".kicad_pcb")]
    stem = stem.replace(" ", "_")
    return f"{demo_id}/{stem}"


def board_revision(board_file: str) -> str:
    """板状态标签：上游文件名明示者（unrouted/routed）按名；余=as_shipped。"""
    return BOARD_REVISIONS.get(board_file, "as_shipped")


def classify_demo_license(dir_license_id: str | None,
                          board_file_count: int) -> dict:
    """逐 demo 许可分类（纯函数）。

    优先级：无板=not_available（no_board_files）> 目录级显式许可 >
    仓库映射默认 CC-BY-SA-4.0。目录级许可按三类：宽松=retain；
    copyleft/互惠=保守排除（非不合规判定）；NC/ND=禁止性条款 blocked。
    """
    if board_file_count <= 0:
        return {"decision": "not_available",
                "reason_code": "no_board_files",
                "license_id": DEFAULT_DEMO_LICENSE_ID}
    if dir_license_id is None:
        return {"decision": "retain",
                "reason_code": "retain_default_repo_mapping",
                "license_id": DEFAULT_DEMO_LICENSE_ID}
    if dir_license_id in PERMISSIVE_DIR_LICENSES:
        return {"decision": "retain",
                "reason_code": "retain_dir_license_permissive",
                "license_id": dir_license_id}
    if dir_license_id in COPYLEFT_DIR_LICENSES:
        return {"decision": "exclude",
                "reason_code": "copyleft_conservative_exclusion",
                "license_id": dir_license_id}
    if dir_license_id in PROHIBITIVE_DIR_LICENSES:
        return {"decision": "blocked",
                "reason_code": "prohibitive_noncommercial",
                "license_id": dir_license_id}
    return {"decision": "blocked",
            "reason_code": "license_unrecognized",
            "license_id": dir_license_id}


def build_demo_audit_ledger(demo_entries: list) -> dict:
    """逐 demo 审计账本（纯装配；与 corpus_pcbench.build_retention_ledger
    同构）。

    demo_entries: [{demo_id, board_files: [demos 相对路径]}]；
    目录级许可事实取自本模块常量表（表=会话实测，缺失即 KeyError fail）。
    返回 {retained, excluded, counts, evaluated}；decision 从
    classify_demo_license 重放，重放结果与 demo_entries 板文件数一致。
    """
    retained, excluded = [], []
    for e in demo_entries:
        demo_id = e["demo_id"]
        if demo_id not in DIR_LICENSE_FILE:
            raise KeyError(f"unknown demo_id: {demo_id}")
        board_files = list(e["board_files"])
        expected = BOARD_FILES[demo_id]
        if sorted(board_files) != sorted(expected):
            raise ValueError(
                f"board files mismatch for {demo_id}: {board_files}")
        lic = classify_demo_license(DIR_LICENSE_ID.get(demo_id),
                                    len(board_files))
        upstream_dir = UPSTREAM_DIR.get(demo_id, demo_id)
        entry = {
            "demo_id": demo_id,
            "upstream_dir": upstream_dir,
            "license_id": lic["license_id"],
            "reason_code": lic["reason_code"],
            "dir_license_file": DIR_LICENSE_FILE[demo_id],
            "board_file_count": len(board_files),
            "board_files": sorted(board_files),
            "project_group": (f"{UPSTREAM_URI}/-/tree/{PIN_COMMIT}"
                              f"/demos/{upstream_dir}"),
        }
        if lic["decision"] == "retain":
            retained.append(entry)
        else:
            excluded.append(dict(entry, decision=lic["decision"]))
    counts = {
        "evaluated": len(retained) + len(excluded),
        "retained_demos": len(retained),
        "retained_board_files": sum(e["board_file_count"]
                                    for e in retained),
        "not_available": sum(1 for x in excluded
                             if x["decision"] == "not_available"),
        "blocked": sum(1 for x in excluded if x["decision"] == "blocked"),
        "copyleft_conservative_exclusion":
            sum(1 for x in excluded
                if x["reason_code"] == "copyleft_conservative_exclusion"),
    }
    return {
        "track": TRACK, "audit_date": AUDIT_DATE,
        "pin_commit": PIN_COMMIT,
        "retained": sorted(retained, key=lambda x: x["demo_id"]),
        "excluded": sorted(excluded, key=lambda x: x["demo_id"]),
        "counts": counts,
    }


# ---------------------------------------------------------------------------
# 3. 留存文件白名单（工程/板/许可；渲染与制造产物不入库）
# ---------------------------------------------------------------------------

RETAIN_EXTENSIONS = frozenset({
    ".kicad_pcb", ".kicad_pro", ".kicad_sch", ".kicad_sym",
    ".kicad_mod", ".kicad_wks", ".kicad_dru",
})
#: 无扩展名工程文件（fp-lib-table / sym-lib-table）
RETAIN_NOEXT_BASENAMES = frozenset({"fp-lib-table", "sym-lib-table"})
#: 许可/说明原文（前缀匹配，大小写不敏感）
RETAIN_NAME_PREFIXES = ("license", "copying", "readme")

#: 不入库类别（编排侧按扩展名归类计数，逐 demo 入账）
SKIP_CATEGORIES = {
    ".step": "3d_model", ".stp": "3d_model", ".wrl": "3d_model",
    ".wings": "3d_model",
    ".gbr": "fabrication", ".drl": "fabrication", ".gbrjob": "fabrication",
    ".pos": "fabrication", ".zip": "fabrication",
    ".pdf": "document", ".jpg": "image", ".jpeg": "image", ".png": "image",
    ".svg": "image", ".bmp": "image",
    ".bin": "misc_binary", ".db": "misc_binary", ".json": "plugin_config",
    ".txt": "tool_data", ".lib": "sim_model", ".mod": "sim_model",
    ".model": "sim_model", ".ibs": "sim_model", ".cir": "sim_model",
    ".wbk": "sim_model",
}


def classify_retention_file(basename: str) -> tuple:
    """文件名 → (keep: bool, category: str)。纯函数。"""
    low = basename.lower()
    stem, ext = os_splitext(low)
    if low.startswith(RETAIN_NAME_PREFIXES):
        return True, "license_or_readme"
    if stem in RETAIN_NOEXT_BASENAMES:
        return True, "project_file"
    if ext in RETAIN_EXTENSIONS:
        return True, "board_or_project_file"
    if ext in SKIP_CATEGORIES:
        return False, SKIP_CATEGORIES[ext]
    return False, "unrecognized"


def os_splitext(name: str) -> tuple:
    """basename 的 (stem, ext)（ext 含点，小写）；供 classify 使用。"""
    i = name.rfind(".")
    if i <= 0:
        return name, ""
    return name[:i], name[i:]


# ---------------------------------------------------------------------------
# 4. 板文本 survey（版本 token + 拓扑签名；KiCad 8.99–10.99 s-expr）
# ---------------------------------------------------------------------------

def survey_board_text(text: str) -> dict:
    """板文本 survey：version token/generator/实体计数（一阶正则计数，
    不解析语义；跨格式容忍 module/footprint 并集，同 corpus.topology_signature）。"""
    sig = corpus.topology_signature(text)
    version = re.search(r"\(version\s+(\w+)\)", text)
    generator = re.search(r'\(generator_version\s+"([^"]+)"\)', text)
    zones = len(re.findall(r"\(zone\s", text))
    return {
        "version_token": version.group(1) if version else "not_available",
        "generator_version": generator.group(1) if generator
        else "not_available",
        "signature": sig,
        "zone_count": zones,
    }


def topology_group_id(sig: dict) -> str:
    """拓扑组 id：签名 canonical JSON 的 sha256 前 16 hex（稳定、可复算）。"""
    body = hashing.canonical_json_bytes({
        "net_count": sig["net_count"],
        "footprint_count": sig["footprint_count"],
        "pad_count": sig["pad_count"],
        "via_count": sig["via_count"],
        "segment_count": sig["segment_count"],
        "named_net_count": sig["named_net_count"],
        "net_name_multiset_sha256": sig["net_name_multiset_sha256"],
    })
    return "ktd-topo-" + hashing.sha256_bytes(body)[:16]


# ---------------------------------------------------------------------------
# 5. split（demo 组整组；字典序末 N 组=holdout）
# ---------------------------------------------------------------------------

def assign_demo_splits(demo_boards: dict) -> dict:
    """按 demo 目录整组简分：demo_id 字典序，末 HOLDOUT_DEMO_COUNT 组=
    holdout；validation 空（demo 数少=如实；禁止同板随机切分）。

    demo_boards: {demo_id: [board_id, ...]} → splits dict（含组级计数与
    frozen 声明）；corpus.audit_split_cross 复核通过为使用前提（测试强制）。
    """
    if len(demo_boards) <= HOLDOUT_DEMO_COUNT:
        raise ValueError("too few demos for train/holdout simple split")
    ordered = sorted(demo_boards)
    holdout = ordered[-HOLDOUT_DEMO_COUNT:]
    train = ordered[:-HOLDOUT_DEMO_COUNT]
    boards = lambda ds: sorted(b for d in ds for b in demo_boards[d])
    splits = {
        "train": boards(train),
        "validation": [],
        "holdout": boards(holdout),
        "external_eval": [],
        "holdout_frozen_readonly": True,
        "split_unit": "board（组=demo 目录整组划分：同 demo 多板/双态"
                      "不跨侧，禁止同板随机切分）",
        "split_rule": (f"demo_id 字典序，末 {HOLDOUT_DEMO_COUNT} 组="
                       "holdout（简分，~20%）；validation 空=如实"
                       "（demo 数少）；train=其余"),
        "group_counts": {"train": len(train),
                         "validation": 0,
                         "holdout": len(holdout)},
    }
    return splits


# ---------------------------------------------------------------------------
# 6. 跨库去重（vs pcbbenchmarks-r1 + pcbench-r1）
# ---------------------------------------------------------------------------

def audit_cross_library(own_items: list, other_items: list) -> dict:
    """跨库内容/拓扑去重（纯函数）。

    own_items/other_items: [{library, board_id, file_role, text}]；
    内容指纹=corpus.content_fingerprint（空白归一）并集去重（决定性）；
    拓扑组=同 signature 键并集分组（补充性，如实记录重叠不判泄漏）。
    返回与既有 leakage-audit-pcbench-r1.json 的 cross_library_dedup
    同形的结果。
    """
    items = []
    for it in own_items:
        items.append({"board_id": it["board_id"],
                      "file_role": it["file_role"],
                      "content_sha256":
                          corpus.content_fingerprint(it["text"])})
    for it in other_items:
        items.append({"board_id": it["board_id"],
                      "file_role": it["file_role"],
                      "content_sha256":
                          corpus.content_fingerprint(it["text"])})
    content = corpus.audit_content_dedup(items)
    sigs = []
    for it in own_items + other_items:
        s = survey_board_text(it["text"])["signature"]
        sigs.append(dict(s, board_id=it["board_id"]))
    topo = corpus.audit_topology_dedup(sigs)
    dup_count = content["duplicate_group_count"]
    return {
        "track": TRACK, "audit_date": AUDIT_DATE,
        "method": ("corpus.content_fingerprint（空白归一）跨库并集去重："
                   "kicad-demos-r1 全部板文件 vs pcbbenchmarks-r1+"
                   "pcbench-r1 全部 .kicad_pcb；拓扑签名并集分组为补充"
                   "证据（重叠如实记录，不单独判泄漏）"),
        "own_board_files": len(own_items),
        "other_board_files": len(other_items),
        "content_duplicate_groups": content["duplicate_groups"],
        "content_duplicate_group_count": dup_count,
        "topology_overlap_groups": topo["topology_duplicate_groups"],
        "topology_overlap_group_count":
            topo["topology_duplicate_group_count"],
        "result": ("cross_library_duplicates_found" if dup_count
                   else "no_cross_library_duplicates"),
    }


# ---------------------------------------------------------------------------
# 7. TD8 manifest record 装配（corpus.build_dataset_manifest 输入侧）
# ---------------------------------------------------------------------------

def build_kicad_demo_manifest_record(*, board_ids: list, revision_ids: list,
                                     raw_files: list, dataset_splits: dict,
                                     project_groups: list,
                                     topology_groups: list,
                                     kicad_version_field: str,
                                     source_archive: dict,
                                     source_research_ref: dict,
                                     excluded_summary: dict,
                                     audit_ref: dict) -> dict:
    """kicad-demos-r1 v1 的 TD8 record；manifest_sha256/raw_hash 由
    corpus.build_dataset_manifest 实算。无据字段如实 not_available/说明。"""
    return {
        "dataset_id": DATASET_ID,
        "version": "1",
        "source_uri_or_archive_sha256": source_archive,
        "license": (
            "mixed per-demo（默认=仓库根 LICENSE.README 映射 "
            "CC-BY-SA-4.0 \"All the demo files provided in demos/*\"；"
            "目录级显式许可优先：Apache-2.0（jetson-agx-thor-baseboard/"
            "tiny_tapeout）、CC-BY-SA-4.0（openair-max）、CERN-OHL-P-2.0"
            "（royalblue54L_feather）；许可原文随 raw/ 逐 demo 存档）"),
        "license_scope": {
            "default_mapping": "LICENSE.README（仓库根许可映射）"
                               "→CC-BY-SA-4.0 覆盖 demos/* 全部文件",
            "dir_level_override": "demo 目录内 LICENSE 文件=更具体声明，"
                                  "优先于仓库映射",
            "board_files": "KiCad 官方 demo 设计文件；attribution=来源"
                           " URL（project_group，pin commit）+许可原文"
                           "随档；CC-BY-SA 板再分发须署名+同许可传递",
            "derivative_analysis": True,
            "local_retention": True,
            "redistribution": "retain 子集可再分发（按各 demo 条款署名；"
                              "CC-BY-SA 同许可传递；CERN-OHL-P 按 P 条款"
                              "）；本仓不发布不分发",
            "excluded_rationale": (
                "cm5_minima=CERN-OHL-S-2.0（强互惠/copyleft 家族）保守"
                "排除（与 pcbench GPL 同口径，非不合规判定）；stickhub="
                "CC-BY-NC-SA-4.0 NonCommercial 禁止性条款 blocked；"
                "simulation=无板文件 not_available"),
        },
        "redistribution_allowed": True,
        "derivative_allowed": True,
        "attribution": True,
        "collection_date": AUDIT_DATE,
        "board_ids": board_ids,
        "revision_ids": revision_ids,
        "project_groups": project_groups,
        "topology_groups": topology_groups,
        "vendor_groups": ("not_available（KiCad 官方 demo 集=项目自有/"
                          "贡献者混合，无厂商归属语义；demo 目录=分组"
                          "单位，作者线索随 demo README/板 title block"
                          " 存档于 raw/）"),
        "consent_or_provenance": (
            "KiCad 官方仓库 demos/ 子树（双 host：gitlab.com/kicad/code/"
            "kicad 与 github.com/KiCad/kicad-source-mirror 同 commit "
            + PIN_COMMIT + " 同步验证）；获取=GitLab archive API "
            "demos 子树 tarball 单次只读下载（96,489,574B，sha256 "
            "1ee5135d…），解包 709 文件与 GitHub 镜像 git tree 枚举"
            "（truncated=false）全等+git blob sha1 全量校验零 mismatch"
            "+GitLab files API 抽样逐字节一致；零安装脚本零执行；"
            "许可映射证据=仓库根 LICENSE.README 逐字引文+6 个目录级"
            "许可原文全文存档"),
        "conversion_script": {
            "modules": {MODULE_NAME: {
                "role": "逐 demo 许可分类/审计账本/白名单/板 survey/"
                        "split/跨库去重/manifest 装配（纯函数）",
                "module_sha256": "not_available（由编排侧 scripts/"
                                 "s15_kicad_demo.py 实测注入）",
            }},
            "entry_points": [
                "corpus_kicad_demo.classify_demo_license",
                "corpus_kicad_demo.build_demo_audit_ledger",
                "corpus_kicad_demo.classify_retention_file",
                "corpus_kicad_demo.survey_board_text",
                "corpus_kicad_demo.topology_group_id",
                "corpus_kicad_demo.assign_demo_splits",
                "corpus_kicad_demo.audit_cross_library",
                "corpus_kicad_demo.build_kicad_demo_manifest_record",
            ],
            "replay_contract": "纯函数：输入=demos 归档解包文件文本+注入 "
                               "hash；输出=审计账本/manifest record；落盘"
                               "由编排侧完成（零子进程/零自身落盘/零网络）",
            "tests": "tests/test_tl5_kicad_demo.py",
            "track": TRACK,
        },
        "kicad_version": kicad_version_field,
        "raw_files": raw_files,
        "normalized_hash": corpus.NA,
        "conversion_log": corpus.NA,
        "field_missingness": {
            "normalized_hash": "not_available（本包零转换零 profile：板为"
                               " KiCad 8.99–10.99 格式，现行转换器兼容域"
                               "（20171130）外；真实 profile 转换属下一包）",
            "conversion_log": "not_available（同上）",
            "DRC_baseline": "not_available（未跑 kicad-cli DRC；本包范围"
                            "=许可审计+合规留存）",
            "dataset_splits.external_eval": "空（无外部评测源）",
            "dataset_splits.validation": "空（15 demo 简分：train/holdout"
                                         " 两分，validation 空=如实）",
            "manifest_path_rename": "1 个上游目录名含空格（sonde xilinx）"
                                    "→dataset id/文件名安全化为 sonde_"
                                    "xilinx（原始名逐条入账，内容零改动）",
            "retention_scope": "3D 模型/制造产物（gbr/drl/pos/zip）/文档 "
                               "PDF/图像/杂项二进制不入库（逐 demo skip "
                               "计数见 license-audit）",
            "gitlab_tree_undercount": "GitLab 递归 tree API 逐目录漏报"
                                      "（cm5_minima/LICENSE.txt、vme-wren "
                                      "97≠128）——清单权威=归档解包 709 "
                                      "文件+GitHub 镜像 git tree"
                                      "（truncated=false）全等",
            "excluded_boards_full_ledger": excluded_summary,
            "license_audit_ref": audit_ref,
        },
        "DRC_baseline": "not_available（本包未跑 kicad-cli DRC）",
        "dataset_splits": dataset_splits,
        "excluded_boards": excluded_summary,
        "source_research_ref": source_research_ref,
    }
