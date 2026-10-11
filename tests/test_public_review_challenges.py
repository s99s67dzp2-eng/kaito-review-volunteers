"""Standalone, synthetic-only tests for public independent reviewer screening.

No private trading source, live credentials, real trading data, outside
dependencies, real CI attestations or real-money permissions.
Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import math
import unittest


def max_equity_drawdown(returns: list[float]) -> float:
    """Simple equity path example; ignores real-world margin and liquidity."""
    equity = peak = 1.0
    largest = 0.0
    for r in returns:
        if not math.isfinite(r) or r <= -1.0:
            raise ValueError("not a bounded synthetic fractional return")
        equity *= 1.0 + r
        peak = max(peak, equity)
        largest = max(largest, 1.0 - equity / peak)
    return largest


def reconcile_path(trades: list[tuple[float, float, float, float]]) -> list[int]:
    """Each tuple: before equity, after equity, pnl, intermediate cashflow.

    The cashflow is applied between preceding after-equity and current before.
    Input values here are fabricated, not audited exchange settlements.
    """
    bad: list[int] = []
    previous_close: float | None = None
    for i, (before, after, pnl, cashflow) in enumerate(trades):
        values = (before, after, pnl, cashflow)
        if not all(math.isfinite(v) for v in values):
            bad.append(i)
            continue
        if not math.isclose(after, before + pnl, rel_tol=0, abs_tol=1e-9):
            bad.append(i)
        if previous_close is not None and not math.isclose(
            before, previous_close + cashflow, rel_tol=0, abs_tol=1e-9
        ):
            bad.append(i)
        previous_close = after
    return sorted(set(bad))


def decompose_synthetic_friction(
    trades: list[dict[str, float]]
) -> dict[str, float]:
    price = math.fsum(t["pre_cost_price_pnl"] for t in trades)
    fee = math.fsum(t["fee"] for t in trades)
    slippage = math.fsum(t["slippage"] for t in trades)
    received = math.fsum(max(t["funding"], 0.0) for t in trades)
    paid = math.fsum(max(-t["funding"], 0.0) for t in trades)
    if min(fee, slippage, paid) < 0:
        raise ValueError("invalid synthetic cost ledger")
    gross = math.fsum((price, received))
    costs = math.fsum((fee, slippage, paid))
    return {
        "funding_received": received,
        "funding_paid": paid,
        "fees": fee,
        "slippage": slippage,
        "gross": gross,
        "costs": costs,
        "net": gross - costs,
    }


def sample_ci_review_is_independent(evidence: dict) -> bool:
    """Demonstration only; never certifies authentic GitHub identities/runs."""
    sha = evidence.get("reviewed_sha")
    runs = evidence.get("runs", [])
    controllers = evidence.get("reviewer_controllers", [])
    return bool(
        isinstance(sha, str)
        and len(sha) == 40
        and all(c in "0123456789abcdef" for c in sha)
        and isinstance(runs, list)
        and len(runs) >= 2
        and len({r.get("run_id") for r in runs}) >= 2
        and all(
            r.get("head_sha") == sha
            and isinstance(r.get("run_id"), int)
            and r.get("run_id") > 0
            and isinstance(r.get("attempt"), int)
            and r.get("attempt") > 0
            and isinstance(r.get("artifact_digest"), str)
            and len(r.get("artifact_digest")) == 64
            for r in runs
        )
        and len(controllers) == 3
        and len(set(controllers)) == 3
        and all(isinstance(c, str) and c for c in controllers)
    )


class SyntheticScreeningCases(unittest.TestCase):
    def test_case_a_iid_histogram_does_not_determine_path_risk(self):
        clustered = [-0.25] * 4 + [0.15] * 36
        dispersed = ([0.15] * 9 + [-0.25]) * 4
        self.assertEqual(sorted(clustered), sorted(dispersed))
        self.assertAlmostEqual(
            math.fsum(clustered) / len(clustered),
            math.fsum(dispersed) / len(dispersed),
        )
        # A Monte Carlo IID bootstrap that discards chronology sees identical
        # return multisets; the actual hypothetical chronological paths differ.
        self.assertGreater(max_equity_drawdown(clustered), 0.65)
        self.assertLess(max_equity_drawdown(dispersed), 0.30)
        self.assertGreater(
            max_equity_drawdown(clustered),
            max_equity_drawdown(dispersed),
        )

    def test_case_a_invalid_trade_return_must_fail(self):
        for invalid in (float("nan"), float("inf"), -1.0):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    max_equity_drawdown([0.15, invalid])

    def test_case_b_fake_constant_equity_is_not_reconciled(self):
        trades = [(1000, 1001, 1, 0)] * 3
        self.assertEqual(reconcile_path(trades), [1, 2])

    def test_case_b_genuine_declared_cashflows_reconcile_arithmetically(self):
        # Synthetic arithmetic can reconcile *claimed* cashflows, not prove
        # authentic deposits/withdrawals or outside custodian statements.
        trades = [
            (1000, 1001, 1, 0),
            (1000, 1001, 1, -1),
            (1000, 1001, 1, -1),
        ]
        self.assertEqual(reconcile_path(trades), [])

    def test_case_b_forged_trade_profit_fails(self):
        self.assertEqual(reconcile_path([(1000, 1001, 0, 0)]), [0])

    def test_case_c_funding_receipts_do_not_hide_funding_payments(self):
        trades = [
            {"pre_cost_price_pnl": 1.30, "fee": 0.10,
             "slippage": 0.10, "funding": 0.40},
            {"pre_cost_price_pnl": 1.30, "fee": 0.10,
             "slippage": 0.10, "funding": -0.30},
        ]
        parts = decompose_synthetic_friction(trades)
        for key, expected in {
            "funding_received": 0.40, "funding_paid": 0.30,
            "fees": 0.20, "slippage": 0.20, "gross": 3.00,
            "costs": 0.70, "net": 2.30,
        }.items():
            self.assertAlmostEqual(parts[key], expected)

    def test_case_d_stale_ci_and_same_controller_cannot_pass(self):
        reviewed = "a" * 40
        bad = {
            "reviewed_sha": reviewed,
            "runs": [
                {"head_sha": "b" * 40, "run_id": 123, "attempt": 1,
                 "artifact_digest": "c" * 64},
                {"head_sha": reviewed, "run_id": 124, "attempt": 1,
                 "artifact_digest": "d" * 64},
            ],
            "reviewer_controllers": ["same-author", "same-author", "external"],
        }
        self.assertFalse(sample_ci_review_is_independent(bad))

    def test_case_d_even_consistent_mock_is_not_real_attestation(self):
        example_only = {
            "reviewed_sha": "a" * 40,
            "runs": [
                {"head_sha": "a" * 40, "run_id": 123, "attempt": 1,
                 "artifact_digest": "c" * 64},
                {"head_sha": "a" * 40, "run_id": 124, "attempt": 1,
                 "artifact_digest": "d" * 64},
            ],
            "reviewer_controllers": ["operator-one", "operator-two", "operator-three"],
        }
        self.assertTrue(sample_ci_review_is_independent(example_only))
        # NOTE: these strings are entirely fabricated and DO NOT prove that
        # three people, two real CI runs, or artifacts truly exist.

if __name__ == "__main__":
    unittest.main()
