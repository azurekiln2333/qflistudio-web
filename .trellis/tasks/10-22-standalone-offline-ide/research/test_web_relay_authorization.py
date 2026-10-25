"""Pure unit controls for web_relay_authorization.

No process, Job, SDK, channel read, channel write or network call. Markers use a
temporary directory. Every case calls the real function under test.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import web_relay_authorization as auth

WRAPPER_SHA = "a" * 64
FROZEN = {"runner": "b" * 64, "worker": "c" * 64, "helper": "d" * 64}
HASHES = {"wrapper": WRAPPER_SHA, "frozen": dict(FROZEN)}
EVENT = {"seq": 4211, "author": "c-coordinator", "grant": "C608-REALRUN",
         "successor": "c-coordinator", "product": "web", "scope": "global",
         "protocol": "web-relay-format-app/v1"}
RAW = {"by": "c-coordinator", "seq": 4211, "kind": "grant",
       "ts": "2026-10-26T03:58:40+00:00",
       "text": "Web ACCEPT C608-REALRUN to c-coordinator. Window 180s."}
COMMAND = {"grant": "C608-REALRUN", "successor": "c-coordinator",
           "windowSeconds": 180}
NOW = datetime(2026, 10, 26, 4, 0, tzinfo=timezone.utc)
ISSUED = "2026-10-26T03:59:00+00:00"
EXPIRES = "2026-10-26T04:05:00+00:00"

# Frozen public surface. Root integrates against exactly this list.
FROZEN_API = ("RECEIPT_SCHEMA", "WINDOW_SECONDS", "MAX_RECEIPT_LIFETIME_SECONDS",
              "MIN_REMAINING_SECONDS", "CLOCK_SKEW_SECONDS", "EXECUTE_FLAG",
              "MARKER_SUFFIX", "EXPECTED_COORDINATOR", "EXPECTED_PRODUCT",
              "EXPECTED_SCOPE", "EXPECTED_PROTOCOL", "PLACEHOLDER_TOKENS",
              "FORBIDDEN_IMPORTS", "GRANT_RE", "OWNER_RE", "SHA256_RE",
              "EVENT_FIELDS", "MARKER_FIELDS", "RAW_EVENT_FIELDS", "FROZEN_KEYS",
              "RECEIPT_FIELDS", "utc_now", "canonical", "digest_of",
              "file_sha256", "hashes_for", "parse_utc", "placeholder_tokens",
              "grant_problem", "event_problem", "raw_event_problem",
              "binding_fields", "receipt_id", "marker_binding", "marker_id",
              "marker_path", "consume_marker", "validate_receipt",
              "build_receipt", "decide_execution", "snapshot", "main",
              "self_test")


def base_receipt():
    """A valid receipt dict, built by hand so any field stays mutable."""
    return {
        "schemaVersion": auth.RECEIPT_SCHEMA,
        "grant": EVENT["grant"],
        "successor": EVENT["successor"],
        "windowSeconds": auth.WINDOW_SECONDS,
        "issuedAtUtc": ISSUED,
        "expiresAtUtc": EXPIRES,
        "issuedBy": "root",
        "wrapperSha256": WRAPPER_SHA,
        "frozen": dict(FROZEN),
        "coordinatorEvent": {field: EVENT[field] for field in auth.EVENT_FIELDS},
        "coordinatorEventSha256": auth.digest_of(EVENT),
        "rawEvent": dict(RAW),
        "rawEventSha256": auth.digest_of(RAW),
    }


def make_receipt(**overrides):
    receipt = base_receipt()
    receipt.update(overrides)
    return receipt


def build(event=EVENT, raw=RAW, **overrides):
    receipt, problem = auth.build_receipt(
        event=event, raw_event=raw,
        successor=overrides.pop("successor", "c-coordinator"),
        wrapper_sha256=overrides.pop("wrapper_sha256", WRAPPER_SHA),
        frozen=overrides.pop("frozen", dict(FROZEN)),
        issued_at=overrides.pop("issued_at", ISSUED),
        expires_at=overrides.pop("expires_at", EXPIRES), now=NOW)
    return receipt, problem


class GrantShapeTests(unittest.TestCase):
    """Any grant shape alone authorizes nothing."""

    def test_shaped_grant_without_receipt_is_refused(self):
        decision = auth.decide_execution(
            flags=(auth.EXECUTE_FLAG,), receipt={}, command=COMMAND,
            event=EVENT, hashes=HASHES, marker_dir="unused")
        self.assertFalse(decision["execute"])

    def test_absent_flag_is_refused(self):
        with tempfile.TemporaryDirectory() as markers:
            decision = auth.decide_execution(
                flags=(), receipt=make_receipt(), command=COMMAND, event=EVENT,
                hashes=HASHES, marker_dir=markers, now=NOW)
            self.assertFalse(decision["execute"])
            self.assertIn(auth.EXECUTE_FLAG, decision["reason"])
            self.assertEqual(list(Path(markers).iterdir()), [])

    def test_grant_not_in_coordinator_event_is_refused(self):
        problems = auth.validate_receipt(make_receipt(), command=COMMAND,
                                         event=dict(EVENT, grant="C608-OTHER"),
                                         hashes=HASHES, now=NOW)
        self.assertTrue(any("coordinator event grant" in item for item in problems))

    def test_placeholder_tokens_are_refused(self):
        for grant in ("C607-NEG", "C608-VALID", "C608-TEST", "C608-DUMMY"):
            self.assertIsNotNone(auth.grant_problem(grant), grant)

    def test_placeholder_event_cannot_build_a_receipt(self):
        receipt, problem = build(event=dict(EVENT, grant="C607-NEG"),
                                raw=dict(RAW))
        self.assertIsNone(receipt)
        self.assertIn("Placeholder", problem)


class RawEventTests(unittest.TestCase):
    """The raw channel record is preserved verbatim and never parsed."""

    def test_raw_fields_are_the_five_channel_fields(self):
        self.assertEqual(auth.RAW_EVENT_FIELDS, ("by", "text", "seq", "ts", "kind"))

    def test_good_raw_is_accepted(self):
        self.assertIsNone(auth.raw_event_problem(RAW))

    def test_raw_requires_every_field(self):
        for field in auth.RAW_EVENT_FIELDS:
            partial = {key: value for key, value in RAW.items() if key != field}
            self.assertIsNotNone(auth.raw_event_problem(partial), field)

    def test_receipt_preserves_the_raw_record(self):
        receipt, problem = build()
        self.assertIsNone(problem)
        self.assertEqual(receipt["rawEvent"], RAW)
        self.assertEqual(receipt["rawEventSha256"], auth.digest_of(RAW))

    def test_raw_digest_mismatch_is_rejected(self):
        problems = auth.validate_receipt(make_receipt(rawEventSha256="e" * 64),
                                         command=COMMAND, event=EVENT,
                                         hashes=HASHES, now=NOW)
        self.assertTrue(any("exact raw event" in item for item in problems), problems)

    def test_raw_sender_must_be_the_event_author(self):
        problems = auth.validate_receipt(
            make_receipt(rawEvent=dict(RAW, by="d-coordinator")),
            command=COMMAND, event=EVENT, hashes=HASHES, now=NOW)
        self.assertTrue(any("Raw event sender" in item for item in problems), problems)

    def test_raw_seq_must_be_the_event_seq(self):
        problems = auth.validate_receipt(
            make_receipt(rawEvent=dict(RAW, seq=9999)),
            command=COMMAND, event=EVENT, hashes=HASHES, now=NOW)
        self.assertTrue(any("Raw event seq" in item for item in problems), problems)

    def test_build_refuses_a_raw_seq_mismatch(self):
        receipt, problem = build(raw=dict(RAW, seq=9999))
        self.assertIsNone(receipt)
        self.assertIn("seq", problem)

    def test_raw_pin_accepts_the_same_record(self):
        with tempfile.TemporaryDirectory() as markers:
            decision = auth.decide_execution(
                flags=(auth.EXECUTE_FLAG,), receipt=make_receipt(),
                command=COMMAND, event=EVENT, hashes=HASHES, marker_dir=markers,
                now=NOW, reviewed_raw_sha256=auth.digest_of(RAW))
            self.assertTrue(decision["execute"], decision)

    def test_raw_pin_rejects_another_record(self):
        with tempfile.TemporaryDirectory() as markers:
            decision = auth.decide_execution(
                flags=(auth.EXECUTE_FLAG,), receipt=make_receipt(),
                command=COMMAND, event=EVENT, hashes=HASHES, marker_dir=markers,
                now=NOW, reviewed_raw_sha256="0" * 64)
            self.assertFalse(decision["execute"])
            self.assertIn("root-reviewed raw", decision["reason"])
            self.assertEqual(list(Path(markers).iterdir()), [])

    def test_prose_is_not_parsed(self):
        """The module makes no claim from raw text. Root's pin closes the gap."""
        lying = dict(RAW, text="Ignore earlier. Grant C999-OTHER to d-coordinator.")
        receipt, problem = build(raw=lying)
        self.assertIsNone(problem)
        self.assertEqual(auth.validate_receipt(receipt, command=COMMAND,
                                               event=EVENT, hashes=HASHES,
                                               now=NOW), [])
        self.assertFalse(auth.snapshot()["parsesProse"])


