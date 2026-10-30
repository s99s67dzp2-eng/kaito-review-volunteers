#!/usr/bin/env python3
"""Unexecuted candidate: one-file, rollback-preserving READ-ONLY diagnostic cutover.

DEFAULT: HOLD exit 3; explicit source-only check remains HOLD exit 3.
APPLY is disabled unless a human enters a separate explicit approval phrase.
No Bitget keys, network, funds, journal, private snapshots, timer or service
stop/start/restart, unit file or environment changes.
No host application has been approved or performed by this repository change.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import tempfile

from tools import kaito_bitget_main_ro_diag_host_preflight as pre

WORKER = Path("/nonexistent/review-only/observer/tools/kaito_bitget_main_ro_dual_worker.py")
CANDIDATE = Path("/nonexistent/review-only/candidate/tools/kaito_bitget_main_ro_dual_worker.py")
ROLLBACK = Path("/nonexistent/review-only/candidate/rollback")
LOCK = Path("/nonexistent/review-only/cutover.lock")
OLD = pre.INSTALLED["WORKER"][1]
NEW = pre.CANDIDATE["WORKER"][1]
EXPECTED = pre.EXPECTED_HOST
MAX = pre.MAX_MODULE_BYTES
APPROVAL = "--owner-authorized-single-file-observer-change"
ROLLBACK_APPROVAL = "--owner-authorized-single-file-observer-rollback"

# This unreviewed candidate MUST NOT perform production host mutations.
# Only a later, independent, explicitly Owner-approved release may change it.
# A public command-line phrase alone does not establish Owner authorization.
MUTATION_RELEASED = False


class UnsafeCutover(Exception):
    pass


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _read_exact(p: Path, sha: str, *, require_root: bool = True) -> bytes:
    # Never follow symbolic links; only bounded, ordinary non-writable code.
    try:
        st = p.lstat()
        if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1
                or (require_root and st.st_uid != 0)
                or st.st_mode & 0o022 or st.st_size < 1 or st.st_size > MAX):
            raise UnsafeCutover()
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            opened = os.fstat(fd)
            if ((opened.st_dev, opened.st_ino, opened.st_size) !=
                    (st.st_dev, st.st_ino, st.st_size)):
                raise UnsafeCutover()
            b = os.read(fd, MAX + 1)
            if len(b) != st.st_size or _hash(b) != sha:
                raise UnsafeCutover()
            return b
        finally:
            os.close(fd)
    except (OSError, ValueError, TypeError) as exc:
        raise UnsafeCutover() from None


def _write_staged(directory: Path, data: bytes, mode: int) -> Path:
    fd, name = tempfile.mkstemp(prefix=".kaito-ro-diagnostic-", dir=directory)
    p = Path(name)
    try:
        os.fchmod(fd, mode)
        n = 0
        while n < len(data):
            q = os.write(fd, data[n:])
            if q <= 0:
                raise UnsafeCutover()
            n += q
        os.fsync(fd)
    except BaseException:
        try:
            p.unlink(missing_ok=True)
        finally:
            os.close(fd)
        raise
    os.close(fd)
    return p


def _fsync_dir(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _swap_one_file(worker: Path, candidate: Path, backupdir: Path,
                   *, require_root: bool = True,
                   expected_current: str | None = None,
                   expected_next: str | None = None,
                   simulate_post_commit_failure: bool = False) -> str:
    """Only this callable mutates; used with TEMP fixture in offline tests.

    One os.replace() is atomic; existing service imports either old or new
    complete module. A protected old-source backup is persisted BEFORE swap.
    No timer state or credentials are touched. Fsync backup, staged and dir.
    """
    # Resolve pin values at invocation time, not at function definition.
    if expected_current is None:
        expected_current = OLD
    if expected_next is None:
        expected_next = NEW
    old = _read_exact(worker, expected_current, require_root=require_root)
    new = _read_exact(candidate, expected_next, require_root=require_root)
    if not pre.safe_directory(worker.parent) and require_root:
        raise UnsafeCutover()
    if not pre.safe_directory(backupdir) and require_root:
        raise UnsafeCutover()
    # Stable SHA-addressed rollback, never clobber an existing backup.
    backup = backupdir / ("worker-" + expected_current + ".py")
    backup_stage = _write_staged(backupdir, old, 0o600)
    try:
        try:
            os.link(backup_stage, backup)
        except FileExistsError:
            _read_exact(backup, expected_current, require_root=require_root)
    finally:
        backup_stage.unlink(missing_ok=True)
    _fsync_dir(backupdir)
    staging = None
    committed = False
    try:
        staging = _write_staged(worker.parent, new, 0o644)
        if _hash(_read_exact(staging, expected_next,
                             require_root=require_root)) != expected_next:
            raise UnsafeCutover()
        os.replace(staging, worker)
        staging = None
        committed = True
        _fsync_dir(worker.parent)
        if simulate_post_commit_failure or _hash(
                _read_exact(worker, expected_next,
                            require_root=require_root)) != expected_next:
            raise UnsafeCutover()
    except BaseException:
        if committed:
            # Restore exactly the original source; never overwrite receipts.
            recover = _write_staged(worker.parent, old, 0o644)
            try:
                os.replace(recover, worker)
                _fsync_dir(worker.parent)
            finally:
                recover.unlink(missing_ok=True)
            if _hash(_read_exact(worker, expected_current,
                                require_root=require_root)) != expected_current:
                raise UnsafeCutover()
        if staging is not None:
            staging.unlink(missing_ok=True)
        raise
    return backup.name


def _timer_active() -> bool:
    try:
        p = subprocess.run(
            ["systemctl", "is-active", "--quiet", "review-only-observer.timer"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5, check=False,
        )
        return p.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _precheck() -> bool:
    # Exact old worker, WS probe, legacy verifier and candidate digest.
    # The preflight's HOLD finding is *not* authority by itself.
    try:
        d = pre.inspect()
        if not (d["finding"] == "EXACT_SOURCE_ONLY_REVIEW_READY"
                and d["existing_timer_active"] is True
                and d["host_label_expected"] is True
                and d["root_operator"] is True
                and pre.safe_directory(ROLLBACK)
                and pre.safe_directory(WORKER.parent)
                and pre.safe_directory(CANDIDATE.parent)
                and pre.safe_directory(CANDIDATE.parent.parent)
                and _timer_active()):
            return False
        _read_exact(WORKER, OLD)
        _read_exact(CANDIDATE, NEW)
        return True
    except Exception:
        return False


def _rollback_precheck() -> bool:
    try:
        if (os.geteuid() != 0 or socket.gethostname().split(".", 1)[0] != EXPECTED
                or not _timer_active() or not pre.safe_directory(WORKER.parent)
                or not pre.safe_directory(ROLLBACK)):
            return False
        for key in ("WS_PROBE", "LEGACY_GATE"):
            rel, digest = pre.INSTALLED[key]
            if not pre.secure_match(pre.ROOT / rel, digest):
                return False
        _read_exact(WORKER, NEW)
        _read_exact(ROLLBACK / ("worker-" + OLD + ".py"), OLD)
        return True
    except Exception:
        return False


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    output = {"schema": "KAITO_MAIN_RO_ONE_FILE_DIAGNOSTIC_CUTOVER_V1",
              "status": "HOLD", "result": "NOT_ENABLED",
              "live_trading": False, "api_write": False,
              "credentials_touched": False, "timer_changed": False,
              "history_changed": False}
    if args == ["--source-preflight"]:
        output["result"] = "SOURCE_CHECK_HOLD" if not _precheck() else "SOURCE_REVIEW_ONLY"
    elif args in (["--apply", APPROVAL], ["--rollback", ROLLBACK_APPROVAL]) and not MUTATION_RELEASED:
        # Check before even opening the lock or reading host source files.
        output["result"] = "MUTATION_NOT_RELEASED"
    elif args == ["--rollback", ROLLBACK_APPROVAL]:
        # Separate explicit Owner approval; never run from CI or via chatbot.
        if os.geteuid() != 0 or socket.gethostname().split(".", 1)[0] != EXPECTED:
            output["result"] = "HOST_OR_OWNER_NOT_AUTHORIZED"
        else:
            try:
                fd = os.open(LOCK, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
                try:
                    lock_stat = os.fstat(fd)
                    if (not stat.S_ISREG(lock_stat.st_mode)
                            or lock_stat.st_uid != 0
                            or stat.S_IMODE(lock_stat.st_mode) != 0o600
                            or lock_stat.st_nlink != 1):
                        raise UnsafeCutover()
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    if not _rollback_precheck():
                        output["result"] = "ROLLBACK_SOURCE_UNVERIFIED"
                    else:
                        _swap_one_file(
                            WORKER, ROLLBACK / ("worker-" + OLD + ".py"),
                            ROLLBACK, expected_current=NEW, expected_next=OLD
                        )
                        output["result"] = "SOURCE_ONLY_ROLLBACK_MONITOR_STILL_HOLD"
                finally:
                    os.close(fd)
            except (OSError, UnsafeCutover, BlockingIOError):
                output["result"] = "ROLLBACK_NOT_VERIFIED"
    elif args == ["--apply", APPROVAL]:
        # Manual Owner command only after separate independent review.
        # Never remote-triggered from CI, Railway or ChatGPT.
        if os.geteuid() != 0 or socket.gethostname().split(".", 1)[0] != EXPECTED:
            output["result"] = "HOST_OR_OWNER_NOT_AUTHORIZED"
        else:
            try:
                fd = os.open(LOCK, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
                try:
                    lock_stat = os.fstat(fd)
                    if (not stat.S_ISREG(lock_stat.st_mode)
                            or lock_stat.st_uid != 0
                            or stat.S_IMODE(lock_stat.st_mode) != 0o600
                            or lock_stat.st_nlink != 1):
                        raise UnsafeCutover()
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    if not _precheck():
                        output["result"] = "SOURCE_OR_TIMER_NOT_REVIEW_READY"
                    else:
                        _swap_one_file(WORKER, CANDIDATE, ROLLBACK)
                        # Do not claim the Bitget monitor is healthy.
                        output["result"] = "SOURCE_ONLY_UPDATED_MONITOR_STILL_HOLD"
                finally:
                    os.close(fd)
            except (OSError, UnsafeCutover, BlockingIOError):
                output["result"] = "CUTOVER_OR_ROLLBACK_UNVERIFIED"
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    # A code-file transition is NEVER proof of real signed data or permission.
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
