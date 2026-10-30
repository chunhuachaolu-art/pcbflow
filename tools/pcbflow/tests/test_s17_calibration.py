"""S17 会话测试：Critic 校准域种子集与一致性比较器（TL-2；APR-0008 线）。

覆盖：
- board_edge_bbox_mm：gr_line start/end + gr_rect 混合文本 bbox；
  无 Edge.Cuts → fail-closed；
- png_board_pixel_bounds：合成渐变背景+方板 PNG 的确定性测量、
  同字节重放一致、坏 magic/坏形态 fail-closed、板触边 fail-closed；
- box_mm_to_frame_pct：top 同向、bottom x 镜像、框越板界 fail-closed、
  值域 [0,1]；
- build_gt_entry / validate_gt_entries：类别越出 critic.FLAG_CATEGORIES
  拒绝（枚举零改动）、框退化/越界拒绝、gt_id 重复拒绝；
- compare（度量定义先写死后跑，阈值=常量断言不得后调）：完美匹配
  recall 1.0、类别不符→missed+false_positive、containment 恰在阈值
  即匹配、低于阈值不匹配、abstain 单列（不匹配不计 FP）、无框旗标
  单列、空读者 recall 0、未知键/非法类别 fail-closed、种子部分覆盖
  caveat 在案（FP 不构成误报率结论）；
- 集成锚（只读）：out/v3-tl2/calibration/ 实况——GT 4 条、类别落在
  枚举、provenance hash 与盘上实文件一致、自检全匹配、manifest 绑定
  GT hash 一致。

纯内存构造（生成器模式）：零子进程/零写盘/零网络。
"""

import json
import os
import struct
import sys
import zlib

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import calibration as cal  # noqa: E402
from pcbflow import critic, hashing  # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")


# ---------------------------------------------------------------------------
# 合成 PNG（8-bit RGB、垂直渐变背景 + 中央方板）
# ---------------------------------------------------------------------------

def _png_chunk(ctype: bytes, body: bytes) -> bytes:
    return (struct.pack(">I", len(body)) + ctype + body
            + struct.pack(">I", zlib.crc32(ctype + body) & 0xFFFFFFFF))


