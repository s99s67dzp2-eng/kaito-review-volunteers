"""No-key synthetic review for single-file atomic diagnostic cutover candidate."""
import contextlib
from io import StringIO
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from tools import kaito_bitget_main_ro_worker_atomic_cutover as module


class AtomicWorkerCutoverTest(unittest.TestCase):
    def _fixture(self, root: Path):
        old = b"old-reviewed-worker-v1\n"
        new = b"new-fixed-labels-worker-v2\n"
        worker_dir = root / "tools"
        worker_dir.mkdir()
        backup = root / "private-rollback"
        backup.mkdir(mode=0o700)
        worker = worker_dir / "kaito_bitget_main_ro_dual_worker.py"
        candidate = root / "candidate"
        worker.write_bytes(old)
        candidate.write_bytes(new)
        worker.chmod(0o644)
        candidate.chmod(0o644)
        return old, new, worker, candidate, backup

    def _swap(self, worker, candidate, backup, old, new, **kwargs):
        with patch.object(module, "OLD", module._hash(old)), patch.object(
            module, "NEW", module._hash(new)
        ):
            return module._swap_one_file(
                worker, candidate, backup, require_root=False, **kwargs
            )

    def test_single_file_atomic_change_preserves_rollback_and_source(self):
        with tempfile.TemporaryDirectory() as d:
            old, new, worker, candidate, backup = self._fixture(Path(d))
            name = self._swap(worker, candidate, backup, old, new)
            self.assertEqual(worker.read_bytes(), new)
            self.assertEqual((backup / name).read_bytes(), old)
            self.assertEqual(stat.S_IMODE((backup / name).stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(worker.stat().st_mode), 0o644)
            self.assertEqual(candidate.read_bytes(), new)

    def test_separate_sha_pinned_emergency_rollback_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            old, new, worker, candidate, backup = self._fixture(Path(d))
            prior = self._swap(worker, candidate, backup, old, new)
            self.assertEqual(prior, "worker-" + module._hash(old) + ".py")
            with patch.object(module, "OLD", module._hash(old)), patch.object(
                module, "NEW", module._hash(new)
            ):
                current_backup = module._swap_one_file(
                    worker, backup / prior, backup, require_root=False,
                    expected_current=module._hash(new),
                    expected_next=module._hash(old),
                )
            self.assertEqual(worker.read_bytes(), old)
            self.assertEqual((backup / current_backup).read_bytes(), new)
            self.assertEqual((backup / prior).read_bytes(), old)
            # Re-applying after a verified rollback may re-use the exact
            # SHA-addressed prior backup, but can never overwrite it.
            self._swap(worker, candidate, backup, old, new)
            self.assertEqual(worker.read_bytes(), new)
            self.assertEqual((backup / prior).read_bytes(), old)

    def test_stale_or_unexpected_existing_backup_refuses_cutover(self):
        with tempfile.TemporaryDirectory() as d:
            old, new, worker, candidate, backup = self._fixture(Path(d))
            stale = backup / ("worker-" + module._hash(old) + ".py")
            stale.write_bytes(b"wrong-backup")
            stale.chmod(0o600)
            with self.assertRaises(module.UnsafeCutover):
                self._swap(worker, candidate, backup, old, new)
            self.assertEqual(worker.read_bytes(), old)

    def test_injected_post_replace_failure_restores_exact_worker(self):
        with tempfile.TemporaryDirectory() as d:
            old, new, worker, candidate, backup = self._fixture(Path(d))
            with self.assertRaises(module.UnsafeCutover):
                self._swap(worker, candidate, backup, old, new,
                           simulate_post_commit_failure=True)
            self.assertEqual(worker.read_bytes(), old)
            self.assertTrue(any(p.read_bytes() == old for p in backup.iterdir()))

    def test_wrong_old_digest_rejects_without_touching_file(self):
        with tempfile.TemporaryDirectory() as d:
            old, new, worker, candidate, backup = self._fixture(Path(d))
            with patch.object(module, "OLD", "0" * 64), patch.object(
                module, "NEW", module._hash(new)
            ), self.assertRaises(module.UnsafeCutover):
                module._swap_one_file(worker, candidate, backup,
                                      require_root=False)
            self.assertEqual(worker.read_bytes(), old)
            self.assertEqual(list(backup.iterdir()), [])

    def test_symlink_or_writable_candidate_refused(self):
        with tempfile.TemporaryDirectory() as d:
            old, new, worker, candidate, backup = self._fixture(Path(d))
            bad = Path(d) / "symlink"
            bad.symlink_to(candidate)
            with self.assertRaises(module.UnsafeCutover):
                self._swap(worker, bad, backup, old, new)
            candidate.chmod(0o666)
            with self.assertRaises(module.UnsafeCutover):
                self._swap(worker, candidate, backup, old, new)
            self.assertEqual(worker.read_bytes(), old)

    def test_code_update_is_never_real_exchange_attestation(self):
        with patch.object(module, "_precheck", return_value=True):
            capture = StringIO()
            with contextlib.redirect_stdout(capture):
                exit_code = module.main(["--source-preflight"])
            d = json.loads(capture.getvalue())
            self.assertEqual(exit_code, 3)
            self.assertEqual(d["status"], "HOLD")
            self.assertEqual(d["result"], "SOURCE_REVIEW_ONLY")
            self.assertFalse(d["api_write"])
            self.assertFalse(d["credentials_touched"])
            self.assertFalse(d["timer_changed"])
            self.assertFalse(d["history_changed"])

    def test_not_released_blocks_even_valid_public_approval_flags(self):
        self.assertIs(module.MUTATION_RELEASED, False)
        with patch.object(module.os, "geteuid", return_value=0), \
             patch.object(module.socket, "gethostname", return_value=module.EXPECTED), \
             patch.object(module, "_precheck", side_effect=AssertionError("PREFLIGHT_ACCESSED")), \
             patch.object(module, "_rollback_precheck",
                          side_effect=AssertionError("ROLLBACK_PREFLIGHT_ACCESSED")), \
             patch.object(module, "_swap_one_file",
                          side_effect=AssertionError("HOST_CODE_MUTATED")), \
             patch.object(module.os, "open",
                          side_effect=AssertionError("HOST_LOCK_OPENED")):
            for args in (
                ["--apply", module.APPROVAL],
                ["--rollback", module.ROLLBACK_APPROVAL],
            ):
                capture = StringIO()
                with contextlib.redirect_stdout(capture):
                    self.assertEqual(module.main(args), 3)
                result = json.loads(capture.getvalue())
                self.assertEqual(result["status"], "HOLD")
                self.assertEqual(result["result"], "MUTATION_NOT_RELEASED")
                for field in ("credentials_touched", "timer_changed",
                              "history_changed", "api_write", "live_trading"):
                    self.assertIs(result[field], False)

    def test_apply_needs_owner_explicit_flag_and_expected_host(self):
        for args in ([], ["--apply"], ["--apply", "--unauthorized"]):
            capture = StringIO()
            with contextlib.redirect_stdout(capture):
                self.assertEqual(module.main(args), 3)
            self.assertEqual(json.loads(capture.getvalue())["result"],
                             "NOT_ENABLED")
        with patch.object(module.os, "geteuid", return_value=1000):
            capture = StringIO()
            with contextlib.redirect_stdout(capture):
                self.assertEqual(module.main(
                    ["--rollback", module.ROLLBACK_APPROVAL]), 3)
            self.assertEqual(json.loads(capture.getvalue())["result"],
                             "MUTATION_NOT_RELEASED")
        with patch.object(module.os, "geteuid", return_value=1000):
            capture = StringIO()
            with contextlib.redirect_stdout(capture):
                self.assertEqual(module.main(["--apply", module.APPROVAL]), 3)
            self.assertEqual(json.loads(capture.getvalue())["result"],
                             "MUTATION_NOT_RELEASED")


if __name__ == "__main__":
    unittest.main()
