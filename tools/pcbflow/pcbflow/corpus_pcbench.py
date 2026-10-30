"""TL-5 第三包：PCBench（SRC-PCBENCH）审计登记、合规子集保留与三分 split。

审计结论（2026-09-03 S7 会话实测，明细见 out/v3-tl5/source-research-r3.json）：
- 仓库根 LICENSE=MIT（Copyright (c) 2023 PCBench）——MIT 覆盖集合仓库自身
  代码（Scripts/RLEnv/数据增强等），**不自动覆盖** PCBs/ 下聚合的第三方
  板文件（板来自 846 上游 GitHub 仓库，仓库内除根 LICENSE 外零板级
  license 文件——git tree 实测）；
- 逐板许可的唯一证据=master_metadata.json 的 licenses 字段（爬取时
  2023-08-17 自 GitHub API / kitspace 记录）：null 612、NOASSERTION 96、
  空串 19、list 混合（GNU/CERN/泛 CC 等）、dict SPDX 明示若干——板许可
  混合 ⇒ 结论三选一取**仅代码 MIT、板许可混合，只留可证子集**；
- 保留规则（可证子集）：licenses 字段可证为宽松许可（下方两个白名单）且
  板格式 KiCad5(version 20171130，现行转换器/工具链兼容域) → 82 板；
  copyleft 家族（GPL/AGPL/LGPL/MPL）排除理由=派生 profile 的 copyleft
  语义对硬件设计文件的适用性未定（保守排除，非不合规判定）；CERN OHL
  （版本不明）/泛 Creative Commons（NC/ND 可能）/License not found/
  NOASSERTION/null/空串=许可不明零留存。

split：按上游仓库组（project_group=source URL）三分
train/validation/holdout——组级整组划分，同组绝不跨 train/validation 与
holdout 边界；holdout frozen_readonly=true。禁止同板随机切分。

生成器纪律：纯函数、零子进程、零自身落盘、零网络、零 wall-clock
（AUDIT_DATE 为声明常量）、零主机路径。
"""

from __future__ import annotations

import json
import re

TRACK = "tl5-pcbench-r1"
MODULE_NAME = "pcbflow.corpus_pcbench"

#: 审计/采集声明日期（人工会话声明，非机器 wall-clock）
AUDIT_DATE = "2026-09-03"

#: dict 型 licenses（GitHub API SPDX）白名单——宽松许可（允许本地留存、
#: 派生分析、再分发须署名/同许可传递按各自条款）
PERMISSIVE_SPDX = frozenset({
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
    "BSD-3-Clause-Clear", "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0",
    "Unlicense", "WTFPL",
})

#: list 型 licenses（[{name, link}]，kitspace 等来源）名字白名单——名字
#: 无歧义且带 license 原文链接（证据可溯）
PERMISSIVE_LIST_NAMES = frozenset({
    "MIT", "MIT License", "BSD", "Apache", "The Unlicense",
    "Creative Commons Attribution Share Alike 4.0 International",
})

#: copyleft 家族（识别明确但保守排除：派生 profile 的 copyleft 语义对
#: 硬件设计文件适用性未定；本地研究用本不违规，为语料洁净度排除）
COPYLEFT_SPDX = frozenset({
    "GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "MPL-2.0",
})

#: 排除的 list 型许可名字（版本/条款不明）
EXCLUDED_LIST_NAMES = frozenset({
    "GNU", "GNU General Public License v2.0", "GPL", "CERN",
    "Creative Commons", "License not found", "TAPR",
})

#: 三分比例（按板数；组级分配只近似逼近）
SPLIT_RATIOS = {"train": 0.7, "validation": 0.15, "holdout": 0.15}

#: 转换器兼容域（corpus_convert.parse_kicad5_board 期望的板版本字面量）
KICAD5_BOARD_VERSION = "20171130"


# ---------------------------------------------------------------------------
# 1. 逐板许可分类（纯函数；输入=master_metadata 的 licenses 字段）
# ---------------------------------------------------------------------------

