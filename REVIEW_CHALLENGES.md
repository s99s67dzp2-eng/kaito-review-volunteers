# Independent review — synthetic screening challenges

These are **made-up examples for volunteer screening only**. They contain no real trades, user data, API keys, proprietary source code or financial statements. Passing them **does not** mean the strategy is profitable, the system is safe, or any formal release gate has passed.

## A — Loss clustering and path-dependent risk

Two hypothetical strategies each report 40 trade returns: **36 at +15% and 4 at −25%**. In strategy A, all four losses arrive consecutively; in strategy B they are separated. Their histograms are identical.

**Question:** Why might an IID/bootstrap risk-of-ruin estimate miss relevant danger? What sequential margin, drawdown, leverage, volatility or market-regime evidence would you require? State at least one test that could falsify a safety claim.

## B — Inconsistent capital path

Three hypothetical trades each report **+1 USDT**. Their claimed before/after balances are **1000→1001, 1000→1001, 1000→1001**, with no intervening deposit or withdrawal record.

**Question:** Is this a reconciled sequential portfolio equity path? What additional independently sourced capital-flow evidence is required?

## C — Net funding hiding gross costs

Two trades each declare 1.30 USDT pre-cost price P&L, fee 0.10, slippage 0.10 and no other costs. First receives **+0.40** in funding; second pays **−0.30**.

**Question:** Separate **gross P&L including funding receipts**, **fees**, **slippage**, **funding payments** and **net P&L**. Why is arithmetic agreement still insufficient to prove real after-friction performance?

For a checkable arithmetic control, the decomposition here is: 3.00 gross including positive funding receipt, 0.20 fee, 0.20 slippage, 0.30 funding paid, 0.70 total outflow and **2.30 USDT net**. These are synthetic quantities, not trading results.

## D — Green CI is not independent method approval

An applicant provides a green CI badge for **a different commit** from the method under review. Two reviewer receipts are issued using identities controlled by the same operator; CI run IDs and artifact digests cannot be checked.

**Question:** Why should the release remain on HOLD? What would distinguish independent review of an exact immutable source revision from a repeated self-signed claim?

## Submitting an answer

Reply to the [volunteer intake issue](../../issues) with a **brief explanation** of one case, role of interest and relevant public technical examples if available. Do not submit secrets, account balances, private datasets, identity documents or credentials. A suggested diagnosis is not an audit attestation, release authorization or certification.
