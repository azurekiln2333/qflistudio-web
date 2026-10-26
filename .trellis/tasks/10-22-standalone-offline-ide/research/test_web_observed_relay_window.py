"""Pure fake-Job observer regressions. Never instantiate a real Job or launcher."""
from __future__ import annotations

import copy
import contextlib
import io
import json
import tempfile
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "web_observed_relay_subject", ROOT / "run-web-observed-relay-window.py")
observer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer)


def root(*, terminal=True, active=0, code=0, pid=91):
    return {"pid": pid, "creationFiletime100ns": "134374558013668585",
            "terminal": terminal, "jobActiveProcesses": active, "exitCode": code}


def phase(*, code=0, pid=91):
    return {"terminalConfirmed": True, "root": root(code=code, pid=pid)}


class Clock:
    def __init__(self):
        self.now = 0.0
    def __call__(self):
        return self.now
    def sleep(self, duration):
        self.now += duration


class FakeJob:
    def __init__(self, states):
        self.states = list(states)
        self.job = 123
        self.process = 456
        self.record = {}
        self.closed = False
        self.close_count = 0
        self.stop_count = 0
        self.events = []
        self.close_error = None
    def start(self, command, directory, env, stdout, stderr):
        self.events.append("start")
        self.record.update(root(terminal=False, active=1))
        callback = getattr(self, "on_start", None)
        if callback:
            callback()
    def empty(self):
        state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        if isinstance(state, BaseException):
            self.events.append("query-error")
            raise state
        self.record.update(state)
        self.events.append((self.record["terminal"], self.record["jobActiveProcesses"]))
        return observer.root_gone(self.record)
    def stop(self):
        self.stop_count += 1
        self.events.append("stop")
    def close(self):
        self.close_count += 1
        if self.close_error:
            error, self.close_error = self.close_error, None
            raise error
        if not observer.root_gone(self.record):
            raise AssertionError("Closed a live exact Job")
        self.closed = True
        self.events.append("close")


class CustodyTests(unittest.TestCase):
    def observe(self, job, *, deadline=10, publisher=False, notify=None):
        clock = Clock()
        held = [job]
        result = {"name": "publisher" if publisher else "validation"}
        snapshots = []
        def checkpoint():
            snapshots.append((copy.deepcopy(result), list(held), job.closed))
            if notify:
                notify(result, held, job)
        observer.observe_owned(job, result, held, deadline, publisher=publisher,
            clock=clock, sleep=clock.sleep, notify=checkpoint)
        return result, held, snapshots

    def test_root_exit_does_not_release_live_descendant(self):
        job = FakeJob([root(terminal=True, active=2), root()])
        result, held, snapshots = self.observe(job)
        self.assertTrue(any(s[0].get("root", {}).get("jobActiveProcesses") == 2
                            and s[1] == [job] and not s[2] for s in snapshots))
        self.assertEqual(job.stop_count, 0)
        self.assertEqual(job.close_count, 1)
        self.assertEqual(held, [])
        self.assertEqual(result["jobHandle"], "123")
        self.assertEqual(result["processHandle"], "456")
        self.assertEqual(job.events[-1], "close")

    def test_terminal_with_live_job_never_means_phase_gone(self):
        self.assertFalse(observer.phase_gone({"terminalConfirmed": True,
            "root": root(active=1)}))

    def test_deadline_holds_original_custodian_then_eventually_cleans(self):
        job = FakeJob([root(terminal=False, active=1), root(terminal=False, active=1), root()])
        result, held, snapshots = self.observe(job, deadline=0.01)
        self.assertTrue(result["deadlineReached"])
        self.assertTrue(result["holdSeen"])
        self.assertEqual(result["status"], "TERMINAL_AFTER_HOLD")
        self.assertEqual(job.stop_count, 0)
        self.assertEqual(held, [])
        self.assertTrue(any(s[0].get("deadlineReached") and s[1] == [job]
                            and not s[2] for s in snapshots))

    def test_uncertain_query_retains_exact_handles_until_recovery(self):
        job = FakeJob([OSError("query uncertain"), root()])
        result, held, snapshots = self.observe(job)
        self.assertTrue(result["holdSeen"])
        self.assertEqual(job.stop_count, 0)
        self.assertEqual(held, [])
        self.assertTrue(any(s[0].get("queryConfirmed") is False and s[1] == [job]
                            and not s[2] for s in snapshots))

    def test_publisher_deadline_only_stops_owned_publisher(self):
        job = FakeJob([root(terminal=False, active=1), root()])
        result, held, _ = self.observe(job, deadline=0, publisher=True)
        self.assertTrue(result["forcedCleanup"])
        self.assertEqual(job.stop_count, 1)
        self.assertEqual(held, [])
        self.assertTrue(result["holdSeen"])

    def test_uncertain_publisher_remains_held_before_later_terminal(self):
        job = FakeJob([OSError("publisher unknown"), root(terminal=True, active=1), root()])
        result, held, snapshots = self.observe(job, publisher=True)
        self.assertTrue(any(s[0].get("queryConfirmed") is False and s[1] == [job]
                            and not s[2] for s in snapshots))
        self.assertTrue(result["holdSeen"])
        self.assertTrue(result["terminalConfirmed"])
        self.assertEqual(held, [])

    def test_close_failure_retains_same_object_and_cannot_promote(self):
        job = FakeJob([root(), root()])
        job.close_error = OSError("uncertain close")
        result, held, snapshots = self.observe(job)
        self.assertTrue(any(s[1] == [job] and not s[2] for s in snapshots))
        self.assertEqual(job.close_count, 2)
        self.assertTrue(result["holdSeen"])
        self.assertEqual(held, [])

    def test_terminal_snapshots_do_not_alias_job_record(self):
        job = FakeJob([root()])
        result, _, _ = self.observe(job)
        job.record["pid"] = 100
        self.assertEqual(result["root"]["pid"], 91)

    def test_evidence_exception_preserves_then_recovers_owner(self):
        job = FakeJob([root(terminal=False, active=1), root()])
        attempts = []
        def notify(*_):
            attempts.append(1)
            if len(attempts) == 1:
                raise OSError("disk busy")
        result, held, _ = self.observe(job, notify=notify)
        self.assertTrue(result["holdSeen"])
        self.assertEqual(job.stop_count, 0)
        self.assertEqual(held, [])