def classify_board_license(licenses_field) -> dict:
    """licenses 字段 → {decision: retain|exclude, reason_code, license_id}。

    retain 条件（全部满足）：
      dict 型：spdx_id ∈ PERMISSIVE_SPDX；
      list 型：非空且全部条目 name ∈ PERMISSIVE_LIST_NAMES（证据 link 由
        调用方入账）。
    exclude 的 reason_code 枚举见实现（许可不明/版本不明/copyleft 保守排除）。
    """
    if licenses_field is None:
        return {"decision": "exclude", "reason_code": "license_null",
                "license_id": None}
    if isinstance(licenses_field, str):
        # 实测均为空串——上游爬虫未取得 license
        return {"decision": "exclude", "reason_code": "license_empty_str",
                "license_id": None if not licenses_field.strip()
                else licenses_field}
    if isinstance(licenses_field, dict):
        spdx = licenses_field.get("spdx_id")
        if spdx in PERMISSIVE_SPDX:
            return {"decision": "retain",
                    "reason_code": "retain_permissive_spdx",
                    "license_id": spdx}
        if spdx in COPYLEFT_SPDX:
            return {"decision": "exclude",
                    "reason_code": "copyleft_conservative_exclusion",
                    "license_id": spdx}
        if spdx == "NOASSERTION":
            return {"decision": "exclude",
                    "reason_code": "license_noassertion", "license_id": spdx}
        return {"decision": "exclude", "reason_code": "license_spdx_other",
                "license_id": spdx}
    if isinstance(licenses_field, list):
        names = {i.get("name") for i in licenses_field if isinstance(i, dict)}
        if licenses_field and names and names <= PERMISSIVE_LIST_NAMES:
            return {"decision": "retain",
                    "reason_code": "retain_permissive_named_list",
                    "license_id": "+".join(sorted(names))}
        if names & EXCLUDED_LIST_NAMES:
            return {"decision": "exclude",
                    "reason_code": "list_license_version_or_terms_unknown",
                    "license_id": "+".join(sorted(names))}
        return {"decision": "exclude", "reason_code": "list_license_other",
                "license_id": "+".join(sorted(names))}
    return {"decision": "exclude", "reason_code": "license_field_untyped",
            "license_id": None}


def build_retention_ledger(board_entries: list,
                           duplicate_of: dict | None = None) -> dict:
    """逐板保留账本（纯装配）。

    board_entries: [{board_id, on_disk, kicad_version, licenses_field,
    source, author}] → {retained: [...], excluded: [...], counts}。
    kicad_version 非 KiCad5 字面量 = 格式域外排除（如实，非许可问题）。
    duplicate_of: {board_id: kept_board_id}——内容指纹完全一致的同库重复
    （编排侧实测后注入；保留字典序最小者，其余排除并入账）。
    """
    duplicate_of = duplicate_of or {}
    retained, excluded = [], []
    for e in board_entries:
        lic = classify_board_license(e["licenses_field"])
        if lic["decision"] != "retain":
            excluded.append({"board_id": e["board_id"],
                             "reason_code": lic["reason_code"],
                             "license_id": lic["license_id"]})
            continue
        if not e["on_disk"]:
            excluded.append({"board_id": e["board_id"],
                             "reason_code": "metadata_entry_without_disk_dir",
                             "license_id": lic["license_id"]})
            continue
        if e["kicad_version"] != KICAD5_BOARD_VERSION:
            excluded.append({"board_id": e["board_id"],
                             "reason_code": "kicad_version_out_of_scope",
                             "license_id": lic["license_id"]})
            continue
        if e["board_id"] in duplicate_of:
            excluded.append({"board_id": e["board_id"],
                             "reason_code": "duplicate_content_of:"
                                            + duplicate_of[e["board_id"]],
                             "license_id": lic["license_id"]})
            continue
        retained.append({
            "board_id": e["board_id"], "license_id": lic["license_id"],
            "reason_code": lic["reason_code"],
            "project_group": e["source"], "author": e["author"],
        })
    counts: dict = {"retained": len(retained), "excluded": len(excluded)}
    for x in excluded:
        counts[x["reason_code"]] = counts.get(x["reason_code"], 0) + 1
    return {"track": TRACK, "audit_date": AUDIT_DATE,
            "retained": sorted(retained, key=lambda x: x["board_id"]),
            "excluded": sorted(excluded, key=lambda x: x["board_id"]),
            "counts": dict(sorted(counts.items()))}


# ---------------------------------------------------------------------------
# 2. 三分 split（组级整组划分；确定性）
# ---------------------------------------------------------------------------

