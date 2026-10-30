# -*- coding: utf-8 -*-
"""envelope 保守包络：外扩、伪影判别。"""
import pytest

from v5.metrics import envelope as env


def test_expand_rect_symmetric():
    assert env.expand_rect((10, 10, 20, 20), 0.6) == (9.4, 9.4, 20.6, 20.6)


def test_default_margin_is_v2_value():
    assert env.DEFAULT_MARGIN == 0.6


def test_segment_envelope_grows_both():
    e = env.segment_envelope((0, 0), (10, 0), half_width=0.1)
    assert e == (-0.7, -0.7, 10.7, 0.7)


def test_segment_envelope_direction_agnostic():
    e = env.segment_envelope((10, 40), (10, 0), half_width=0.1, margin=0.2)
    assert e == pytest.approx((9.7, -0.3, 10.3, 40.3))


def test_pad_envelope():
    assert env.pad_envelope((5, 5), 0.15, margin=0.6) == (4.25, 4.25, 5.75, 5.75)


def test_envelopes_overlap_true():
    assert env.envelopes_overlap((0, 0, 2, 2), (1, 1, 3, 3)) is True


def test_envelopes_overlap_false():
    assert env.envelopes_overlap((0, 0, 2, 2), (2.7, 0, 4, 1)) is False


def test_overlap_depth():
    assert env.envelope_overlap_depth((0, 0, 2, 2), (1, 1, 3, 3)) == 1.0


def test_overlap_depth_negative_gap():
    assert env.envelope_overlap_depth((0, 0, 2, 2), (3, 0, 5, 1)) == -1.0


def test_artifact_detected():
    """对抗：包络外扩伪影——包络响警（重叠 0.4）但实际间距 1.0 ≥ R5 限 0.5。"""
    ea = env.segment_envelope((0, 0), (10, 0), half_width=0.1)      # y∈[-0.7,0.7]
    eb = env.segment_envelope((0, 1.0), (10, 1.0), half_width=0.1)  # y∈[0.3,1.7]
    assert env.envelopes_overlap(ea, eb)
    is_art, gap = env.artifact_check(ea, eb, actual_gap=1.0)
    assert is_art and gap == pytest.approx(1.0)


def test_artifact_not_triggered_real_conflict():
    """实际间距 0.3 < 0.5：包络响警对应真冲突，非伪影。"""
    ea = env.segment_envelope((0, 0), (10, 0), half_width=0.1)
    eb = env.segment_envelope((0, 0.3), (10, 0.3), half_width=0.1)
    assert env.envelopes_overlap(ea, eb)
    is_art, _ = env.artifact_check(ea, eb, actual_gap=0.3)
    assert not is_art
