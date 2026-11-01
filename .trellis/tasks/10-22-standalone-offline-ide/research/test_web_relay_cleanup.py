"""Pure fake-Job cleanup tests. Never call run, create a Job, or launch processes."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "relay_cleanup_subject", ROOT / "run-web-relay-window.py")
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)


class FakeJob:
    """Model only the OwnedJob empty/stop/close contract, with synthetic handles."""

    def __init__(self, states, *, pid=101, stop_error=None, close_error=None):
        self.job = 1001
        self.process = 2001
        self.record = {"pid": pid, "creationFiletime100ns": "123456789"}
        self.states = iter(states)
        self.last_state = False
        self.stop_error = stop_error
        self.close_error = close_error
        self.stop_calls = 0
        self.close_calls = 0
        self.empty_calls = 0

    def empty(self):
        self.empty_calls += 1
        try:
            result = next(self.states)
        except StopIteration:
            result = self.last_state
        if isinstance(result, BaseException):
            raise result
        self.last_state = result
        self.record.update(terminal=result, jobActiveProcesses=0 if result else 1)
        if result:
            self.record["exitCode"] = 124 if self.stop_calls else 0
        return result

    def stop(self):
        self.stop_calls += 1
        if self.stop_error:
            raise self.stop_error

    def close(self):
        self.close_calls += 1
        if self.close_error:
            raise self.close_error


class WrapperCleanupTests(unittest.TestCase):
    def clean(self, job, *, deadline=0, phases=None, state=None):
        held = [job]
        errors = []
        state = {"stopped": False, "jobs": []} if state is None else state
        phases = [] if phases is None else phases
        with patch.object(wrapper.time, "monotonic", return_value=1), \
             patch.object(wrapper.time, "sleep") as sleep:
            confirmed = wrapper.wrapper_cleanup(
                held, deadline, errors.append, state, phases)
        return confirmed, held, errors, state, sleep

    def test_empty_list_needs_no_job_or_clock(self):
        state = {"stopped": False}
        with patch.object(wrapper.time, "monotonic", side_effect=AssertionError), \
             patch.object(wrapper.time, "sleep", side_effect=AssertionError):
            self.assertTrue(wrapper.wrapper_cleanup([], 0, self.fail, state))
        self.assertEqual(state, {"stopped": False, "jobs": []})

    def test_already_empty_closes_without_force_or_sleep(self):
        job = FakeJob([True])
        confirmed, held, errors, state, sleep = self.clean(job)
        self.assertTrue(confirmed)
        self.assertEqual((held, errors), ([], []))
        self.assertEqual((job.stop_calls, job.close_calls), (0, 1))
        self.assertFalse(state["stopped"])
        self.assertTrue(state["jobs"][0]["handlesClosed"])
        sleep.assert_not_called()

    def test_forced_stop_then_empty_preserves_identity_before_close(self):
        job = FakeJob([False, True])
        phase = {"name": "supervisor", "root": {"pid": 101},
                 "terminalConfirmed": False}
        confirmed, held, errors, state, _ = self.clean(job, phases=[phase])
        self.assertTrue(confirmed)
        self.assertEqual((held, errors), ([], []))
        self.assertTrue(state["stopped"])
        self.assertEqual((job.stop_calls, job.close_calls), (1, 1))
        entry = state["jobs"][0]
        self.assertEqual((entry["jobHandle"], entry["processHandle"]), ("1001", "2001"))
        self.assertEqual(entry["root"]["creationFiletime100ns"], "123456789")
        self.assertEqual(entry["phase"], "supervisor")
        self.assertTrue(phase["terminalConfirmed"])
        self.assertEqual(phase["root"]["exitCode"], 124)
        self.assertTrue(wrapper.released_resources(
            cleanup_confirmed=confirmed, held=held, phases=[phase]))

    def test_active_at_deadline_retains_exact_job_and_handles(self):
        job = FakeJob([False])
        phase = {"name": "relay", "root": {"pid": 101}}
        confirmed, held, errors, state, sleep = self.clean(job, phases=[phase])
        self.assertFalse(confirmed)
        self.assertIs(held[0], job)
        self.assertEqual(job.close_calls, 0)
        self.assertEqual(job.stop_calls, 1)
        self.assertIn("handles retained", errors[0])
        self.assertFalse(state["jobs"][0]["handlesClosed"])
        self.assertFalse(phase["terminalConfirmed"])
        self.assertEqual(phase["root"]["jobActiveProcesses"], 1)
        self.assertEqual(wrapper.ownership_state(resources_released=
            wrapper.released_resources(cleanup_confirmed=confirmed,
                                       held=held, phases=[phase])), "HOLD")
        sleep.assert_not_called()

    def test_polling_eventually_observes_empty(self):
        job = FakeJob([False, False, True])
        held, errors = [job], []
        state = {"stopped": False, "jobs": []}
        with patch.object(wrapper.time, "monotonic", side_effect=[0, 2]), \
             patch.object(wrapper.time, "sleep") as sleep:
            confirmed = wrapper.wrapper_cleanup(held, 1, errors.append, state)
        self.assertTrue(confirmed)
        self.assertEqual(held, [])
        sleep.assert_called_once_with(wrapper.POLL_SECONDS)

    def test_empty_query_error_retains_handle_and_records_identity(self):
        job = FakeJob([OSError("query failed")])
        confirmed, held, errors, state, _ = self.clean(job)
        self.assertFalse(confirmed)
        self.assertIs(held[0], job)
        self.assertEqual((job.stop_calls, job.close_calls), (0, 0))
        self.assertEqual(state["jobs"][0]["root"]["pid"], 101)
        self.assertIn("query failed", errors[0])

    def test_stop_error_retains_handle_and_marks_force_attempt(self):
        job = FakeJob([False], stop_error=OSError("stop failed"))
        confirmed, held, errors, state, _ = self.clean(job)
        self.assertFalse(confirmed)
        self.assertIs(held[0], job)
        self.assertTrue(state["stopped"])
        self.assertEqual(job.close_calls, 0)
        self.assertIn("stop failed", errors[0])

    def test_close_error_does_not_drop_confirmed_empty_job(self):
        job = FakeJob([True], close_error=OSError("close failed"))
        confirmed, held, errors, state, _ = self.clean(job)
        self.assertFalse(confirmed)
        self.assertIs(held[0], job)
        self.assertFalse(state["jobs"][0]["handlesClosed"])
        self.assertTrue(state["jobs"][0]["terminalAndEmpty"])
        self.assertIn("close failed", errors[0])

    def test_second_empty_query_error_keeps_stopped_job(self):
        job = FakeJob([False, OSError("post-stop query failed")])
        confirmed, held, errors, state, _ = self.clean(job)
        self.assertFalse(confirmed)
        self.assertIs(held[0], job)
        self.assertTrue(state["stopped"])
        self.assertEqual(job.close_calls, 0)
        self.assertIn("post-stop query failed", errors[0])

    def test_one_failure_does_not_skip_other_owned_job(self):
        blocked, clean = FakeJob([False], pid=101), FakeJob([True], pid=202)
        held, errors = [blocked, clean], []
        state = {"stopped": False, "jobs": []}
        with patch.object(wrapper.time, "monotonic", return_value=1), \
             patch.object(wrapper.time, "sleep"):
            confirmed = wrapper.wrapper_cleanup(held, 0, errors.append, state)
        self.assertFalse(confirmed)
        self.assertEqual(held, [blocked])
        self.assertEqual(clean.close_calls, 1)
        self.assertEqual(len(state["jobs"]), 2)

    def test_unmatched_phase_is_preserved(self):
        job = FakeJob([True])
        phase = {"name": "accept", "root": {"pid": 999}, "terminalConfirmed": False}
        confirmed, _, _, state, _ = self.clean(job, phases=[phase])
        self.assertTrue(confirmed)
        self.assertEqual(phase["root"], {"pid": 999})
        self.assertFalse(phase["terminalConfirmed"])
        self.assertEqual(state["jobs"][0]["phase"], "unassigned-before-root")

    def test_record_is_snapshot_not_alias_to_mutable_job(self):
        job = FakeJob([True])
        phase = {"name": "supervisor", "root": {"pid": 101}}
        _, _, _, state, _ = self.clean(job, phases=[phase])
        job.record["pid"] = 999
        self.assertEqual(state["jobs"][0]["root"]["pid"], 101)
        self.assertEqual(phase["root"]["pid"], 101)

    def test_later_cleanup_can_confirm_previously_held_job(self):
        job = FakeJob([False, False, True])
        held, errors = [job], []
        state = {"stopped": False, "jobs": []}
        with patch.object(wrapper.time, "monotonic", return_value=1), \
             patch.object(wrapper.time, "sleep"):
            self.assertFalse(wrapper.wrapper_cleanup(held, 0, errors.append, state))
            self.assertTrue(wrapper.wrapper_cleanup(held, 0, errors.append, state))
        self.assertEqual(held, [])
        self.assertEqual(len(state["jobs"]), 2)
        self.assertFalse(state["jobs"][0]["handlesClosed"])
        self.assertTrue(state["jobs"][1]["handlesClosed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
