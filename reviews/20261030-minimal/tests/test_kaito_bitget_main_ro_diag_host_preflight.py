"""Source-only negative controls for the pending owner-side host preflight."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import kaito_bitget_main_ro_diag_host_preflight as pre


class HostDiagnosticPreflightTest(unittest.TestCase):
    def base(self):
        return dict(
            host=pre.EXPECTED_HOST,
            user_is_root=True,
            installed={k: True for k in pre.INSTALLED},
            candidate={k: True for k in pre.CANDIDATE},
            timer_active=True,
        )

    def test_matching_sources_never_authorize_any_mutation(self):
        r = pre.result(**self.base())
        self.assertEqual(r["status"], "HOLD")
        self.assertEqual(r["finding"], "EXACT_SOURCE_ONLY_REVIEW_READY")
        for k in (
            "host_guest_signer_verified",
            "authenticated_bitget_verified",
            "full_key_consumer_inventory_verified",
            "rollback_executed_verified",
            "cutover_authorized", "credential_access",
            "api_write", "service_mutation", "live_trading", "funds_movement",
        ):
            self.assertIs(r[k], False)
        raw = json.dumps(r)
        self.assertNotIn("API_SECRET", raw)
        self.assertNotIn("main_uid", raw)

    def test_unknown_host_nonroot_old_digest_candidate_digest_and_timer_hold(self):
        for change in (
            {"host": "attacker.example"},
            {"user_is_root": False},
            {"installed": {**self.base()["installed"], "WORKER": False}},
            {"installed": {**self.base()["installed"], "LEGACY_GATE": False}},
            {"candidate": {**self.base()["candidate"], "WS_PROBE": False}},
            {"timer_active": False},
            {"timer_active": None},
        ):
            data = self.base()
            data.update(change)
            r = pre.result(**data)
            self.assertEqual(r["finding"], "SOURCE_OR_RUNTIME_NOT_REVIEW_READY")
            self.assertEqual(r["status"], "HOLD")
            self.assertFalse(r["cutover_authorized"])

    def test_unexpected_keys_rejected_before_reporting(self):
        for slot in ("candidate", "installed"):
            data = self.base()
            data[slot] = {**data[slot], "EXTRA": True}
            with self.assertRaises(ValueError):
                pre.result(**data)

    def test_synthetic_file_metadata_permissions_fail_closed(self):
        good = SimpleNamespace(st_mode=stat.S_IFREG | 0o644,
                               st_uid=0, st_size=20, st_nlink=1)
        self.assertTrue(pre._safe_root_file(good))
        for extra in (
            {"st_mode": stat.S_IFLNK | 0o777},
            {"st_mode": stat.S_IFREG | 0o666},
            {"st_uid": 1000},
            {"st_size": 0},
            {"st_size": pre.MAX_MODULE_BYTES + 1},
            {"st_nlink": 2},
        ):
            v = SimpleNamespace(**{**vars(good), **extra})
            self.assertFalse(pre._safe_root_file(v))

    def test_missing_symlink_or_untrusted_source_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "candidate.py"
            p.write_bytes(b"test-contents")
            link = Path(tmp) / "redirect.py"
            link.symlink_to(p)
            self.assertFalse(pre.secure_match(link, "0" * 64))
            self.assertFalse(pre.secure_match(p, "0" * 64))
            self.assertFalse(pre.secure_match(Path(tmp) / "absent", "0" * 64))
            self.assertFalse(pre.safe_directory(Path(tmp) / "absent"))

    def test_explicit_cli_cannot_grant_cutover_even_if_inspection_is_green(self):
        with patch.object(pre, "inspect", return_value=pre.result(**self.base())):
            from contextlib import redirect_stdout
            from io import StringIO
            output = StringIO()
            with redirect_stdout(output):
                status = pre.main(["--inspect-source-only"])
            self.assertEqual(status, 3)
            self.assertFalse(json.loads(output.getvalue())["cutover_authorized"])

    def test_cli_disabled_by_default_no_guest_or_secret_access(self):
        p = subprocess.run([sys.executable, "-m",
                            "tools.kaito_bitget_main_ro_diag_host_preflight"],
                           capture_output=True, text=True, check=False)
        self.assertEqual(p.returncode, 3)
        self.assertFalse(p.stderr)
        j = json.loads(p.stdout)
        self.assertEqual(j["finding"], "DISABLED")
        self.assertFalse(j["api_write"])


if __name__ == "__main__":
    unittest.main()