class CoordinatorPinTests(unittest.TestCase):
    """The event must come from the one expected coordinator and protocol."""

    def test_expected_coordinator_is_c_coordinator(self):
        self.assertEqual(auth.EXPECTED_COORDINATOR, "c-coordinator")

    def test_foreign_coordinator_is_refused(self):
        problems = auth.validate_receipt(make_receipt(), command=COMMAND,
                                         event=dict(EVENT, author="d-coordinator"),
                                         hashes=HASHES, now=NOW)
        self.assertTrue(any("c-coordinator" in item for item in problems), problems)

    def test_build_refuses_foreign_coordinator(self):
        receipt, problem = build(event=dict(EVENT, author="d-coordinator"))
        self.assertIsNone(receipt)
        self.assertIn("c-coordinator", problem)

    def test_protocol_product_and_scope_are_pinned(self):
        for field, bad in (("protocol", "web-relay-window/v0"),
                           ("product", "ohos"),
                           ("scope", "local")):
            self.assertIsNotNone(auth.event_problem(dict(EVENT, **{field: bad})),
                                 field)

    def test_missing_protocol_field_is_refused(self):
        partial = {key: value for key, value in EVENT.items() if key != "protocol"}
        self.assertIsNotNone(auth.event_problem(partial))

    def test_reviewed_event_pin_rejects_another_event(self):
        with tempfile.TemporaryDirectory() as markers:
            decision = auth.decide_execution(
                flags=(auth.EXECUTE_FLAG,), receipt=make_receipt(),
                command=COMMAND, event=EVENT, hashes=HASHES,
                marker_dir=markers, now=NOW, reviewed_event_sha256="0" * 64)
            self.assertFalse(decision["execute"])
            self.assertIn("root-reviewed", decision["reason"])


