"""cmp_stats 单测：确定性 PRNG、percentile、bootstrap 双跑一致、符号检验。"""

import unittest

from pcbflow.v4exp import cmp_stats


class TestSha1Prng(unittest.TestCase):
    def test_deterministic(self):
        _f1, i1 = cmp_stats.sha1_prng("seed-a")
        _f2, i2 = cmp_stats.sha1_prng("seed-a")
        self.assertEqual([i1(100) for _ in range(50)],
                         [i2(100) for _ in range(50)])

    def test_different_seed_different_stream(self):
        _f1, i1 = cmp_stats.sha1_prng("seed-a")
        _f2, i2 = cmp_stats.sha1_prng("seed-b")
        self.assertNotEqual([i1(1 << 30) for _ in range(10)],
                            [i2(1 << 30) for _ in range(10)])

    def test_in_range(self):
        _f, nxt = cmp_stats.sha1_prng("s")
        for _ in range(500):
            v = nxt(7)
            self.assertGreaterEqual(v, 0)
            self.assertLess(v, 7)


class TestPercentile(unittest.TestCase):
    def test_linear_interp(self):
        self.assertAlmostEqual(cmp_stats.percentile([1, 2, 3], 0), 1.0)
        self.assertAlmostEqual(cmp_stats.percentile([1, 2, 3], 50), 2.0)
        self.assertAlmostEqual(cmp_stats.percentile([1, 2, 3], 100), 3.0)
        self.assertAlmostEqual(cmp_stats.percentile([1, 2, 3], 25), 1.5)

    def test_single(self):
        self.assertEqual(cmp_stats.percentile([42], 90), 42.0)


class TestBootstrap(unittest.TestCase):
    def test_double_run_identical(self):
        d = [0.5, -1.25, 2.0, 0.0, 3.75, -0.5]
        r1 = cmp_stats.paired_bootstrap_ci_mean_delta(d, "v4cmp-boot-seed-v1")
        r2 = cmp_stats.paired_bootstrap_ci_mean_delta(d, "v4cmp-boot-seed-v1")
        self.assertEqual(r1, r2)
        self.assertAlmostEqual(r1["observed_mean_delta"], 0.75, 6)
        self.assertLessEqual(r1["ci95_lo"], r1["ci95_hi"])

    def test_zero_deltas(self):
        r = cmp_stats.paired_bootstrap_ci_mean_delta(
            [0.0, 0.0, 0.0], "s")
        self.assertEqual(r["observed_mean_delta"], 0.0)
        self.assertEqual(r["ci95_lo"], 0.0)
        self.assertEqual(r["ci95_hi"], 0.0)


class TestSignTest(unittest.TestCase):
    def test_extremes(self):
        self.assertAlmostEqual(cmp_stats.sign_test_two_sided(5, 0),
                               2.0 / 32.0, 6)
        self.assertAlmostEqual(cmp_stats.sign_test_two_sided(3, 2), 1.0, 6)
        self.assertEqual(cmp_stats.sign_test_two_sided(0, 0), 1.0)


if __name__ == "__main__":
    unittest.main()