def assign_group_splits(group_boards: dict) -> dict:
    """按上游仓库组三分：train/validation/holdout。

    算法（确定性）：组名（source URL）字典序遍历，每步把整组划给
    "剩余容量最大"的角色（容量=target−已分配板数；并列按
    train>validation>holdout 次序）；target=round(N×ratio)，holdout=余数。
    收尾保证：validation/holdout 至少一组（不足时从 train 字典序末组移入
    ——板数 ≥3 组即不触发）。同组绝不跨 train/validation 与 holdout 边界
    （组级划分保证，corpus.audit_split_cross 复核）。
    """
    roles = ("train", "validation", "holdout")
    n = sum(len(v) for v in group_boards.values())
    target = {"train": round(n * SPLIT_RATIOS["train"]),
              "validation": round(n * SPLIT_RATIOS["validation"])}
    target["holdout"] = n - target["train"] - target["validation"]
    assigned = {r: [] for r in roles}
    counts = {r: 0 for r in roles}
    for g in sorted(group_boards):
        role = max(roles, key=lambda r: (target[r] - counts[r],
                                         -roles.index(r)))
        assigned[role].append(g)
        counts[role] += len(group_boards[g])
    # 边界保证（小组集情形；81 板/57 组不触发，测试覆盖触发路径）：仅当
    # train 移出后仍非空才补给空角色（组数 <3 时物理上无法三方非空——
    # 退化集如实保留空角色，corpus.audit_split_cross 对空角色不判违例）
    for r in ("validation", "holdout"):
        while not assigned[r] and len(assigned["train"]) > 1:
            moved = assigned["train"].pop()
            assigned[r].append(moved)
            counts[r] += len(group_boards[moved])
            counts["train"] -= len(group_boards[moved])
    splits = {}
    for r in roles:
        splits[r] = sorted(b for g in assigned[r]
                           for b in group_boards[g])
    splits.update({
        "split_unit": "board（组=上游仓库整组划分，禁止同板随机切分）",
        "holdout_frozen_readonly": True,
        "external_eval": [],
        "split_rule": "组名字典序贪心（剩余容量最大者得整组；并列 "
                      "train>validation>holdout）",
        "group_counts": {r: len(assigned[r]) for r in roles},
        "group_targets": dict(target),
    })
    return splits


# ---------------------------------------------------------------------------
# 3. unrouted 态确定性推导（PCBench 板=只有 routed 态）
# ---------------------------------------------------------------------------

def derive_unrouted_model(model: dict) -> dict:
    """从 processed（routed）板模型确定性推导 unrouted 态。

    PCBench 板实存 routed 态（raw=上游原始布线；processed=清洗后布线；
    final.json 自带 problem/solution 切分，solution=布线）——不存在
    pcbbenchmarks 式 unrouted 文件。推导=剥除 routed 几何：segment/via/arc
    计数清零 + general.tracks 置 "0"（normalized_board_text 本就丢弃 routed
    几何，此推导使 audit 的 unrouted_state_pristine 检查语义成立）。
    封装/焊盘/网表/层表原样保留（布局=设计起点）。纯深拷贝，不改入参。
    """
    out = json_deepcopy(model)
    out["segment_count"] = 0
    out["via_count"] = 0
    out["arc_count"] = 0
    general = dict(out.get("general") or {})
    general["tracks"] = "0"
    out["general"] = general
    out["derived_unrouted"] = {
        "basis": "routed_geometry_stripped",
        "source_state": "processed.kicad_pcb (routed, cleaned)",
        "stripped": ["segment", "via", "arc"],
        "note": "PCBench 无 unrouted 文件；推导与上游 final.json 的 "
                "problem/solution 切分同构（solution=布线）",
    }
    return out


def json_deepcopy(obj):
    return json.loads(json.dumps(obj))


def board_slug(board_id: str) -> str:
    """board_id → profile 目录名 slug（小写；非 [a-z0-9] 折叠为 '-'）。

    PCBench 目录名含空格/下划线/点/百分号编码（如 kitspace_Control%20Board）
    ——slug 只用于本地 profile 目录，board_id 原样入 dataset 账本。
    """
    s = re.sub(r"[^a-z0-9]+", "-", board_id.lower())
    return s.strip("-")