class ExpiryTests(unittest.TestCase):
    """Short lifetime, no future issue, enough runway for the window."""

    def assert_rejected(self, receipt, needle, now=NOW):
        problems = auth.validate_receipt(receipt, command=COMMAND, event=EVENT,
                                         hashes=HASHES, now=now)
        self.assertTrue(problems, "receipt should have been rejected")
        self.assertTrue(any(needle in item for item in problems),
                        f"expected {needle!r} in {problems}")

    def test_max_lifetime_is_ten_minutes(self):
        self.assertEqual(auth.MAX_RECEIPT_LIFETIME_SECONDS, 600)

    def test_future_issue_is_rejected(self):
        self.assert_rejected(make_receipt(issuedAtUtc="2026-10-26T04:05:00+00:00",
                                          expiresAtUtc="2026-10-26T04:09:00+00:00"),
                             "issuedAtUtc is in the future")

    def test_small_clock_skew_is_tolerated(self):
        problems = auth.validate_receipt(
            make_receipt(issuedAtUtc="2026-10-26T04:00:30+00:00",
                         expiresAtUtc="2026-10-26T04:05:30+00:00"),
            command=COMMAND, event=EVENT, hashes=HASHES, now=NOW)
        self.assertEqual(problems, [])

    def test_long_lifetime_is_rejected(self):
        self.assert_rejected(make_receipt(expiresAtUtc="2026-10-26T04:10:00+00:00"),
                             "lifetime exceeds")

    def test_insufficient_runway_is_rejected(self):
        self.assert_rejected(make_receipt(expiresAtUtc="2026-10-26T04:02:00+00:00"),
                             "less than the 180 s window")

    def test_expired_receipt_is_rejected(self):
        self.assert_rejected(make_receipt(expiresAtUtc="2026-10-26T03:59:30+00:00"),
                             "expired")

    def test_build_refuses_a_short_runway(self):
        receipt, problem = build(expires_at="2026-10-26T04:01:00+00:00")
        self.assertIsNone(receipt)
        self.assertIn("180", problem)

    def test_build_refuses_a_long_lifetime(self):
        receipt, problem = build(expires_at="2026-10-26T04:20:00+00:00")
        self.assertIsNone(receipt)
        self.assertIn("lifetime", problem)