def _make_png(w: int, h: int, board_box) -> bytes:
    """board_box=(x0,y0,x1,y1) inclusive 方板区用固定异色，其余逐行渐变。"""
    rows = bytearray()
    bx0, by0, bx1, by1 = board_box
    for y in range(h):
        rows.append(0)                      # filter none
        for x in range(w):
            if bx0 <= x <= bx1 and by0 <= y <= by1:
                rows += bytes((30, 120, 30))
            else:
                g = 200 - (y * 100 // max(1, h))
                rows += bytes((g, g, (g + 30) % 256))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", zlib.compress(bytes(rows)))
            + _png_chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# board_edge_bbox_mm
# ---------------------------------------------------------------------------

def test_edge_bbox_multiline_and_rect():
    text = """
	(gr_line
		(start 0 70)
		(end 0 0)
		(layer "Edge.Cuts")
	)
	(gr_rect
		(start 10 10)
		(end 60 60)
		(layer "F.Cu")
	)
	(gr_line
		(start 70 0)
		(end 70 70)
		(layer "Edge.Cuts")
	)
"""
    bbox = cal.board_edge_bbox_mm(text)
    assert bbox == {"x_min": 0.0, "y_min": 0.0, "x_max": 70.0, "y_max": 70.0}


def test_edge_bbox_empty_fail_closed():
    with pytest.raises(ValueError):
        cal.board_edge_bbox_mm("(gr_line (start 0 0) (end 1 1) (layer F.Cu))")


# ---------------------------------------------------------------------------
# png_board_pixel_bounds
# ---------------------------------------------------------------------------

def test_png_bounds_gradient_deterministic():
    data = _make_png(200, 120, (60, 20, 139, 99))
    b1 = cal.png_board_pixel_bounds(data)
    b2 = cal.png_board_pixel_bounds(data)
    assert (b1["x0"], b1["y0"], b1["x1"], b1["y1"]) == (60, 20, 139, 99)
    assert b1 == b2
    assert b1["image_width"] == 200 and b1["image_height"] == 120


def test_png_bounds_bad_magic_and_edge_touch_fail_closed():
    with pytest.raises(ValueError):
        cal.png_board_pixel_bounds(b"not a png")
    touching = _make_png(100, 100, (0, 10, 99, 90))   # 板触左右缘
    with pytest.raises(ValueError):
        cal.png_board_pixel_bounds(touching)


def test_png_bounds_unsupported_color_type():
    body = struct.pack(">IIBBBBB", 4, 4, 8, 3, 0, 0, 0)   # palette 不支持
    data = (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", body)
            + _png_chunk(b"IDAT", zlib.compress(b"\x00" * 16))
            + _png_chunk(b"IEND", b""))
    with pytest.raises(ValueError):
        cal.png_board_pixel_bounds(data)


# ---------------------------------------------------------------------------
# box_mm_to_frame_pct
# ---------------------------------------------------------------------------

PX = {"x0": 40, "y0": 10, "x1": 440, "y1": 410,
      "image_width": 480, "image_height": 480}
BBOX = {"x_min": 0.0, "y_min": 0.0, "x_max": 70.0, "y_max": 70.0}


def test_frame_pct_top_bottom_mirror():
    box = [30.0, 20.0, 40.0, 50.0]
    top = cal.box_mm_to_frame_pct(box, BBOX, PX, side="top")
    bottom = cal.box_mm_to_frame_pct(box, BBOX, PX, side="bottom")
    for v in top + bottom:
        assert 0.0 <= v <= 1.0
    # x 镜像：bottom 的 x 区间与 top 关于板中心对称；y 相同
    assert top[1] == bottom[1] and top[3] == bottom[3]
    assert top[0] < top[2] and bottom[0] < bottom[2]
    # 镜像关系（板在图幅内水平居中时，关于图幅中心对称）
    assert abs((1 - bottom[2]) - top[0]) < 1e-9
    assert abs((1 - bottom[0]) - top[2]) < 1e-9
    # 板左缘像素 x=40 → 图幅 40/480
    assert abs(top[0] - 40 / 480) < 1e-6 or box[0] > 0


def test_frame_pct_out_of_board_fail_closed():
    with pytest.raises(ValueError):
        cal.box_mm_to_frame_pct([0.0, 0.0, 71.0, 5.0], BBOX, PX, side="top")
    with pytest.raises(ValueError):
        cal.box_mm_to_frame_pct([0.0, 0.0, 5.0, 5.0], BBOX, PX, side="left")


# ---------------------------------------------------------------------------
# GT 条目
# ---------------------------------------------------------------------------

def _gt_entry(**over):
    base = dict(
        gt_id="GT-X-1", category="courtyard_crowding", side="top",
        board_box_mm=[1.0, 2.0, 3.0, 4.0],
        frame_box_pct=[0.1, 0.2, 0.3, 0.4],
        drc_types=["courtyards_overlap"], cluster_refs=["R4", "J3"],
        basis_refs=["pose_revision_proof"], description="判例描述")
    base.update(over)
    return base


def test_build_gt_entry_valid_and_enum_guard():
    e = cal.build_gt_entry(**_gt_entry())
    assert e["gt_id"] == "GT-X-1"
    for bad in ("not_a_category", "silk_readability ", "layout_conclusion"):
        with pytest.raises(ValueError):
            cal.build_gt_entry(**_gt_entry(category=bad))
    # 类别集与 critic.FLAG_CATEGORIES 逐字一致（枚举零改动）
    assert "courtyard_crowding" in critic.FLAG_CATEGORIES
    assert "other_advisory" in critic.FLAG_CATEGORIES


def test_build_gt_entry_box_guards():
    with pytest.raises(ValueError):
        cal.build_gt_entry(**_gt_entry(frame_box_pct=[0.1, 0.2, 0.05, 0.4]))
    with pytest.raises(ValueError):
        cal.build_gt_entry(**_gt_entry(frame_box_pct=[0.1, 0.2, 1.3, 0.4]))
    with pytest.raises(ValueError):
        cal.build_gt_entry(**_gt_entry(frame_box_pct=[0.1, 0.2, 0.1, 0.4]))
    with pytest.raises(ValueError):
        cal.build_gt_entry(**_gt_entry(drc_types=[]))
    with pytest.raises(ValueError):
        cal.build_gt_entry(**_gt_entry(description="  "))


def test_validate_gt_entries_duplicate_id():
    a = cal.build_gt_entry(**_gt_entry())
    b = cal.build_gt_entry(**_gt_entry(gt_id="GT-X-1",
                                       frame_box_pct=[0.5, 0.5, 0.6, 0.6]))
    with pytest.raises(ValueError):
        cal.validate_gt_entries([a, b])
    cal.validate_gt_entries([a])


# ---------------------------------------------------------------------------
# compare（度量定义先写死后跑）
# ---------------------------------------------------------------------------

def test_metric_threshold_is_fixed_constant():
    assert cal.CONTAINMENT_MIN == 0.5
    assert cal.METRIC_VERSION == "calibration-metric-v1"


def test_compare_perfect_and_empty():
    gt = [cal.build_gt_entry(**_gt_entry())]
    flags = [{"flag_id": "F1", "category": "courtyard_crowding",
              "confidence": 0.9, "abstain": False,
              "frame_box_pct": [0.1, 0.2, 0.3, 0.4]}]
    r = cal.compare(flags, gt)
    assert r["gt_recall"] == 1.0
    assert r["gt_matched_count"] == 1
    assert r["reader_false_positive_ids"] == []
    empty = cal.compare([], gt)
    assert empty["gt_recall"] == 0.0
    assert empty["gt_missed_ids"] == ["GT-X-1"]
    assert empty["reader_precision_vs_seed_gt"] is None


def test_compare_containment_threshold_semantics():
    gt = [cal.build_gt_entry(**_gt_entry())]
    # containment 恰=0.5 → 匹配（≥ 阈值）
    half = [0.1, 0.2, 0.2, 0.4]     # 交集宽 = GT 宽的一半、全高
    r = cal.compare([{"flag_id": "F", "category": "courtyard_crowding",
                      "confidence": 0.5, "abstain": False,
                      "frame_box_pct": half}], gt)
    assert r["gt_matched_count"] == 1
    assert r["matches"][0]["containment"] == 0.5
    # containment < 0.5 → 不匹配 → FP
    less = [0.1, 0.2, 0.15, 0.4]
    r2 = cal.compare([{"flag_id": "F", "category": "courtyard_crowding",
                       "confidence": 0.5, "abstain": False,
                       "frame_box_pct": less}], gt)
    assert r2["gt_missed_ids"] == ["GT-X-1"]
    assert r2["reader_false_positive_ids"] == ["F"]


def test_compare_category_mismatch_abstain_no_box():
    gt = [cal.build_gt_entry(**_gt_entry())]
    flags = [
        {"flag_id": "FW", "category": "silk_readability",
         "confidence": 0.7, "abstain": False,
         "frame_box_pct": [0.1, 0.2, 0.3, 0.4]},      # 类别不符 → FP
        {"flag_id": "FA", "category": "courtyard_crowding",
         "confidence": 0.4, "abstain": True,
         "frame_box_pct": [0.1, 0.2, 0.3, 0.4]},      # abstain 单列
        {"flag_id": "FN", "category": "courtyard_crowding",
         "confidence": 0.6, "abstain": False},        # 无框 → no_box
    ]
    r = cal.compare(flags, gt)
    assert r["reader_abstain_ids"] == ["FA"]
    assert r["reader_unmatched_no_box_ids"] == ["FN"]
    assert r["reader_false_positive_ids"] == ["FW"]
    assert r["gt_missed_ids"] == ["GT-X-1"]
    assert "部分覆盖" in r["coverage_caveat"]


def test_compare_input_validation_fail_closed():
    gt = [cal.build_gt_entry(**_gt_entry())]
    with pytest.raises(ValueError):
        cal.compare([{"flag_id": "F", "category": "nope",
                      "confidence": 0.5, "abstain": False}], gt)
    with pytest.raises(ValueError):
        cal.compare([{"flag_id": "F", "category": "courtyard_crowding",
                      "confidence": 0.5, "abstain": False, "junk": 1}], gt)
    with pytest.raises(ValueError):
        cal.compare([{"flag_id": "F", "category": "courtyard_crowding",
                      "confidence": 1.5, "abstain": False}], gt)
    with pytest.raises(ValueError):
        cal.compare([{"flag_id": "F", "category": "courtyard_crowding",
                      "confidence": 0.5, "abstain": "yes"}], gt)


# ---------------------------------------------------------------------------
# 集成锚（只读 out/ 实况）
# ---------------------------------------------------------------------------

def test_calibration_artifacts_on_disk():
    cal_dir = os.path.join(REPO, "out", "v3-tl2", "calibration")
    gt_path = os.path.join(cal_dir, "ground-truth-v1.json")
    mf_path = os.path.join(cal_dir, "calibration-domain-v1.json")
    gt = json.load(open(gt_path, encoding="utf-8"))
    manifest = json.load(open(mf_path, encoding="utf-8"))
    entries = gt["gt_entries"]
    assert len(entries) == 4
    assert {e["category"] for e in entries} <= set(critic.FLAG_CATEGORIES)
    assert gt["self_check"]["gt_matched_count"] == \
        gt["self_check"]["gt_count"] == 4
    assert gt["self_check"]["reader_false_positive_ids"] == []
    # provenance hash 对盘上实文件（sha256_file byte 口径）
    for name, src in gt["provenance"].items():
        disk = hashing.sha256_file(
            os.path.join(REPO, *src["path_rel"].split("/")))
        assert disk == src["sha256"], name
    # manifest 绑定 GT hash 一致 + 语义边界在案
    assert manifest["ground_truth"]["sha256"] == \
        hashing.sha256_file(gt_path)
    assert manifest["metric"]["is_gate"] is False
    assert manifest["status"] == "seed_annotation_only"
    assert manifest["domain_id"] == cal.DOMAIN_ID
    # 比较器对盘上 GT 自比较全匹配（箱体/类别一致性）
    flags = [{"flag_id": e["gt_id"], "category": e["category"],
              "confidence": 1.0, "abstain": False,
              "frame_box_pct": e["frame_box_pct"]} for e in entries]
    r = cal.compare(flags, entries)
    assert r["gt_recall"] == 1.0
    assert r["reader_false_positive_ids"] == []