class ReportTests(unittest.TestCase):
    def reports(self, gate="PASS"):
        w = {"grant": "UNIT-FIXTURE", "runName": "fixture", "wrapper": root(),
             "authorization": {"rawEventSha256": "a" * 64},
             "resourcesReleased": True, "cleanupConfirmed": True,
             "handlesRetained": False, "assessment": {"gate": gate},
             **{name: phase() for name in ("accept", "sourceFormat", "supervisor", "relay")}}
        c = {"grant": "UNIT-FIXTURE", "allOwnedJobsEmpty": True,
             "terminalConfirmed": True, "phases": [phase()], "publication": phase()}
        return w, c
    def inspect(self, w, c, validation=None):
        return observer.inspect_reports(w, c, validation or phase(), grant="UNIT-FIXTURE",
            run_name="fixture", raw_pin="a" * 64)

    def test_missing_report_refuses_release_with_known_resource_clear(self):
        w, _ = self.reports()
        actual = phase()
        self.assertTrue(observer.phase_gone(actual))
        self.assertFalse(self.inspect(w, None, actual)["releaseEligible"])

    def test_failed_gate_releases_when_actual_resources_proven_clear(self):
        w, c = self.reports(gate="FAIL")
        result = self.inspect(w, c)
        self.assertTrue(result["releaseEligible"])
        self.assertEqual(result["gate"], "FAIL")

    def test_pending_child_publisher_blocks_release(self):
        w, c = self.reports()
        c["publication"]["root"]["jobActiveProcesses"] = 1
        self.assertFalse(self.inspect(w, c)["releaseEligible"])

    def test_report_cannot_substitute_another_validation_pid(self):
        w, c = self.reports()
        w["wrapper"]["pid"] = 999
        self.assertFalse(self.inspect(w, c)["releaseEligible"])

    def test_report_cannot_substitute_another_creation_identity(self):
        w, c = self.reports()
        w["wrapper"]["creationFiletime100ns"] = "10"
        self.assertFalse(self.inspect(w, c)["releaseEligible"])

    def test_child_optional_run_name_cannot_conflict_with_expected_directory(self):
        w, c = self.reports()
        c["runName"] = "another-run"
        self.assertFalse(self.inspect(w, c)["releaseEligible"])

    def test_child_next_owner_cannot_conflict_with_wrapper(self):
        w, c = self.reports()
        w["nextOwner"] = "c-coordinator"
        c["nextOwner"] = "another-owner"
        self.assertFalse(self.inspect(w, c)["releaseEligible"])

    def test_child_payload_terminal_without_zero_descendants_blocks(self):
        w, c = self.reports()
        c["phases"][0]["root"]["jobActiveProcesses"] = 2
        self.assertFalse(self.inspect(w, c)["releaseEligible"])

    def test_true_aggregate_cannot_hide_missing_wrapper_phase(self):
        w, c = self.reports()
        w.pop("sourceFormat")
        self.assertFalse(self.inspect(w, c)["releaseEligible"])

    def test_independent_raw_pin_is_checked_against_wrapper_receipt(self):
        w, c = self.reports()
        w["authorization"]["rawEventSha256"] = "b" * 64
        self.assertFalse(self.inspect(w, c)["releaseEligible"])

    def test_uncreated_process_is_not_an_exact_terminal_identity(self):
        self.assertFalse(observer.phase_gone({"terminalConfirmed": True,
            "root": {"terminal": True, "jobActiveProcesses": 0}}))


