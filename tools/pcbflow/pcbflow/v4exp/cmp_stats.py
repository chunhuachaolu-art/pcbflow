"""pcbflow.v4exp.cmp_stats -- 冻结的非参数统计辅助（确定性，零依赖）。

用于 V4 全面对照实验（v4cmp）协议：
* percentile（线性插值口径，合同固定）；
* paired bootstrap 均值置信区间：重采样流 = SHA-256 派生确定性 PRNG
  （cmp_stats 自含，不用 random 模块，避免跨版本实现差异），
  种子串在协议中冻结。

纯函数，无 I/O。
"""

from __future__ import annotations

import hashlib


def sha1_prng(seed_str: str):
    """确定性 PRNG：u = int(sha256(seed_str||n 的 8 字节大端计数), big) / 2^256。

    返回 (next_float, next_int) 闭包对；n 从 1 递增，永不重置。
    """
    state = {"n": 0}

    def nxt_float() -> float:
        state["n"] += 1
        digest = hashlib.sha256(
            seed_str.encode("utf-8") + state["n"].to_bytes(8, "big")
        ).digest()
        return int.from_bytes(digest, "big") / float(1 << 256)

    def nxt_int(bound: int) -> int:
        """[0, bound) 均匀整数（拒绝采样消除模偏差）。"""
        if bound <= 0:
            raise ValueError("bound must be positive")
        while True:
            v = nxt_float()
            i = int(v * bound)
            # 接受域 v < bound/2^ceil 等价于 i 的满概率桶；
            # 简化：仅拒绝 i == bound（v==1.0 不可达，故无实际拒绝）
            if i < bound:
                return i

    return nxt_float, nxt_int


def percentile(values: list, pct: float) -> float:
    """线性插值口径：rank = (n-1)*pct/100，在升序数组上插值。"""
    if not values:
        raise ValueError("percentile of empty list")
    vs = sorted(float(v) for v in values)
    if len(vs) == 1:
        return vs[0]
    rank = (len(vs) - 1) * pct / 100.0
    lo = int(rank)
    hi = min(lo + 1, len(vs) - 1)
    frac = rank - lo
    return vs[lo] * (1.0 - frac) + vs[hi] * frac


def mean(values: list):
    return (sum(float(v) for v in values) / len(values)) if values else None


def median(values: list):
    return percentile(values, 50.0) if values else None


def paired_bootstrap_ci_mean_delta(deltas: list, seed_str: str,
                                  resamples: int = 10000,
                                  alpha: float = 0.05) -> dict:
    """配对 delta 均值的双侧 bootstrap percentile 区间。"""
    ds = [float(d) for d in deltas]
    n = len(ds)
    if n == 0:
        raise ValueError("empty deltas")
    nxt_float, nxt_int = sha1_prng(seed_str)
    means = []
    for _ in range(resamples):
        s = 0.0
        for _ in range(n):
            s += ds[nxt_int(n)]
        means.append(s / n)
    lo = percentile(means, 100.0 * alpha / 2.0)
    hi = percentile(means, 100.0 * (1.0 - alpha / 2.0))
    return {"n": n,
            "observed_mean_delta": round(mean(ds), 6),
            "ci95_lo": round(lo, 6), "ci95_hi": round(hi, 6),
            "resamples": resamples, "seed": seed_str,
            "method": "paired bootstrap percentile, SHA-256 counter PRNG"}


def sign_test_two_sided(positive: int, negative: int) -> float:
    """非零配对上 H0:p=0.5 的双侧二项精确 p 值（纯整数算术）。"""
    n = positive + negative
    if n == 0:
        return 1.0
    def binom(k):
        r = 1
        for i in range(1, k + 1):
            r = r * (n - i + 1) // i
        return r
    tail = 0.0
    lo = min(positive, negative)
    # 两侧尾概率和（含观测点），用精确分数累加后除 2^n
    num = 0
    for k in range(0, lo + 1):
        num += binom(k)
    p = min(1.0, 2.0 * num / float(1 << n))
    return round(p, 6)