# ---------------------------------------------------------------------------
# 4. 转换选板（确定性规则，2–4 块）
# ---------------------------------------------------------------------------

#: v3 manifest 路径字符集（镜像 schemas._REL_POSIX——manifest inputs/backtest
#: 引用禁空格/%/{}/非 ASCII；含此类字符的板目录不可被 profile manifest 引用
#: → 转换候选如实排除（数据集保留不受影响：corpus 侧路径仅禁主机形态））
MANIFEST_PATH_RE_STR = r"^[A-Za-z0-9._/+-]+$"


def manifest_path_compatible(rel_path: str) -> bool:
    return bool(re.match(MANIFEST_PATH_RE_STR, rel_path))


def dataset_board_paths(board_id: str) -> dict:
    """板的仓库相对数据集路径（corpus 侧 canonical 引用形态）。"""
    base = f"datasets/pcbench-r1/raw/{board_id}"
    return {"processed": f"{base}/processed.kicad_pcb",
            "raw": f"{base}/raw.kicad_pcb"}


SELECTION_RULE = (
    "候选=保留板中 parse_ok 且 identity_ok（processed 与 raw 同板身份："
    "net id 序列与 module ref 多重集一致）且 manifest_path_ok（数据集相对"
    "路径匹配 v3 manifest 字符集 ^[A-Za-z0-9._/+-]+$——含空格/%/花括号的"
    "板目录名不可被 profile manifest 引用，如实排除不硬转）者；"
    "S1=候选中 2 铜层板字典序最小者；S2=候选中 4 铜层板字典序最小者"
    "（层多样性：cu4）；S3=候选字典序遍历取第一个 project_group ∉ {S1,S2} "
    "且 topology_group ∉ {S1,S2} 者；任一槽空则如实跳过不凑数"
)


def select_conversion_boards(candidates: list) -> list:
    """确定性选板（规则=SELECTION_RULE）。

    candidates: [{board_id, copper_layers, topology_group, project_group,
    parse_ok, identity_ok, manifest_path_ok}] → 选中项列表（含 slot 标注）。
    manifest_path_ok 可缺省（缺省=True，由调用方按实测传入）。
    """
    qual = sorted((c for c in candidates if c["parse_ok"]
                   and c["identity_ok"]
                   and c.get("manifest_path_ok", True)),
                  key=lambda c: c["board_id"])
    selected = []

    def pick(pred):
        for c in qual:
            if c["board_id"] in {s["board_id"] for s in selected}:
                continue
            if pred(c):
                return c
        return None

    s1 = pick(lambda c: c["copper_layers"] == 2)
    if s1:
        selected.append(dict(s1, slot="S1_2layer_lex_first"))
    s2 = pick(lambda c: c["copper_layers"] == 4)
    if s2:
        selected.append(dict(s2, slot="S2_4layer_lex_first"))
    used_groups = {s["project_group"] for s in selected}
    used_topo = {s["topology_group"] for s in selected}
    s3 = pick(lambda c: c["project_group"] not in used_groups
              and c["topology_group"] not in used_topo)
    if s3:
        selected.append(dict(s3, slot="S3_distinct_group_and_topology"))
    return selected


# ---------------------------------------------------------------------------
# 5. PCBench 转换日志（routed-only 库的如实账；corpus_convert 不改——bm 产物
#    的 module_sha256 重放声明保持有效）
# ---------------------------------------------------------------------------

