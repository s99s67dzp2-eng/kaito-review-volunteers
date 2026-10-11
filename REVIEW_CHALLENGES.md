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

## E — Verify a *real public* GitHub Actions run without granting private access

The public [synthetic-screening workflow](.github/workflows/synthetic-screening.yml) generates a `public-synthetic-ci-witness-practice` artifact containing `witness-practice.json` and `witness-practice.sha256` **only after its fabricated-data tests succeed**. Unlike the entirely invented run IDs in case D, this exercise offers a real GitHub-hosted run and downloadable artifact — but still **no independent Method Freeze approval**.

**Optional witness task (public metadata; GitHub may require sign-in to download the artifact, but never provide exchange secrets):**

1. Select a *completed successful* public [workflow run](https://github.com/s99s67dzp2-eng/kaito-review-volunteers/actions/workflows/synthetic-screening.yml) with this artifact. Record its exact **run ID, attempt number, event, Git commit SHA, job ID and conclusion** from GitHub's own Actions record. Do not rely on a screenshot or badge.
2. Check GitHub's public workflow job list and actual executed step names. Compare the checked-out Git SHA and source file hashes against the **downloaded** JSON manifest. For a pull-request run, explicitly distinguish the **temporary merge commit** used by the workflow from the PR source-head commit. Do not silently treat them as the same.
3. Verify the manifest's SHA-256 against `witness-practice.sha256`. If the GitHub REST artifact metadata reports a digest, distinguish the **archive digest** from the **inner JSON file digest**; one is not proof of the other without opening the actual bytes.
4. Provide one concrete falsifying negative control: a stale run SHA, wrong run attempt, changed source bytes, mismatched archive digest, missing expected job step, or a reviewer/witness operating under the same controller. Explain how it would force **HOLD**.
5. State why a job-created manifest is **self-reported**, and why the exercise cannot certify real strategy returns, independent people, authentic exchange balances, private production source or deployment approval.

**Public evidence only.** No private repository invitations, personal data, API keys or wallet information. A good answer makes you a *potential* witness volunteer; it never grants access or signs any production attestation.

## Submitting an answer

Reply to the [volunteer intake issue](https://github.com/s99s67dzp2-eng/kaito-review-volunteers/issues/1) with a **brief explanation** of one case, role of interest and relevant public technical examples if available. Do not submit secrets, account balances, private datasets, identity documents or credentials. A suggested diagnosis is not an audit attestation, release authorization or certification.