class WindowLockTests(unittest.TestCase):
    """The window is fixed at 180. Neither caller nor receipt may widen it."""

    def test_validate_refuses_a_widened_window(self):
        receipt = make_receipt(windowSeconds=360)
        problems = auth.validate_receipt(
            receipt, command=dict(COMMAND, windowSeconds=360), event=EVENT,
            hashes=HASHES, now=NOW, window=360)
        self.assertTrue(problems, "a widened window must be refused")
        self.assertTrue(any("fixed at 180" in item for item in problems), problems)

    def test_every_problem_is_reported_for_a_widened_window(self):
        problems = auth.validate_receipt(
            make_receipt(windowSeconds=360),
            command=dict(COMMAND, windowSeconds=360), event=EVENT,
            hashes=HASHES, now=NOW, window=360)
        self.assertTrue(any("Receipt window must be 180" in item for item in problems),
                        problems)
        self.assertTrue(any("Command window must be 180" in item for item in problems),
                        problems)
        self.assertTrue(any("fixed at 180" in item for item in problems), problems)

    def test_build_refuses_a_widened_window(self):
        receipt, problem = build()
        self.assertIsNone(problem)
        widened, problem = auth.build_receipt(
            event=EVENT, raw_event=RAW, successor="c-coordinator",
            wrapper_sha256=WRAPPER_SHA, frozen=FROZEN, issued_at=ISSUED,
            expires_at=EXPIRES, now=NOW, window=360)
        self.assertIsNone(widened)
        self.assertIn("fixed at 180", problem)

    def test_decide_refuses_a_widened_window_and_burns_no_marker(self):
        with tempfile.TemporaryDirectory() as markers:
            decision = auth.decide_execution(
                flags=(auth.EXECUTE_FLAG,),
                receipt=make_receipt(windowSeconds=360),
                command=dict(COMMAND, windowSeconds=360), event=EVENT,
                hashes=HASHES, marker_dir=markers, now=NOW, window=360)
            self.assertFalse(decision["execute"], decision)
            self.assertEqual(list(Path(markers).iterdir()), [])

    def test_the_default_window_still_passes(self):
        self.assertEqual(auth.validate_receipt(make_receipt(), command=COMMAND,
                                               event=EVENT, hashes=HASHES,
                                               now=NOW), [])

    def test_window_constant_is_180(self):
        self.assertEqual(auth.WINDOW_SECONDS, 180)


