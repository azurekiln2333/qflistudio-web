"""Pure wrapper authorization regression checks. Never call run or process APIs."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import web_relay_authorization as auth

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("relay_guard_subject", ROOT / "run-web-relay-window.py")
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)


class WrapperGuardTests(unittest.TestCase):
    def test_missing_flag_refuses_before_receipt_or_module_reads(self):
        self.assertIn("--execute-reviewed", wrapper.reviewed_authorization(None)[2])

    def test_missing_root_raw_pin_refuses(self):
        self.assertIn("root-reviewed raw", wrapper.reviewed_authorization(
            SimpleNamespace(execute_reviewed=True))[2])

    def test_validator_source_drift_refuses_before_import(self):
        args = SimpleNamespace(execute_reviewed=True, reviewed_raw_sha256="a" * 64)
        with patch.object(wrapper, "AUTHORIZATION_SHA256", "0" * 64):
            self.assertIn("module changed", wrapper.reviewed_authorization(args)[2])

    def test_valid_receipt_is_pure_then_consumes_once_across_names(self):
        # This event is a unit fixture. It is never passed to run(), a CLI,
        # a channel publisher, a Job or an SDK.
        event = {"seq": 90001, "author": "c-coordinator", "grant": "C900-SOURCECONTROL",
                 "successor": "c-coordinator", "product": "web", "scope": "global",
                 "protocol": "web-relay-format-app/v1"}
        now = datetime.now(timezone.utc)
        raw = {"kind": "message", "by": "c-coordinator", "seq": event["seq"],
               "ts": now.isoformat(), "text": "Unit fixture only; no runtime grant.",
               "origin": "cli", "to": ["web-offline-1022"]}
        hashes = auth.hashes_for(wrapper.__file__, wrapper.RUNNER,
                                 wrapper.WORKER, wrapper.HELPER)
        receipt, problem = auth.build_receipt(
            event=event, raw_event=raw, successor="c-coordinator",
            wrapper_sha256=hashes["wrapper"], frozen=hashes["frozen"],
            issued_at=now.isoformat(), expires_at=(now + timedelta(minutes=5)).isoformat(),
            now=now)
        self.assertIsNone(problem)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "receipt.json"
            target.write_text(json.dumps(receipt), encoding="utf-8")
            args = SimpleNamespace(execute_reviewed=True,
                reviewed_raw_sha256=auth.digest_of(raw), authorization=str(target),
                grant=event["grant"], next_owner="c-coordinator", run_name="first")
            with patch.object(wrapper, "RESEARCH", base):
                self.assertIsNone(wrapper.reviewed_authorization(args)[2])
                self.assertFalse((base / ".web-relay-consumed").exists())
                self.assertIsNone(wrapper.reviewed_authorization(args, consume=True)[2])
                args.run_name = "different-name"
                self.assertIn("consumed", wrapper.reviewed_authorization(args, consume=True)[2])
                self.assertEqual(len(list((base / ".web-relay-consumed").iterdir())), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