class ApprovalTests(unittest.TestCase):
    def test_existing_grant_without_observer_approval_is_not_enough(self):
        receipt = {"rawEvent": {"text": "Underlying app grant only " + "a" * 64}}
        self.assertIsNotNone(observer.observer_approval(receipt, own_sha="a" * 64,
                                                       reviewed_sha="a" * 64))

    def test_observer_approval_is_exact_source_bound(self):
        receipt = {"rawEvent": {"text": "ACCEPT " + observer.PROTOCOL + " sha256="
                    + "a" * 64 + " boundary=" + observer.CONTROL_BOUNDARY}}
        self.assertIsNone(observer.observer_approval(receipt, own_sha="a" * 64,
                                                    reviewed_sha="a" * 64))
        self.assertIsNotNone(observer.observer_approval(receipt, own_sha="b" * 64,
                                                       reviewed_sha="a" * 64))

    def test_missing_control_boundary_is_rejected(self):
        receipt = {"rawEvent": {"text": "ACCEPT " + observer.PROTOCOL
                                    + " sha256=" + "a" * 64}}
        self.assertIsNotNone(observer.observer_approval(receipt, own_sha="a" * 64,
                                                       reviewed_sha="a" * 64))

    def test_negative_mention_is_not_an_acceptance_line(self):
        receipt = {"rawEvent": {"text": "DO NOT ACCEPT " + observer.PROTOCOL
            + " sha256=" + "a" * 64 + " boundary=" + observer.CONTROL_BOUNDARY}}
        self.assertIsNotNone(observer.observer_approval(receipt, own_sha="a" * 64,
                                                       reviewed_sha="a" * 64))

    def test_missing_explicit_flag_refuses_before_source_or_receipt_reads(self):
        with patch.object(observer, "sha256", side_effect=AssertionError("read")):
            with self.assertRaisesRegex(PermissionError, "execute-reviewed"):
                observer.preflight(SimpleNamespace(execute_reviewed=False))

    def test_missing_independent_raw_pin_refuses_before_source_reads(self):
        with patch.object(observer, "sha256", side_effect=AssertionError("read")):
            with self.assertRaisesRegex(PermissionError, "raw-event"):
                observer.preflight(SimpleNamespace(execute_reviewed=True))

    def test_observer_hash_drift_refuses_before_frozen_import(self):
        args = SimpleNamespace(execute_reviewed=True, reviewed_raw_sha256="a" * 64,
                               reviewed_observer_sha256="b" * 64)
        with patch.object(observer, "sha256", return_value="c" * 64), \
             patch.object(observer, "load_wrapper", side_effect=AssertionError("import")):
            with self.assertRaisesRegex(PermissionError, "observer source pin"):
                observer.preflight(args)


