# -*- coding: utf-8 -*-
"""sidecar 卫生静态检查脚本（P0 门：产出物全部落在允许目录且带 provenance 头）。

用法：python tools/check_sidecar.py [root]
默认检查 E:/ZCodeData/ZCodeProject/route-v5/out。退出码 0=全绿，1=有违例。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5 import sidecar  # noqa: E402

# 历史豁免：V5.0 P0 之前已收口产物（append-only 档案，不带新 provenance 头）。
# 新产物自 P0 起一律带 provenance 头并纳入检查。
EXEMPT_DIRS = {"seat-ab-r1a"}

# failcert 纯证书形态豁免（P3 首次暴露的 P0 合同缝）：failcert.v1 schema
# additionalProperties=false 不容 provenance 键，证书本体须保持可直接独立 verify
# 的纯形态；溯源改经同事务 selection.json 的 cert_sha256 对账（v5.selection
# 文档化偏离 3，DISPATCH-LOG 已登记）。
EXEMPT_SUFFIX = ".failcert.json"

# 席位实验 run 三件套自存证豁免（v5 延伸 seat-ab-r1a 同类豁免）：runs/ 目录下的
# output.json=席位回复逐字提取件（逐字合同完整性优先，加头即破坏证据本体）、
# meta.json=实验运行簿记（非派生工件）；response-raw.md 非 json 本就不检。
EXEMPT_DIR_SEGMENT = "runs"


def _exempt_rel(rel_parts):
    return EXEMPT_DIR_SEGMENT in rel_parts


def main(argv):
    root = argv[1] if len(argv) > 1 else sidecar.ALLOWED_ROOTS[0]
    if not os.path.isdir(root):
        print("no output tree at %s — nothing to check" % root)
        return 0
    problems = []
    json_files = 0
    cert_exempt = 0
    run_exempt = 0

    def check_json(path, dir_rel_parts, fn):
        """返回 'checked' | 'cert_exempt' | 'run_exempt'。"""
        if fn.endswith(EXEMPT_SUFFIX):
            return "cert_exempt"
        if _exempt_rel(dir_rel_parts):
            return "run_exempt"
        problems.extend(sidecar.check_file(path))
        return "checked"

    for entry in sorted(os.listdir(root)):
        full = os.path.join(root, entry)
        if entry in EXEMPT_DIRS:
            continue
        if os.path.isdir(full):
            for dirpath, _d, files in os.walk(full):
                rel_parts = os.path.relpath(dirpath, root).split(os.sep)
                for fn in sorted(files):
                    if not fn.endswith(".json"):
                        continue
                    verdict = check_json(os.path.join(dirpath, fn), rel_parts, fn)
                    if verdict == "checked":
                        json_files += 1
                    elif verdict == "cert_exempt":
                        cert_exempt += 1
                    else:
                        run_exempt += 1
        elif entry.endswith(".json"):
            verdict = check_json(full, [], entry)
            if verdict == "checked":
                json_files += 1
            elif verdict == "cert_exempt":
                cert_exempt += 1
            else:
                run_exempt += 1
    if problems:
        for p in problems:
            print("VIOLATION %s: %s" % (p["path"], p["issue"]))
        print("sidecar check: %d problem(s) / %d json files" % (len(problems), json_files))
        return 1
    print("sidecar check: GREEN (%d json files under %s, exempt=%s, cert_exempt=%d,"
          " run_exempt=%d)" % (json_files, root, ",".join(sorted(EXEMPT_DIRS)) or "-",
                               cert_exempt, run_exempt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