class BuildRefusalTests(unittest.TestCase):
    """Any expiry problem refuses. No malformed receipt is ever produced."""

    def test_build_refuses_a_malformed_issue_time(self):
        receipt, problem = build(issued_at="not-a-time")
        self.assertIsNone(receipt)
        self.assertIn("issuedAtUtc", problem)

    def test_build_refuses_a_malformed_expiry(self):
        receipt, problem = build(expires_at="2026-13-45")
        self.assertIsNone(receipt)
        self.assertIn("expiresAtUtc", problem)

    def test_build_refuses_an_inverted_expiry(self):
        receipt, problem = build(issued_at="2026-10-26T03:58:00+00:00",
                                 expires_at="2026-10-26T03:57:00+00:00")
        self.assertIsNone(receipt)
        self.assertIn("expiry", problem)

    def test_build_refuses_a_zoneless_time(self):
        receipt, problem = build(issued_at="2026-10-26T03:59:00")
        self.assertIsNone(receipt)

    def test_build_accepts_the_good_case(self):
        receipt, problem = build()
        self.assertIsNone(problem)
        self.assertEqual(problem, None)


class BindingTests(unittest.TestCase):
    """The receipt binds the coordinator event, the raw record and the hashes."""

    def assert_rejected(self, receipt, needle, event=None, hashes=None,
                        now=NOW, command=None):
        problems = auth.validate_receipt(
            receipt, command=command or COMMAND, event=event or EVENT,
            hashes=hashes or HASHES, now=now)
        self.assertTrue(problems, "receipt should have been rejected")
        self.assertTrue(any(needle in item for item in problems),
                        f"expected {needle!r} in {problems}")

    def test_valid_receipt_has_no_problems(self):
        self.assertEqual(auth.validate_receipt(
            make_receipt(), command=COMMAND, event=EVENT, hashes=HASHES,
            now=NOW), [])

    def test_wrong_seq_is_rejected(self):
        self.assert_rejected(make_receipt(), "coordinatorEvent.seq",
                             event=dict(EVENT, seq=4210))

    def test_wrong_receipt_author_is_rejected(self):
        receipt = make_receipt()
        receipt["coordinatorEvent"] = dict(receipt["coordinatorEvent"],
                                           author="d-coordinator")
        self.assert_rejected(receipt, "coordinatorEvent.author")

    def test_wrong_successor_is_rejected(self):
        self.assert_rejected(make_receipt(), "coordinatorEvent.successor",
                             event=dict(EVENT, successor="d-coordinator"))

    def test_event_digest_binding_is_rejected(self):
        self.assert_rejected(make_receipt(coordinatorEventSha256="e" * 64),
                             "not bound to this exact coordinator event")

    def test_window_must_be_180(self):
        self.assert_rejected(make_receipt(windowSeconds=300),
                             "Receipt window must be 180")

    def test_command_window_must_be_180(self):
        self.assert_rejected(make_receipt(), "Command window must be 180",
                             command=dict(COMMAND, windowSeconds=300))

    def test_wrapper_hash_mismatch_is_rejected(self):
        self.assert_rejected(make_receipt(), "wrapper hash does not match",
                             hashes={"wrapper": "f" * 64, "frozen": dict(FROZEN)})

    def test_frozen_hash_mismatch_is_rejected(self):
        drifted = {"wrapper": WRAPPER_SHA,
                   "frozen": dict(FROZEN, runner="e" * 64)}
        self.assert_rejected(make_receipt(), "frozen.runner does not match",
                             hashes=drifted)

    def test_schema_version_is_enforced(self):
        self.assert_rejected(make_receipt(schemaVersion=2),
                             "schemaVersion must be 3")

    def test_issuer_must_be_named(self):
        self.assert_rejected(make_receipt(issuedBy="  "), "must name its issuer")

    def test_validate_writes_nothing(self):
        with tempfile.TemporaryDirectory() as workspace:
            auth.validate_receipt(make_receipt(), command=COMMAND, event=EVENT,
                                  hashes=HASHES, now=NOW)
            self.assertEqual(list(Path(workspace).iterdir()), [])


