# Deployment-mechanism review draft — NOT PUBLISHED / NOT INSTALLABLE

本包尚未公開，僅供擁有者確認公開範圍。不要上傳至正式主機或拿來替換現有工具。

## Proposed disclosure / 預計公開內容
- Two Python modules: source metadata/hash preflight; atomic single-file replacement with backup and rollback.
- Two synthetic unittest modules (16 tests) and empty package markers.
- This scope/limitations document, test results and SHA256 manifest.
- Project/module names and algorithm structure remain visible. Publication would disclose this limited implementation.

## Removed / 已移除
Real hostname, production filesystem locations, actual timer name, installed/candidate source fingerprint constants. Host uses a deliberately mismatching example; paths are nonexistent placeholders; pinned digests are zero placeholders. MUTATION_RELEASED remains False.
No account identifiers, balances, credential files, IP addresses, logs, screenshots, trading strategies or Bitget network/signing implementation are included.

## Reproduce (Linux, Python 3.12, no third-party packages)
From an extracted copy, as an ordinary user:

    python3 -m unittest discover -s tests -v

Tests use temporary files and mocked observations. Do not pass deployment flags or modify the release lock for production use. Internal swap routines really write temporary fixture files during tests.

## What the review can establish
Review the metadata validation, expected-hash checks, backup ordering, atomic rename, exception rollback, and default/CLI release lock. Report reproducible failure cases with line references and tests; do not request keys or server access.

## What it cannot establish
This is a SANITIZED DERIVATIVE, not byte-identical production source. Passing tests or reviewing this package does not approve the private exact version. Private-to-public substitutions must be reviewed before applying any findings to deployment.
The observer, WebSocket client and credential/network code are excluded; neither DATA_INVALID root cause nor real Bitget access nor 24-hour continuity is demonstrated. A reviewer of this subset cannot approve the omitted code.
No independent review, deployment permission, power-loss durability, concurrent administrator safety or live recovery is claimed. Inspect especially symlink/ancestor trust, concurrent file changes, partial I/O, interruption around rename/fsync and rollback when the timer is inactive.

## Publication
No public repository mutation or external message was performed when preparing this ZIP. Owner approval is required before publishing this specific disclosure scope. Keep the primary repository private.
