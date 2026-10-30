# -*- coding: utf-8 -*-
"""V5-SMALLWAVE A3 钉值：executor 0.6.1 几何二级归因 log 行（log-only 非行为）。

合同（route-v5/V5-SMALLWAVE-TASKBOOK-2026-09-23.md §1.A3/§2 门 2）：
- 每条 exhaustion-cause 行后追加一行
  "net=<N> partition=<P> geom-secondary=<value>"，value ∈
  {fixed-copper-sealed（…）, open（…）}——失败网端点 r0/r1 出边密封普查、
  阻塞源仅计板固有固定铜（DIAG-FAILED8 方法移植）。
- log-only：不改任何路由决策/序/尝试阶梯——FAILED 板（本文件合成夹具族）
  的 verdict/per_net/attempts/既有 exhaustion-cause 串与 0.6.0 逐位一致
  （既有钉值测试 test_f4_* 族仍在位即为其证）；SAT/ROUTED 板零 geom-secondary
  行（无失败网 → negotiation_log 逐字节=0.6.0，门 2 字节等抽查的合成面）。
- 触发面披露（报告 §A3）：任务书 §1.A3 字面=「exhaustion-cause=ripup-
  exhausted 落 log 时」；门 2 要求 stm32 板（obstacle-dense 类）diff 恰=
  新 geom-secondary 行——两者兼容解=对**全部** exhaustion-cause 行触发
  （ripup-exhausted 为其子集），SAT 板字节等不受影响。
"""
import time

import pytest

import v5.executor as ex
from v5.executor import EXECUTOR_VERSION, execute_candidate

import test_upgrade5_engine_capability as E   # noqa: E402 既有合成板夹具族

_GEOM2_VALUES = ("fixed-copper-sealed（", "open（")


def _legacy_attempt_plans():
    return E._legacy_attempt_plans()


@pytest.fixture()
def legacy_world(monkeypatch):
    """改造前世界（106 阶梯无细档、无 rip-up）——复用既有夹具语义。"""
    monkeypatch.setattr(ex, "_attempt_plans", _legacy_attempt_plans)
    monkeypatch.setattr(ex, "_ripup_retry", lambda *a, **k: (None, None, 0))


def _geom2(log):
    return [l for l in log if " geom-secondary=" in l]


def _causes(log):
    return [l for l in log if " exhaustion-cause=" in l]


# ------------------------------------------------ 行格式与伴随位置（log-only 面）

@pytest.mark.parametrize("builder", [E._dense_first_board,
                                     E._ripup_fail_board,
                                     E._ripup_stillsealed_board])
def test_a3_geom_secondary_line_follows_every_exhaustion_cause(builder):
    """当前世界 FAILED 板：每条 exhaustion-cause 行的**下一位**=同 net/partition
    前缀的 geom-secondary 行（无插入、无缺失）；值域恰两支。"""
    board = E._board(builder)
    res = execute_candidate(board, E._cand(board))
    assert res["verdict"] == "FAILED"
    log = res["negotiation_log"]
    causes, g2 = _causes(log), _geom2(log)
    assert len(causes) >= 1 and len(g2) == len(causes)
    for c in g2:
        assert any(v in c for v in _GEOM2_VALUES)
    for i, c in enumerate(causes):
        head = c.split(" exhaustion-cause=", 1)[0]     # "net=N partition=P"
        j = next(k for k, l in enumerate(log) if l == c)
        assert log[j + 1] == "%s geom-secondary=%s" % (
            head, g2[i].split(" geom-secondary=", 1)[1])


@pytest.mark.parametrize("builder", [E._endpoint_seal_board,
                                     E._partial_seal_board,
                                     E._ripup_ok_board])
def test_a3_no_geom_secondary_lines_on_routed_boards(builder):
    """ROUTED 板无失败网 → 零 exhaustion-cause/geom-secondary 行
    （negotiation_log 与 0.6.0 逐字节一致——门 2 SAT 字节等的合成面）。"""
    board = E._board(builder)
    res = execute_candidate(board, E._cand(board))
    assert res["verdict"] == "ROUTED"
    assert _geom2(res["negotiation_log"]) == []
    assert _causes(res["negotiation_log"]) == []


def test_a3_exhaustion_cause_strings_unchanged_vs_060():
    """exhaustion-cause 串与 attempts 面（R2 翻转披露 0.6.1→0.7.0：rip-up
    轮 2→5 → attempts 318→636；geom-secondary 行为仍纯追加，过滤后日志=
    新钉值形态）。"""
    board = E._board(E._ripup_stillsealed_board)
    res = execute_candidate(board, E._cand(board))
    log = res["negotiation_log"]
    assert _causes(log) == ["net=NB partition=PT-B exhaustion-cause="
                            "ripup-exhausted（rip-up 5 轮仍耗尽，阻塞集=['NA']）"]
    assert any(l.startswith("net=NB partition=PT-B FAILED after 636 attempts: ")
               for l in log)
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["NB"]["status"] == "failed" and by_net["NB"]["attempts"] == 636