def build_pcbench_conversion_log(*, board_id: str, profile_id: str,
                                 module_hashes: dict, inputs: list,
                                 outputs: list, model_u: dict, model_p: dict,
                                 model_r: dict, crit: dict,
                                 topology_group: str) -> dict:
    """PCBench 板转换日志（TD8；纯装配，hash 由编排侧实算注入）。

    与 corpus_convert.build_conversion_log 的差异（如实）：
    - 输入态语义：PCBench 只有 routed 态——unrouted 态=processed 确定性
      剥除 routed 几何推导（derive_unrouted_model）；routed 参考=raw；
    - dropped.zones 按本板实数记录（无 bm 日志的"两板均为 0"模板断言）；
    - 解析/规范化/构件函数仍=pcbflow.corpus_convert（原模块零改动）。
    """
    return {
        "track": TRACK, "conversion_date": AUDIT_DATE,
        "board_id": board_id, "profile_id": profile_id,
        "modules": {
            "pcbflow.corpus_convert": {
                "role": "parse/normalize/artifact 构件（原模块零改动）",
                "module_sha256": module_hashes["corpus_convert"]},
            "pcbflow.corpus_pcbench": {
                "role": "PCBench 审计/保留/split/选板/派生 unrouted/本日志",
                "module_sha256": module_hashes["corpus_pcbench"]},
        },
        "input_state_semantics": {
            "library_state": "routed-only（raw=上游原始 routed；"
                             "processed=清洗后 routed；PCBench 无 unrouted 文件）",
            "unrouted_derivation": "derive_unrouted_model(processed)："
                                   "segment/via/arc 清零+general.tracks=0"
                                   "（与上游 final.json problem/solution 切分"
                                   "同构，solution=布线）",
            "routed_reference": "raw.kicad_pcb（hash 绑定于 manifest.backtest"
                                ".reference_route）",
            "stripped_counts": {
                "segments": model_p["segment_count"] - model_u["segment_count"],
                "vias": model_p["via_count"] - model_u["via_count"],
                "arcs": model_p["arc_count"] - model_u["arc_count"]},
        },
        "inputs": inputs, "outputs": outputs,
        "retained": [
            "copper layer name/index/type", "net declarations (id+name)",
            "footprint ref/lib/layer/at", "pad name/type/shape/at/size/"
            "drill/layers/net", "placement（processed 的 at 字面量）",
        ],
        "dropped": {
            "fp_text_value_and_graphics": "fp_text 值文本/fp_poly/fp_line 等"
                                          "图形不进规范化板",
            "zones": f"zones 不进规范化板（processed zones="
                     f"{model_p['zone_count']}、raw zones="
                     f"{model_r['zone_count']}，原样留存于 datasets）",
            "setup_detail": "setup 细参只留最小值集（进 stackup.setup_mins）",
            "routed_geometry": f"processed routed segments={model_p['segment_count']} "
                               f"vias={model_p['via_count']} "
                               f"arcs={model_p['arc_count']} 剥除（unrouted 推导）；"
                               f"raw routed segments={model_r['segment_count']} "
                               f"vias={model_r['via_count']} 以 manifest.backtest"
                               f".reference_route hash 绑定为回测参考",
            "non_copper_layers": "非铜层不进规范化板（计数入 stackup."
                                 "non_copper_layer_count）",
            "final_json": "PCB-RDL final.json 未消费（.kicad_pcb 为权威输入；"
                          "随 datasets 留存备查）",
        },
        "convention_basis": crit["basis"],
        "field_missingness": {
            "anchors": "not_determinable（布局冻结集属项目决策，板文本无据）",
            "via_cost": "not_determinable（router 参数非板属性）",
            "length_match_tolerance": "not_determinable（无原理图/规范源）",
            "physics_required": "not_determinable（无介质参数/电流源）",
            "params": "空（搜索域不可从板文本判定）",
        },
        "parse_warnings": model_p["parse_warnings"]
                          + model_r["parse_warnings"],
        "topology_group": topology_group,
        "determinism_claim": "pure function of source text; byte-exact "
                             "replay（数值保留源字面量；canonical JSON）",
    }


# ---------------------------------------------------------------------------
# 6. TD8 manifest record 装配（corpus.build_dataset_manifest 的输入侧）
# ---------------------------------------------------------------------------