class BuildTests(unittest.TestCase):
    """Root builds a receipt from a real grant without human approval."""

    def test_build_matches_the_validated_shape(self):
        receipt, problem = build()
        self.assertIsNone(problem)
        self.assertEqual(receipt, base_receipt())
        self.assertEqual(auth.validate_receipt(receipt, command=COMMAND,
                                               event=EVENT, hashes=HASHES,
                                               now=NOW), [])

    def test_build_needs_no_human_approval_field(self):
        receipt, problem = build()
        self.assertIsNone(problem)
        self.assertEqual(receipt["issuedBy"], "root")
        self.assertNotIn("approvedBy", receipt)

    def test_build_rejects_foreign_successor(self):
        receipt, problem = build(successor="d-coordinator")
        self.assertIsNone(receipt)
        self.assertIn("Successor", problem)

    def test_build_rejects_bad_event(self):
        receipt, problem = build(event={"grant": EVENT["grant"]})
        self.assertIsNone(receipt)
        self.assertIn("seq", problem)


class ConsumptionTests(unittest.TestCase):
    """One consumption per coordinator and grant. seq never reopens the door."""

    def allow(self, markers, receipt, hashes=None, event=None, now=NOW,
              flags=(auth.EXECUTE_FLAG,)):
        return auth.decide_execution(flags=flags, receipt=receipt,
                                     command=COMMAND, event=event or EVENT,
                                     hashes=hashes or HASHES,
                                     marker_dir=markers, now=now)

    def test_marker_fields_are_author_and_grant(self):
        self.assertEqual(auth.MARKER_FIELDS, ("author", "grant"))
        self.assertEqual(auth.marker_binding(EVENT),
                         {"author": "c-coordinator", "grant": "C608-REALRUN"})
        self.assertEqual(auth.marker_id(EVENT),
                         auth.digest_of({"author": "c-coordinator",
                                         "grant": "C608-REALRUN"}))

    def test_marker_ignores_seq(self):
        self.assertEqual(auth.marker_id(EVENT), auth.marker_id(dict(EVENT, seq=4212)))
        self.assertFalse(auth.snapshot()["markerDependsOnSeq"])

    def test_new_seq_for_the_same_grant_cannot_replay(self):
        """The core control: a restated grant with a new seq is still spent."""
        with tempfile.TemporaryDirectory() as markers:
            self.assertTrue(self.allow(markers, make_receipt())["execute"])
            restated = dict(EVENT, seq=4300)
            restated_raw = dict(RAW, seq=4300, ts="2026-10-26T04:01:30+00:00",
                                text="ACK. C608-REALRUN already granted.")
            second_receipt, problem = build(event=restated, raw=restated_raw)
            self.assertIsNone(problem)
            second = self.allow(markers, second_receipt, event=restated)
            self.assertFalse(second["execute"], second)
            self.assertIn("already consumed", second["reason"])
            self.assertEqual(len(list(Path(markers).iterdir())), 1)

    def test_a_new_grant_from_the_same_coordinator_is_allowed(self):
        with tempfile.TemporaryDirectory() as markers:
            self.assertTrue(self.allow(markers, make_receipt())["execute"])
            fresh = dict(EVENT, seq=4301, grant="C609-REALRUN")
            fresh_raw = dict(RAW, seq=4301)
            receipt, problem = build(event=fresh, raw=fresh_raw)
            self.assertIsNone(problem)
            decision = auth.decide_execution(
                flags=(auth.EXECUTE_FLAG,), receipt=receipt,
                command=dict(COMMAND, grant="C609-REALRUN"), event=fresh,
                hashes=HASHES, marker_dir=markers, now=NOW)
            self.assertTrue(decision["execute"], decision)
            self.assertEqual(len(list(Path(markers).iterdir())), 2)

    def test_first_decision_allows_and_writes_one_marker(self):
        with tempfile.TemporaryDirectory() as markers:
            decision = self.allow(markers, make_receipt())
            self.assertTrue(decision["execute"], decision)
            self.assertFalse(decision["processStarted"])
            self.assertEqual(len(list(Path(markers).iterdir())), 1)

    def test_second_decision_is_a_replay(self):
        with tempfile.TemporaryDirectory() as markers:
            first = self.allow(markers, make_receipt())
            second = self.allow(markers, make_receipt())
            self.assertTrue(first["execute"])
            self.assertFalse(second["execute"])
            self.assertIn("already consumed", second["reason"])

    def test_marker_survives_a_wrapper_hash_change(self):
        with tempfile.TemporaryDirectory() as markers:
            self.assertTrue(self.allow(markers, make_receipt())["execute"])
            other = "9" * 64
            second = self.allow(markers, make_receipt(wrapperSha256=other),
                                hashes={"wrapper": other, "frozen": dict(FROZEN)})
            self.assertFalse(second["execute"], second)
            self.assertIn("already consumed", second["reason"])

    def test_marker_survives_a_new_expiry(self):
        with tempfile.TemporaryDirectory() as markers:
            self.assertTrue(self.allow(markers, make_receipt())["execute"])
            later = make_receipt(issuedAtUtc="2026-10-26T04:01:00+00:00",
                                 expiresAtUtc="2026-10-26T04:06:00+00:00")
            second = self.allow(markers, later, now=datetime(
                2026, 10, 26, 4, 2, tzinfo=timezone.utc))
            self.assertFalse(second["execute"], second)

    def test_marker_name_is_the_marker_id(self):
        with tempfile.TemporaryDirectory() as markers:
            rid = auth.marker_id(EVENT)
            consumed, problem = auth.consume_marker(markers, rid)
            self.assertTrue(consumed, problem)
            self.assertTrue(auth.marker_path(markers, rid).is_file())

    def test_exclusive_create_refuses_the_second_writer(self):
        with tempfile.TemporaryDirectory() as markers:
            rid = auth.marker_id(EVENT)
            self.assertEqual(auth.consume_marker(markers, rid), (True, None))
            consumed, problem = auth.consume_marker(markers, rid)
            self.assertFalse(consumed)
            self.assertIn("already consumed", problem)

    def test_bad_receipt_does_not_burn_the_marker(self):
        with tempfile.TemporaryDirectory() as markers:
            refused = self.allow(markers, make_receipt(windowSeconds=300))
            self.assertFalse(refused["execute"])
            self.assertEqual(list(Path(markers).iterdir()), [])
            self.assertTrue(self.allow(markers, make_receipt())["execute"])

    def test_marker_rejects_a_non_sha256_id(self):
        with tempfile.TemporaryDirectory() as markers:
            consumed, problem = auth.consume_marker(markers, "not-a-digest")
            self.assertFalse(consumed)
            self.assertIn("sha256", problem)

    def test_decision_reports_both_ids(self):
        with tempfile.TemporaryDirectory() as markers:
            decision = self.allow(markers, make_receipt())
            self.assertEqual(decision["markerId"], auth.marker_id(EVENT))
            self.assertEqual(decision["receiptId"], auth.receipt_id(base_receipt()))
            self.assertNotEqual(decision["receiptId"], decision["markerId"])