class CompleteInvocationTests(unittest.TestCase):
    """Exercise real orchestration with only fake Jobs and temporary evidence."""
    def exercise(self, *, gate="PASS", missing_report=False, query_failure=False,
                 sender_exit=0, validation_exit=None, validation_elapsed=0,
                 preflight_elapsed=0, construction_elapsed=0):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            directory = base / "fixture-observed"
            args = SimpleNamespace(grant="UNIT-FIXTURE", run_name="fixture",
                next_owner="c-coordinator", authorization=str(base / "receipt.json"),
                reviewed_raw_sha256="a" * 64)
            w, c = ReportTests().reports(gate)
            order = []
            initial = observer.time.monotonic()
            timeline = [initial]
            states = ([OSError("temporarily uncertain")] if query_failure else [])
            actual_exit = (0 if gate == "PASS" else 1) if validation_exit is None else validation_exit
            validation = FakeJob(states + [root(code=actual_exit)])
            sender = FakeJob([root(pid=92, code=sender_exit)])
            def validation_start():
                order.append("validation-start")
                timeline[0] = initial + validation_elapsed
                if not missing_report:
                    (base / "fixture-relay").mkdir()
                    (base / "fixture").mkdir()
                    (base / "fixture-relay/wrapper.json").write_text(json.dumps(w), encoding="utf-8")
                    (base / "fixture/job.json").write_text(json.dumps(c), encoding="utf-8")
            def sender_start():
                self.assertTrue(validation.closed)
                self.assertTrue(observer.root_gone(validation.record))
                self.assertTrue((directory / "final-release.txt").is_file())
                order.append("sender-start-after-validation-terminal")
            validation.on_start = validation_start
            sender.on_start = sender_start
            jobs = iter([validation, sender])
            def make_job():
                job = next(jobs)
                if job is validation:
                    timeline[0] += construction_elapsed
                return job
            def preflight(_):
                timeline[0] += preflight_elapsed
                return wrapper, {}, directory
            helper = SimpleNamespace(OwnedJob=make_job,
                channel_command=lambda message, owner: ["pure-fake-publisher", str(message), owner])
            frozen = SimpleNamespace(load_helper=lambda: helper)
            spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None))
            wrapper = SimpleNamespace(RUNNER=base / "unused-frozen.py")
            with patch.object(observer, "preflight", side_effect=preflight), \
                 patch.object(observer.os, "name", "nt"), \
                 patch.object(observer, "ROOT", base), patch.object(observer, "RESEARCH", base), \
                 patch.object(observer.importlib.util, "spec_from_file_location", return_value=spec), \
                 patch.object(observer.importlib.util, "module_from_spec", return_value=frozen), \
                 patch.object(observer.time, "monotonic", side_effect=lambda: timeline[0]), \
                 contextlib.redirect_stdout(io.StringIO()):
                code = observer.run(args, started=initial)
            report = json.loads((directory / "observer.json").read_text(encoding="utf-8"))
            sender_path = directory / "final-sender.json"
            sender_report = json.loads(sender_path.read_text(encoding="utf-8")) if sender_path.exists() else None
            return code, report, sender_report, order, validation, sender

    def test_automatic_sender_follows_actual_child_terminal_in_same_invocation(self):
        code, report, sender, order, validation, publisher = self.exercise()
        self.assertEqual(code, 0)
        self.assertEqual(order, ["validation-start", "sender-start-after-validation-terminal"])
        self.assertTrue(report["releasePublished"])
        self.assertTrue(report["resourcesReleased"])
        self.assertTrue(sender["phase"]["terminalConfirmed"])
        self.assertEqual(sender["phase"]["root"]["jobActiveProcesses"], 0)
        self.assertFalse(sender["selfTerminalClaim"])
        self.assertTrue(validation.closed and publisher.closed)

    def test_failed_validation_still_automatically_releases_ownership(self):
        code, report, sender, order, _, _ = self.exercise(gate="FAIL")
        self.assertEqual(code, 1)
        self.assertTrue(report["releasePublished"])
        self.assertEqual(report["assessment"]["gate"], "FAIL")
        self.assertTrue(sender["delivered"])
        self.assertEqual(len(order), 2)

    def test_missing_report_closes_resources_without_fabricating_release(self):
        code, report, sender, order, validation, _ = self.exercise(missing_report=True)
        self.assertEqual(code, 1)
        self.assertTrue(validation.closed)
        self.assertTrue(report["resourcesReleased"])
        self.assertFalse(report["releasePublished"])
        self.assertIsNone(sender)
        self.assertEqual(order, ["validation-start"])

    def test_recovered_query_uncertainty_cannot_promote_bounded_success(self):
        code, report, sender, _, validation, _ = self.exercise(query_failure=True)
        self.assertEqual(code, 1)
        self.assertTrue(report["releasePublished"])
        self.assertTrue(report["holdSeen"])
        self.assertFalse(report["budgetLate"])
        self.assertEqual(report["localBudget"], "PROVISIONAL_WITHIN")
        self.assertEqual(validation.stop_count, 0)
        self.assertTrue(sender["delivered"])

    def test_nonzero_validation_exit_cannot_be_hidden_by_pass_gate(self):
        code, report, sender, _, _, _ = self.exercise(validation_exit=1)
        self.assertEqual(code, 1)
        self.assertEqual(report["assessment"]["gate"], "PASS")
        self.assertEqual(report["validationExitCode"], 1)
        self.assertTrue(sender["delivered"])
        self.assertTrue(report["releasePublished"])

    def test_preflight_exhaustion_refuses_validation_before_creating_job(self):
        code, report, sender, order, validation, publisher = self.exercise(preflight_elapsed=181)
        self.assertEqual(code, 1)
        self.assertFalse(order)
        self.assertFalse(validation.events)
        self.assertFalse(publisher.events)
        self.assertFalse(validation.closed)
        self.assertTrue(report["resourcesReleased"])
        self.assertFalse(report["releasePublished"])
        self.assertFalse(report["refusal"]["processStarted"])
        self.assertEqual(report["refusal"]["grantConsumption"],
                         "NOT_ATTEMPTED_BY_THIS_INVOCATION")
        self.assertTrue(report["coordinatorRelayRequired"])
        self.assertNotIn("assessment", report)
        self.assertIsNone(sender)

    def test_job_construction_exhaustion_closes_unstarted_validation_job(self):
        code, report, sender, order, validation, publisher = self.exercise(construction_elapsed=181)
        self.assertEqual(code, 1)
        self.assertFalse(order)
        self.assertNotIn("start", validation.events)
        self.assertFalse(publisher.events)
        self.assertTrue(validation.closed)
        self.assertEqual(validation.stop_count, 0)
        self.assertTrue(report["resourcesReleased"])
        self.assertFalse(report["releasePublished"])
        self.assertFalse(report["refusal"]["wrapperStarted"])
        self.assertNotIn("assessment", report)
        self.assertIsNone(sender)

    def test_late_validation_records_local_release_without_publisher_launch(self):
        code, report, sender, order, validation, publisher = self.exercise(validation_elapsed=181)
        self.assertEqual(code, 1)
        self.assertEqual(order, ["validation-start"])
        self.assertFalse(publisher.events)
        self.assertTrue(validation.closed)
        self.assertTrue(report["resourcesReleased"])
        self.assertTrue(report["budgetLate"])
        self.assertFalse(report["releasePublished"])
        self.assertFalse(sender["delivered"])
        self.assertTrue(sender["coordinatorRelayRequired"])
        self.assertEqual(sender["phase"]["admission"], "DENIED_PARENT_DEADLINE")
        self.assertTrue(report["localRelease"]["validationTerminalAndJob0"])
        self.assertTrue(report["localRelease"]["requireParentActualExitBeforeRelay"])

    def test_publisher_allowance_is_capped_by_parent_remaining_budget(self):
        self.assertEqual(observer.publisher_deadline(180, 100), 108)
        self.assertEqual(observer.publisher_deadline(180, 177), 180)
        self.assertIsNone(observer.publisher_deadline(180, 180))
        self.assertIsNone(observer.publisher_deadline(180, 181))

    def test_final_sender_nonzero_is_durable_and_cannot_pass(self):
        code, report, sender, _, _, publisher = self.exercise(sender_exit=7)
        self.assertEqual(code, 1)
        self.assertFalse(report["releasePublished"])
        self.assertEqual(sender["phase"]["root"]["exitCode"], 7)
        self.assertTrue(publisher.closed)
        self.assertTrue(sender["phase"]["terminalConfirmed"])


class MainBudgetTests(unittest.TestCase):
    def test_first_preflight_uses_same_parent_entry_budget(self):
        argv = ["observer", "--execute-reviewed", "--authorization", "fixture.json",
                "--reviewed-raw-sha256", "a" * 64,
                "--reviewed-observer-sha256", "b" * 64,
                "--grant", "UNIT-FIXTURE", "--run-name", "fixture",
                "--next-owner", "c-coordinator"]
        order = []
        def checked(_):
            order.append("first-preflight")
        def observed(args, *, started):
            self.assertEqual(order, ["first-preflight"])
            self.assertEqual(started, 123.0)
            return 17
        with patch.object(observer.sys, "argv", argv), \
             patch.object(observer.time, "monotonic", return_value=123.0), \
             patch.object(observer, "preflight", side_effect=checked), \
             patch.object(observer, "run", side_effect=observed):
            self.assertEqual(observer.main(), 17)


if __name__ == "__main__":
    unittest.main(verbosity=2)