def test_a3_double_run_byte_equal():
    """确定性：双跑 negotiation_log 逐字节等（geom-secondary 行含在内）。"""
    board = E._board(E._ripup_fail_board)
    r1 = execute_candidate(board, E._cand(board))
    r2 = execute_candidate(board, E._cand(board))
    assert r1["negotiation_log"] == r2["negotiation_log"]


# ------------------------------------------------ 两支值各有一例（分支覆盖）

def test_a3_value_open_on_corridor_block(legacy_world, monkeypatch):
    """open 支：dense-first（dc-scm 签名）失败在直连走廊稠密焊盘墙、端点
    r0/r1 出边在仅计板固有固定铜口径下存在开放边 → 如实 open。

    V5-EXECUTOR-ENG-R1 翻新披露（2026-10-02）：本板 56 个端点行被 W-1 SC-1
    事前判定为真密封（首封=PT-P6/ep1，独立 distance_to 复核全部点位
    <R5−EPS；判定器关停后 PT-P6 首位 106 阶梯仍耗尽=伪证测试在案）——
    默认路径短路收口（GND 穷举面不再可达），open 支值钉改以判定器关停
    （_preflight_seal_shortcircuit no-op）跑原断言；默认路径短路行为另钉
    于 tests/test_executor_shortcircuit.py。"""
    board = E._board(E._dense_first_board)
    res = execute_candidate(board, E._cand(board))
    assert res["verdict"] == "FAILED"
    assert any("exhaustion-cause=sealed-short-circuit" in l
               for l in res["negotiation_log"])
    monkeypatch.setattr(ex, "_preflight_seal_shortcircuit",
                        lambda *a, **k: None)
    res = execute_candidate(board, E._cand(board))
    g2 = _geom2(res["negotiation_log"])
    assert len(g2) == 1 and " geom-secondary=open（" in g2[0]


def test_a3_value_fixed_copper_sealed_on_pad_box(legacy_world):
    """fixed-copper-sealed 支：endpoint-seal 板（atmega 签名）端点 a 被三面
    固定铜带盒封死（legacy 世界全阶梯耗尽 endpoint-sealed）→ 仅计板固有
    固定铜口径下 r0/r1 出边全封 → fixed-copper-sealed。"""
    board = E._board(E._endpoint_seal_board)
    res = execute_candidate(board, E._cand(board))
    assert res["verdict"] == "FAILED"
    g2 = _geom2(res["negotiation_log"])
    assert len(g2) == 1 and " geom-secondary=fixed-copper-sealed（" in g2[0]
    assert _causes(res["negotiation_log"]) == [
        "net=NA partition=PT-A exhaustion-cause="
        "endpoint-sealed（端点吸附节点出边全封，逃逸/细化类）"]


# ------------------------------------------------ 状态无残留 + 开销量级

def test_a3_geom_secondary_state_restoration_and_cost(legacy_world):
    """幂等+门 3 量级钉：以失败前态 ctx 直呼 _geom_secondary_attr——两次同值、
    state_key 前后逐位不变（快照/恢复无残留）；墙钟 <2s 量级（断言上限
    10s=量级护栏，实测记录见 SMALLWAVE-REPORT 门 3 段）。"""
    board = E._board(E._endpoint_seal_board)
    from v5.executor import _Context, _geom_secondary_attr
    ctx = _Context(board)
    holes_before = list(ctx.holes)
    edge_before = tuple(ctx.edge_inner)
    pid_a = "PT-A"
    part = next(p for p in board["partitions"]
                if p["partition_id"] == pid_a)
    a_pt = tuple(float(v) for v in part["geometry"]["endpoints"][0])
    b_pt = tuple(float(v) for v in part["geometry"]["endpoints"][1])
    width = float(part.get("planned_width", 0.2))
    key_before = ctx.state_key()
    t0 = time.time()
    v1 = _geom_secondary_attr(ctx, pid_a, "NA", width, a_pt, b_pt)
    w1 = time.time() - t0
    t0 = time.time()
    v2 = _geom_secondary_attr(ctx, pid_a, "NA", width, a_pt, b_pt)
    w2 = time.time() - t0
    assert v1 == v2 and "fixed-copper-sealed（" in v1
    assert ctx.state_key() == key_before
    assert list(ctx.holes) == holes_before and tuple(ctx.edge_inner) == edge_before
    assert w1 < 10.0 and w2 < 10.0, (w1, w2)


def test_a3_version_pin_disclosed():
    """版本钉翻转披露：0.6.0→0.6.1（geom-secondary log 行，log-only）。"""
    # V5-R2 翻转披露（2026-09-24）：executor 0.6.1→0.7.0（rip-up 有界深化
    # 2/8/20→5/12/30+W-2 联合重排+W-3 波次/档位导引+W-4 victim 定向探针）
    # V5-EXECUTOR-ENG-R1 翻转披露（2026-10-02）：executor 0.8.0→0.9.0
    # （W-1 SC-1 事前短路+W-2 verdict_provenance；geom-secondary 行在短路
    # 链中照发见 _preflight_seal_shortcircuit）
    assert EXECUTOR_VERSION == "v5.executor/0.13.0"  # 0.13.0 同步（engine-fix-r1 阶段一：FX-1 梯内 memo＋FX-2 微优化，纯等价提速；0.11.0=EXEC-R8-B）  # EXEC-R8-B 同步（候选出口事件接线）