class IsolationTests(unittest.TestCase):
    """The module starts nothing, reads no channel and claims no crypto."""

    def test_module_imports_nothing_operational(self):
        source = Path(auth.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(sorted(imported & set(auth.FORBIDDEN_IMPORTS)), [])

    def test_module_has_no_launch_helper(self):
        source = Path(auth.__file__).read_text(encoding="utf-8")
        for token in ("subprocess.Popen", "os.system", "os.startfile",
                      "CreateProcess", "WinDLL"):
            self.assertNotIn(token, source)

    def test_snapshot_states_its_limits(self):
        snap = auth.snapshot()
        self.assertFalse(snap["execution"])
        self.assertFalse(snap["processStarted"])
        self.assertFalse(snap["cryptographicAuthentication"])
        self.assertFalse(snap["normalizedEventIsOriginalAuthorization"])
        self.assertFalse(snap["receiptReplacesCoordinatorGrant"])
        self.assertFalse(snap["readsChannel"])
        self.assertFalse(snap["writesChannel"])
        self.assertFalse(snap["parsesProse"])
        self.assertFalse(snap["markerDependsOnRunName"])
        self.assertFalse(snap["markerDependsOnSeq"])
        self.assertFalse(snap["markerDependsOnHashes"])
        self.assertFalse(snap["markerDependsOnExpiry"])
        self.assertTrue(snap["rawEventPreserved"])
        self.assertEqual(snap["receiptSchema"], 3)
        self.assertEqual(snap["windowSeconds"], 180)
        self.assertEqual(snap["maxReceiptLifetimeSeconds"], 600)
        self.assertEqual(snap["minRemainingSeconds"], 180)
        self.assertEqual(snap["expectedCoordinator"], "c-coordinator")

    def test_decision_never_claims_a_start(self):
        with tempfile.TemporaryDirectory() as markers:
            decision = auth.decide_execution(
                flags=(auth.EXECUTE_FLAG,), receipt=make_receipt(),
                command=COMMAND, event=EVENT, hashes=HASHES,
                marker_dir=markers, now=NOW)
            self.assertTrue(decision["execute"])
            self.assertFalse(decision["processStarted"])

    def test_self_test_passes(self):
        self.assertEqual(auth.self_test(), 0)

    def test_public_api_is_frozen(self):
        """Root integrates against these names only."""
        self.assertEqual(tuple(auth.__all__), FROZEN_API)
        for name in FROZEN_API:
            self.assertTrue(hasattr(auth, name), name)

    def test_no_extra_public_names(self):
        public = {name for name in dir(auth) if not name.startswith("_")}
        allowed = set(FROZEN_API) | {"argparse", "datetime", "timezone",
                                     "hashlib", "json", "os", "Path", "re",
                                     "annotations"}
        self.assertEqual(sorted(public - allowed), [])


class RawExtraFieldRegressionTests(unittest.TestCase):
    def test_actual_channel_optional_fields_survive_receipt_round_trip(self):
        raw = dict(RAW, origin="cli", to=["web-offline-1022"], extra={"retained": True})
        receipt, problem = auth.build_receipt(
            event=EVENT, raw_event=raw, successor=EVENT["successor"],
            wrapper_sha256=WRAPPER_SHA, frozen=FROZEN,
            issued_at=ISSUED, expires_at=EXPIRES, now=NOW)
        self.assertIsNone(problem)
        self.assertEqual(receipt["rawEvent"], raw)
        self.assertEqual(auth.validate_receipt(
            receipt, command=COMMAND, event=EVENT, hashes=HASHES, now=NOW,
            reviewed_raw_sha256=auth.digest_of(raw)), [])


class SuccessorBindingRegressionTests(unittest.TestCase):
    def test_receipt_and_command_cannot_override_coordinator_successor(self):
        receipt = base_receipt()
        receipt["successor"] = "different-owner"
        command = dict(COMMAND, successor="different-owner")
        problems = auth.validate_receipt(receipt, command=command, event=EVENT,
            hashes=HASHES, now=NOW)
        self.assertIn("Receipt successor is not the coordinator event successor", problems)


if __name__ == "__main__":
    unittest.main(verbosity=2)
