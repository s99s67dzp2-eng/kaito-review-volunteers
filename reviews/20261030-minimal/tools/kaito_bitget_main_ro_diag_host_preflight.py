#!/usr/bin/env python3
"""Source-only metadata preflight for a *possible* two-module diagnostic cutover.

Always HOLD / exit 3. Never retrieves a Bitget API key, private journal,
portfolio data, environment, unit contents, or changes files/service/timer.
The source hashes here are an exact-version guard, not a deployment approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys

EXPECTED_HOST = "review-only-host-placeholder"
ROOT = Path("/nonexistent/review-only/observer")
# Existing owner-observed production baselines, not draft branch hashes.
INSTALLED = {
    "WORKER": ("tools/kaito_bitget_main_ro_dual_worker.py",
               "0000000000000000000000000000000000000000000000000000000000000000"),
    "WS_PROBE": ("tools/kaito_bitget_main_ro_ws_probe.py",
                 "0000000000000000000000000000000000000000000000000000000000000000"),
    "LEGACY_GATE": ("tools/kaito_bitget_main_ro_dual_24h_gate.py",
                    "0000000000000000000000000000000000000000000000000000000000000000"),
}
# Reviewed diagnostic-only replacement modules on the PR head; not installed.
CANDIDATE = {
    "WORKER": ("kaito_bitget_main_ro_dual_worker.py",
               "0000000000000000000000000000000000000000000000000000000000000000"),
    "WS_PROBE": ("kaito_bitget_main_ro_ws_probe.py",
                 "0000000000000000000000000000000000000000000000000000000000000000"),
}
MAX_MODULE_BYTES = 128 * 1024


def _safe_root_file(st) -> bool:
    return (stat.S_ISREG(st.st_mode) and st.st_uid == 0
            and not (st.st_mode & 0o022)
            and 0 < st.st_size <= MAX_MODULE_BYTES and st.st_nlink == 1)


def secure_match(path: Path, digest: str) -> bool:
    """Bounded exact digest of regular root-owned, non-group-writable code."""
    try:
        st = path.lstat()
        if not _safe_root_file(st):
            return False
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            opened = os.fstat(fd)
            if ((opened.st_dev, opened.st_ino, opened.st_size) !=
                    (st.st_dev, st.st_ino, st.st_size)
                    or not _safe_root_file(opened)):
                return False
            h = hashlib.sha256()
            n = 0
            while True:
                block = os.read(fd, 16384)
                if not block:
                    break
                n += len(block)
                if n > MAX_MODULE_BYTES or n > st.st_size:
                    return False
                h.update(block)
            return n == st.st_size and h.hexdigest() == digest
        finally:
            os.close(fd)
    except (OSError, ValueError, TypeError):
        return False


def result(*, host: str, user_is_root: bool, installed: dict[str, bool],
           candidate: dict[str, bool], timer_active: bool | None) -> dict:
    if type(host) is not str or type(user_is_root) is not bool or (
        set(installed) != set(INSTALLED) or set(candidate) != set(CANDIDATE)
    ):
        raise ValueError("bad synthetic result input")
    exact_host = host.split(".", 1)[0] == EXPECTED_HOST
    matched = (exact_host and user_is_root
               and all(x is True for x in installed.values())
               and all(x is True for x in candidate.values())
               and timer_active is True)
    return {
        "schema": "KAITO_MAIN_RO_DIAGNOSTIC_CUTOVER_PREFLIGHT_V1",
        "status": "HOLD",
        "finding": "EXACT_SOURCE_ONLY_REVIEW_READY" if matched
                   else "SOURCE_OR_RUNTIME_NOT_REVIEW_READY",
        "host_label_expected": exact_host,
        "root_operator": user_is_root,
        "installed_module_hash_matches": installed,
        "diagnostic_bundle_hash_matches": candidate,
        "existing_timer_active": timer_active,
        "host_guest_signer_verified": False,
        "authenticated_bitget_verified": False,
        "full_key_consumer_inventory_verified": False,
        "rollback_executed_verified": False,
        "cutover_authorized": False,
        "credential_access": False,
        "api_write": False,
        "service_mutation": False,
        "live_trading": False,
        "funds_movement": False,
    }


def safe_directory(path: Path) -> bool:
    try:
        st = path.lstat()
        return (stat.S_ISDIR(st.st_mode) and st.st_uid == 0
                and not (st.st_mode & 0o022))
    except OSError:
        return False


def inspect() -> dict:
    # Inspect trusted code and systemd's active-state bit; NO journal, API, key.
    # Caller must run from independently reviewed root-managed candidate checkout.
    here = Path(__file__).resolve().parent
    installed_dirs_safe = safe_directory(ROOT) and safe_directory(ROOT / "tools")
    candidate_dir_safe = safe_directory(here)
    installed = {k: installed_dirs_safe and secure_match(ROOT / rel, digest)
                 for k, (rel, digest) in INSTALLED.items()}
    candidate = {k: candidate_dir_safe and secure_match(here / rel, digest)
                 for k, (rel, digest) in CANDIDATE.items()}
    try:
        p = subprocess.run(
            ["systemctl", "is-active", "--quiet", "review-only-observer.timer"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5, check=False,
        )
        timer_active = p.returncode == 0
    except (OSError, subprocess.SubprocessError):
        timer_active = None
    return result(host=socket.gethostname(), user_is_root=os.geteuid() == 0,
                  installed=installed, candidate=candidate,
                  timer_active=timer_active)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--inspect-source-only"]:
        try:
            output = inspect()
        except Exception:
            output = {"schema": "KAITO_MAIN_RO_DIAGNOSTIC_CUTOVER_PREFLIGHT_V1",
                      "status": "HOLD", "finding": "INSPECTION_UNAVAILABLE",
                      "api_write": False, "live_trading": False}
    else:
        output = {"schema": "KAITO_MAIN_RO_DIAGNOSTIC_CUTOVER_PREFLIGHT_V1",
                  "status": "HOLD", "finding": "DISABLED",
                  "api_write": False, "live_trading": False}
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 3  # Never authorize cutover even if exact source matches.


if __name__ == "__main__":
    raise SystemExit(main())