def build_pcbench_manifest_record(*, board_ids: list, raw_files: list,
                                  dataset_splits: dict,
                                  project_groups: list,
                                  topology_groups: list,
                                  conversion_script: dict,
                                  conversion_log: list,
                                  kicad_version_field,
                                  normalized_hash: str,
                                  excluded_summary: dict,
                                  source_archive: dict,
                                  source_research_ref: dict,
                                  drc_baseline) -> dict:
    """pcbench-r1 v1 的 TD8 record（license/board_ids/splits/raw_files 等）；
    manifest_sha256/raw_hash 由 corpus.build_dataset_manifest 实算。"""
    return {
        "dataset_id": "pcbench-r1",
        "version": "1",
        "source_uri_or_archive_sha256": source_archive,
        "license": "mixed per-board（master_metadata licenses 字段可证为宽松"
                   "许可的子集：MIT/Apache-2.0/BSD*/CC0/CC-BY(-SA)/Unlicense/"
                   "WTFPL；板级证据=raw/<board>/metadata.json 原样存档）；"
                   "集合仓库自身代码=MIT（raw/LICENSE 存档）——MIT 不覆盖板文件",
        "license_scope": {
            "collection_repo_code": "MIT（根 LICENSE；覆盖 Scripts/RLEnv/"
                                    "augmentation 等集合代码）",
            "board_files": "upstream 第三方设计，逐板 licenses 证据保留于"
                           " raw/<board>/metadata.json（attribution=source/"
                           "author 字段；CC-BY/CC-BY-SA 板随档满足署名）",
            "redistribution": "permissive-only 子集可再分发（按各板条款署名；"
                              "CC-BY-SA 同许可传递）；本仓不发布不分发",
            "derivative_analysis": True,
            "local_retention": True,
            "excluded_copyleft_rationale": "GPL/AGPL/LGPL/MPL 识别明确但保守"
                                           "排除（派生 profile 的 copyleft "
                                           "语义对硬件设计文件适用性未定）",
        },
        "redistribution_allowed": True,
        "derivative_allowed": True,
        "attribution": True,
        "collection_date": AUDIT_DATE,
        "board_ids": board_ids,
        "revision_ids": [f"{b}.processed" for b in board_ids]
                       + [f"{b}.raw" for b in board_ids],
        "project_groups": project_groups,
        "topology_groups": topology_groups,
        "vendor_groups": "not_available（板来自 846 上游社区仓库，无厂商归属"
                         "语义；author 字段逐板在 raw/<board>/metadata.json）",
        "consent_or_provenance": "PCBench 集合仓库（MIT 代码）自 846 上游 "
                                 "GitHub 仓库爬取（master_metadata：逐板 "
                                 "org/source/author/licenses/retrieved-at="
                                 "2023-08-17）；本仓获取=codeload tarball "
                                 "只读单次下载、零安装脚本零执行、宽松许可"
                                 "可证子集 82 板 + 三个集合文件落盘；选中"
                                 "转换板的上游现行 license 已 GitHub API "
                                 "逐仓复验（MIT）",
        "conversion_script": conversion_script,
        "kicad_version": kicad_version_field,
        "raw_files": raw_files,
        "normalized_hash": normalized_hash,
        "conversion_log": conversion_log,
        "field_missingness": {
            "archive_retention": "codeload 归档（165,099,022B）只读下载、"
                                 "sha256 入账，未整档留存（体积纪律）；留存="
                                 "宽松许可 81 板数据文件+LICENSE+README+"
                                 "master_metadata.json（330 文件）",
            "visual_png": "逐板 visual.png 未留存（渲染图非设计数据；"
                          "上游可复取）",
            "DRC_baseline.reproducibility": "DRC JSON 含 kicad-cli 自身 date "
                                            "字段（外部工具输出原样留存；重跑"
                                            "仅该字段变化，violations 可复算）",
            "DRC_baseline.scope": "3 块转换板的 routed 参考态（raw）；"
                                  "其余 78 板未跑 DRC（本包有界转换范围）",
            "normalized_hash.scope": "3 块转换 profile 的 inputs/derived 18 "
                                     "文件 aggregate；其余 78 板未转换",
            "conversion.scope": "有界转换 3/81 板（确定性选板规则见 "
                                "source-research-r3.conversion_selection）",
            "manifest_path_incompatible_boards": "4 块保留板目录名含空格/%/"
                                                 "花括号——v3 manifest 路径字符"
                                                 "集不兼容→不可转 profile"
                                                 "（数据集保留不受影响）："
                                                 "Blink-Eras_Blink Eras、"
                                                 "RF_SIGNAL_GENERATOR_HARDWARE_"
                                                 "RF Signal Generator、"
                                                 "cookiecutter-xsproduct_"
                                                 "{{cookiecutter.product_name}}、"
                                                 "kitspace_Control%20Board",
            "dataset_splits.external_eval": "空（无外部评测源）",
            "excluded_boards_full_ledger": excluded_summary,
        },
        "DRC_baseline": drc_baseline if drc_baseline is not None
        else "not_available（本包未跑 kicad-cli DRC）",
        "dataset_splits": dataset_splits,
        "excluded_boards": excluded_summary,
        "source_research_ref": source_research_ref,
    }
