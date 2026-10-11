# KAITO — Volunteer Independent Review / 免費獨立技術審查志工招募

**Status / 狀態：OPEN for unpaid expressions of interest — no reviewers appointed, no formal audit completed.**  
**範圍：公開招募與合成測試；不是交易程式碼庫，不提供帳戶或金鑰。**

## 中文招募說明

我們正在開發一套**私人研究中的加密資產量化分析系統**，目前**沒有經正式驗證的正期望策略，也沒有授權任何實單交易**。為避免開發者自行審查、低估回測偏差或資金風險，正在尋找：

1. **獨立技術審查者 × 2**：熟悉 Python、統計、回測／時間序列、過度擬合、資料洩漏、負控制、連續虧損、倉位與資金流水、費用／滑價／資金費率風險。
2. **獨立 GitHub CI 證據見證者 × 1**：能核對實際 GitHub Actions 工作流程、精確 commit、run/attempt、工作日誌及工件雜湊，辨識冒充、舊版本及不完整證據。

**完全自願、無報酬。** 第一階段只希望進行 **20–30 分鐘的範圍討論**，也可用 GitHub 留言非同步進行；正式審查內容與時間由雙方另外確認。**歡迎指出缺陷並拒絕 PASS。** 不承諾收益、工作、報酬或任何交易機會。

<https://github.com/s99s67dzp2-eng/kaito-review-volunteers/issues/1> — **直接在這個招募 Issue 留言申請**

想先了解測試題目，請看 [四個合成資料審查案例](REVIEW_CHALLENGES.md)；參與界線請看 [安全與權限說明](SECURITY_AND_SCOPE.md)。

可選：獨立執行 [公開、純合成 Python 測試](tests/test_public_review_challenges.py)，不需任何帳號、金鑰、安裝套件或交易資料。在本機執行 `python3 -m unittest discover -s tests -v`；[公開 GitHub Actions 測試紀錄](actions/workflows/synthetic-screening.yml) 可查看執行結果。**即使測試全部通過，也只代表合成篩選測試可重現，不代表真實策略獲利或任何正式 Gate 通過。**

**CI 見證志工：** 現在也可做 [案例 E：核對真實 GitHub Actions run / attempt / 來源 SHA / 公開合成工件雜湊](REVIEW_CHALLENGES.md#e--verify-a-real-public-github-actions-run-without-granting-private-access)。這是零金鑰、純公開的獨立來源核對入門；工件內容由工作流程自行產生，**不能當作獨立簽章或私人交易系統驗證**。

## English call for independent review volunteers

A **private, research-only cryptocurrency quantitative-analysis project** seeks **two genuinely independent technical methodology reviewers** and **a separate GitHub Actions provenance witness**. **No positive expectancy has been validated and no real-money trading is authorized.**

Reviewers should be comfortable with Python, backtest leakage/overfitting, time-series and clustered-loss tail risk, sequential equity/cash-flow reconciliation, fees/slippage/funding and adversarial negative controls. The CI witness should independently validate immutable Git source identities, actual CI runs/attempts, execution steps and artifact digests.

The work is **unpaid and voluntary**. We initially ask only for an optional **20–30 minute scoping discussion** (asynchronous GitHub comments are fine). **An honest HOLD or REJECT is valuable.** This is neither a profitability claim nor an investment invitation.

**Apply by commenting on [Volunteer Intake Issue #1](https://github.com/s99s67dzp2-eng/kaito-review-volunteers/issues/1).** You may answer one [synthetic challenge](REVIEW_CHALLENGES.md) and review the [scope and security policy](SECURITY_AND_SCOPE.md).

## Non-negotiable access and evidence boundaries

- This is **only a separate public recruitment repository**, not the private trading source. **No source, API key, password, seed phrase, signing private key, exchange account access, withdrawal or transfer authority is requested or granted.**
- Applying does **not** grant access to private code or GitHub collaborator/write permission. Later access, if required, needs an independently verified **Owner-approved read-only method**.
- Public screening, a green CI badge or three self-generated signing keys do **not** constitute independent methodology review. No real trading, OOS/holdout release or method gate will open on that basis.
- Please keep replies to public GitHub handles and relevant skills. **Do not post private personal information or credentials.**

---

**Project status:** independent reviewer recruitment **OPEN**, independent review approvals **NOT RECEIVED**, positive-expectancy validation **NOT ESTABLISHED**, live trading **OFF**.
