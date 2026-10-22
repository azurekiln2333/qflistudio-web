#!/usr/bin/env python3
"""Host regression checks for device-driver gates; these are not OHOS passes."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import run_ohos_catalog as driver


def fixture_catalog() -> dict[str, bytes]:
    examples = {"schemaVersion": 1, "entries": [{"id": "html-example-001", "code": "<!doctype html><p>fixture</p>"}]}
    files = {"examples.json": json.dumps(examples).encode(), "tutorials.json": b'{"schemaVersion":1,"entries":[]}'}
    manifest = {"schemaVersion": 1, "kind": "qfli-ohos-catalog", "counts": {"examples": 1, "tutorials": 0, "lessons": 1},
                "files": {kind: {"path": f"ohos_catalog/{kind}.json", "bytes": len(files[kind + ".json"]),
                                  "sha256": driver.sha(files[kind + ".json"])} for kind in ("examples", "tutorials")}}
    return {**files, "manifest.json": json.dumps(manifest).encode()}


def fixture_archive(path: Path, kind: str, files: dict[str, bytes], *, stale=False, singleton=True, leak=False,
                    emulator=False, missing_library=None, machine=62) -> None:
    module, ability, module_type = (("entry", "EntryAbility", "entry") if kind == "production" else
                                   ("entry_test", "TestAbility", "feature"))
    metadata = {"app": {"bundleName": driver.BUNDLE, "versionCode": 1, "versionName": "1.0"},
                "module": {"name": module, "type": module_type, "mainElement": ability,
                           "abilities": [{"name": ability, "exported": True,
                                          "launchType": "singleton" if singleton else "standard"}]}}
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("module.json", json.dumps(metadata))
        archive.writestr("ets/modules.abc", b"CatalogHarness qfliCatalogStop" if kind == "test" else b"production bytecode")
        for name in ("examples.json", "tutorials.json"):
            prefix = "ohos_catalog/" if kind == "test" else "flutter_assets/assets/content/"
            archive.writestr("resources/rawfile/" + prefix + name, files[name] + (b" " if stale else b""))
        if kind == "test" or leak:
            archive.writestr("resources/rawfile/ohos_catalog/manifest.json", files["manifest.json"])
        archive.writestr("libs/arm64-v8a/libqfli_nginx_napi.so", b"fixture, not a native executable")
        if kind == "production" and emulator:
            # Header-only host fixtures exercise the driver's ELF identity gate;
            # they are not working native libraries or device-runtime evidence.
            header = bytearray(64)
            header[:6] = b"\x7fELF\x02\x01"
            header[18:20] = machine.to_bytes(2, "little")
            for library in driver.EMULATOR_LIBRARIES:
                if library != missing_library:
                    archive.writestr(f"libs/x86_64/{library}", bytes(header))


def fixture_report(files: dict[str, bytes]) -> dict:
    code = json.loads(files["examples.json"])["entries"][0]["code"]
    return {"runtime": "ohos-arkweb", "device": {"runId": "test-session", "manifest": json.loads(files["manifest.json"]),
            "environment": {"bundleName": driver.BUNDLE, "moduleName": "entry_test", "abilityName": "TestAbility",
                            "osFullName": "OpenHarmony-fixture", "sdkApiVersion": 24, "deviceType": "phone"}},
            "browserVersion": "fixture", "catalog": {"complete": True, "executedExamples": 1, "totalExamples": 1,
            "totalLessons": 1, **{kind + "Sha256": driver.sha(files[kind + ".json"]) for kind in ("examples", "tutorials")}},
            "passed": 1, "failed": 0, "mappingIssues": [], "totalChecks": 1,
            "results": [{"id": "html-example-001", "pass": True, "codeSha256": driver.sha(code.encode()),
                         "checks": 1, "assertions": [{"name": "fixture-only", "ok": True}]}]}


class DriverGatesTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="qfli-driver-tests-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.files = fixture_catalog()

    def emulator_attempt(self, *, model="emulator", architecture="x86_64", explicit=True,
                         missing_library=None, machine=62, stale=False, changed_model=None,
                         semantic_failure=False):
        stage = self.root / "emulator-stage"
        stage.mkdir(exist_ok=True)
        for name, payload in self.files.items():
            (stage / name).write_bytes(payload)
        production, test = self.root / "production.hap", self.root / "test.hap"
        fixture_archive(production, "production", self.files, emulator=True, missing_library=missing_library,
                        machine=machine, stale=stale)
        fixture_archive(test, "test", self.files)
        sign_tool = self.root / "sign.jar"
        sign_tool.write_bytes(b"fixture")
        report = self.root / "emulator.md"
        calls = []
        model_reads = 0
        forwarded = False

        class FakeDevice:
            def __init__(self, executable, target):
                pass

            def require_live(self):
                calls.append(("require-live",))

            def call(self, *arguments):
                nonlocal model_reads, forwarded
                calls.append(arguments)
                if arguments == ("shell", "param", "get", driver.EMULATOR_MODEL_PARAMETER):
                    model_reads += 1
                    return changed_model if model_reads > 1 and changed_model is not None else model
                if arguments == ("shell", "uname", "-m"):
                    return architecture
                if arguments[:3] == ("shell", "param", "get"):
                    return dict(zip(driver.PARAMETERS, ("OpenHarmony-fixture", "24", "phone")))[arguments[3]]
                if arguments[0] == "install":
                    return "install bundle successfully"
                if arguments[:3] == ("shell", "aa", "start"):
                    return "start ability successfully."
                if arguments == ("fport", "ls"):
                    return "tcp:9222 tcp:9222" if forwarded else ""
                if arguments == ("fport", "tcp:9222", "tcp:9222"):
                    forwarded = True
                    return "Forwardport result:OK"
                if arguments == ("fport", "rm", "tcp:9222", "tcp:9222"):
                    forwarded = False
                    return "Remove forward ruler success"
                if arguments[:2] == ("fport", "rm"):
                    raise ValueError("HDC forward removal requires separate local and remote arguments")
                raise ValueError(f"unexpected fixture device call: {arguments}")

        def semantic_run(*arguments, **options):
            value = fixture_report(self.files)
            if semantic_failure:
                value["runtime"] = "host-chromium"
            report.with_suffix(".json").write_text(json.dumps(value), encoding="utf-8")
            return subprocess.CompletedProcess(arguments[0], 0)

        arguments = ["driver", "--device", "chosen", "--production-hap", str(production),
                     "--test-hap", str(test), "--run", "--report", str(report),
                     "--hdc", "hdc", "--java", "java", "--node", "node"]
        if explicit:
            arguments.append("--unsigned-emulator")
        with patch.object(sys, "argv", arguments), patch.object(driver, "Device", FakeDevice), \
                patch.object(driver, "OUTPUT", stage), patch.object(driver, "staged_files", return_value=self.files), \
                patch.object(driver, "find_sign_tool", return_value=sign_tool) as find_sign, \
                patch.object(driver, "verify_signature", side_effect=ValueError("unsigned fixture rejected")) as verify, \
                patch.object(driver, "wait_for_bootstrap"), patch.object(driver.socket, "socket"), \
                patch.object(driver.subprocess, "run", side_effect=semantic_run):
            status = driver.main()
        evidence = json.loads(report.with_suffix(".device.json").read_text(encoding="utf-8"))
        return status, evidence, calls, find_sign, verify

    def test_unsigned_emulator_requires_actual_model_and_x86_64(self):
        for model, architecture in (("phone", "x86_64"), ("", "x86_64"), ("emulator", "aarch64"),
                                    ("emulator", "x86"), ("emulator", "")):
            with self.subTest(model=model, architecture=architecture):
                status, evidence, calls, find_sign, verify = self.emulator_attempt(
                    model=model, architecture=architecture)
                self.assertEqual(status, 1)
                self.assertIn("actual model emulator and uname -m x86_64", evidence["error"])
                self.assertFalse(any(call[0] in ("install", "fport") or "aa" in call for call in calls))
                self.assertEqual(evidence["cleanup"], [])
                find_sign.assert_not_called()
                verify.assert_not_called()

    def test_unsigned_artifacts_without_explicit_flag_keep_official_signature_gate(self):
        status, evidence, calls, find_sign, verify = self.emulator_attempt(explicit=False)
        self.assertEqual(status, 1)
        self.assertEqual(evidence["signingMode"], "official-signature")
        self.assertIn("unsigned fixture rejected", evidence["error"])
        self.assertNotIn("emulatorIdentity", evidence)
        self.assertFalse(any(call[0] == "install" for call in calls))
        find_sign.assert_called_once()
        verify.assert_called_once()

    def test_unsigned_emulator_requires_all_four_actual_x86_64_runtime_members(self):
        for missing in driver.EMULATOR_LIBRARIES:
            with self.subTest(missing=missing):
                status, evidence, calls, _, _ = self.emulator_attempt(missing_library=missing)
                self.assertEqual(status, 1)
                self.assertIn(f"requires packaged x86_64 {missing}", evidence["error"])
                self.assertFalse(any(call[0] == "install" for call in calls))
        status, evidence, calls, _, _ = self.emulator_attempt(machine=183)
        self.assertEqual(status, 1)
        self.assertIn("not the inspected little-endian ELF64 x86_64 runtime", evidence["error"])
        self.assertFalse(any(call[0] == "install" for call in calls))

    def test_explicit_unsigned_emulator_runs_guarded_path_without_claiming_signed_proof(self):
        status, evidence, calls, find_sign, verify = self.emulator_attempt()
        self.assertEqual(status, 0)
        self.assertEqual(evidence["status"], "passed")
        self.assertEqual(evidence["signingMode"], "unsigned-emulator")
        self.assertEqual(evidence["emulatorIdentity"], {"model": "emulator", "architecture": "x86_64"})
        self.assertEqual(len([call for call in calls if call == ("require-live",)]), 2)
        self.assertEqual(len([call for call in calls if call == ("shell", "uname", "-m")]), 2)
        installed = [call for call in calls if call[0] == "install"]
        self.assertEqual(installed, [("install", "-r", str(self.root / "production.hap"), str(self.root / "test.hap"))])
        for artifact in evidence["artifacts"].values():
            self.assertIs(artifact["signature"]["verified"], False)
            self.assertEqual(artifact["signature"]["verification"], "not-performed")
            self.assertNotIn("certificateChainSha256", artifact["signature"])
        self.assertEqual(len(evidence["artifacts"]["production"]["emulatorRuntime"]["libraries"]), 4)
        self.assertEqual(evidence["semantic"]["passed"], 1)
        self.assertEqual(evidence["cleanup"], ["owned HDC forward removed", "targeted test ability stop requested"])
        self.assertFalse(any("force-stop" in call or "setenforce" in call for call in calls))
        find_sign.assert_not_called()
        verify.assert_not_called()

    def test_unsigned_emulator_rechecks_identity_before_ordinary_install(self):
        status, evidence, calls, _, _ = self.emulator_attempt(changed_model="phone")
        self.assertEqual(status, 1)
        self.assertIn("actual model emulator and uname -m x86_64", evidence["error"])
        self.assertFalse(any(call[0] == "install" for call in calls))
        self.assertEqual(evidence["cleanup"], [])

    def test_forward_cleanup_passes_local_remote_separately_on_success_and_semantic_failure(self):
        for semantic_failure in (False, True):
            with self.subTest(semantic_failure=semantic_failure):
                status, evidence, calls, _, _ = self.emulator_attempt(semantic_failure=semantic_failure)
                self.assertEqual(status, 1 if semantic_failure else 0)
                removals = [call for call in calls if call[:2] == ("fport", "rm")]
                self.assertEqual(removals, [("fport", "rm", "tcp:9222", "tcp:9222")])
                self.assertEqual(evidence["cleanup"], ["owned HDC forward removed",
                                                     "targeted test ability stop requested"])

    def test_unsigned_emulator_preserves_archive_semantic_and_cleanup_gates(self):
        status, evidence, calls, _, _ = self.emulator_attempt(stale=True)
        self.assertEqual(status, 1)
        self.assertIn("differs from current source/staging", evidence["error"])
        self.assertFalse(any(call[0] == "install" for call in calls))
        status, evidence, calls, _, _ = self.emulator_attempt(semantic_failure=True)
        self.assertEqual(status, 1)
        self.assertIn("another catalog/runtime", evidence["error"])
        self.assertEqual(evidence["cleanup"], ["owned HDC forward removed", "targeted test ability stop requested"])
        self.assertEqual(len([call for call in calls if "qfliCatalogStop" in call]), 1)

    def test_live_target_requires_exact_match_and_rejects_empty_marker(self):
        for requested, listed, accepted in (("chosen", "chosen\nother", True), ("chosen", "other", False),
                                             ("[Empty]", "[Empty]", False), ("", "[Empty]", False)):
            with self.subTest(requested=requested, listed=listed), patch.object(driver, "execute", return_value=
                    subprocess.CompletedProcess([], 0, listed, "")) as execute:
                if accepted:
                    driver.Device("hdc", requested).require_live()
                else:
                    with self.assertRaises(ValueError):
                        driver.Device("hdc", requested).require_live()
                self.assertEqual(execute.call_args.args[0], ["hdc", "list", "targets"])

    def test_empty_device_cli_performs_no_install_launch_forward_or_archive_read(self):
        report = self.root / "empty.md"
        arguments = ["driver", "--device", "chosen", "--production-hap", "missing.hap", "--test-hap", "missing-test.hap",
                     "--run", "--report", str(report), "--hdc", "hdc", "--java", "java", "--node", "node"]
        for mode in ([], ["--unsigned-emulator"]):
            with self.subTest(mode=mode), patch.object(sys, "argv", arguments + mode), \
                    patch.object(driver, "execute", return_value=
                                 subprocess.CompletedProcess([], 0, "[Empty]", "")) as execute, \
                    patch.object(driver, "inspect_archive") as inspect:
                self.assertEqual(driver.main(), 1)
                self.assertEqual(execute.call_count, 1)
                inspect.assert_not_called()
            evidence = json.loads(report.with_suffix(".device.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "failed")
            self.assertEqual(evidence["cleanup"], [])
            self.assertNotIn("chosen", json.dumps(evidence))

    def test_zero_exit_signature_failure_is_rejected(self):
        with patch.object(driver, "execute", return_value=subprocess.CompletedProcess([], 0, "verify-app failed", "")):
            with self.assertRaisesRegex(ValueError, "verify-app did not verify"):
                driver.verify_signature(self.root / "unsigned.hap", self.root / "tool.jar", "java")

    def test_verified_profile_bundle_and_public_evidence(self):
        for bundle in (driver.BUNDLE, "wrong.bundle"):
            def verify(arguments, timeout):
                operation = arguments[3]
                if operation == "verify-app":
                    Path(arguments[arguments.index("-outCertChain") + 1]).write_bytes(b"public cert chain")
                    Path(arguments[arguments.index("-outProfile") + 1]).write_bytes(b"signed profile fixture")
                else:
                    content = {"bundle-info": {"bundle-name": bundle}, "type": "debug",
                               "validity": {"not-before": 0, "not-after": 9999999999},
                               "debug-info": {"device-ids": ["private-identifier-must-not-escape"]}}
                    Path(arguments[arguments.index("-outFile") + 1]).write_text(json.dumps(
                        {"verifiedPassed": True, "content": content}), encoding="utf-8")
                return subprocess.CompletedProcess([], 0, operation + " success", "")
            with self.subTest(bundle=bundle), patch.object(driver, "execute", side_effect=verify):
                if bundle == driver.BUNDLE:
                    result = driver.verify_signature(self.root / "signed.hap", self.root / "tool.jar", "java")
                    self.assertTrue(result["verified"])
                    self.assertNotIn("private-identifier", json.dumps(result))
                else:
                    with self.assertRaisesRegex(ValueError, "not bound"):
                        driver.verify_signature(self.root / "signed.hap", self.root / "tool.jar", "java")

    def test_archive_rejects_stale_catalog_nonsingleton_test_and_production_leak(self):
        for kind, options, accepted in (("test", {}, True), ("production", {}, True),
                                       ("test", {"stale": True}, False), ("production", {"stale": True}, False),
                                       ("test", {"singleton": False}, False), ("production", {"leak": True}, False)):
            with self.subTest(kind=kind, options=options):
                path = self.root / "fixture.hap"
                fixture_archive(path, kind, self.files, **options)
                if accepted:
                    self.assertEqual(driver.inspect_archive(path, kind, self.files)["bundleName"], driver.BUNDLE)
                else:
                    with self.assertRaises(ValueError):
                        driver.inspect_archive(path, kind, self.files)

    def test_report_requires_complete_native_per_entry_source_and_assertions(self):
        valid = fixture_report(self.files)
        path = self.root / "semantic.json"
        parameters = dict(zip(driver.PARAMETERS, ("OpenHarmony-fixture", "24", "phone")))
        path.write_text(json.dumps(valid), encoding="utf-8")
        self.assertEqual(driver.validate_report(path, self.files, parameters)["passed"], 1)
        mutations = (
            lambda value: value.update(runtime="host-chromium"),
            lambda value: value["catalog"].update(complete=False),
            lambda value: value.update(failed=1),
            lambda value: value["results"][0].update(id="unexecuted-example"),
            lambda value: value["results"][0].update(codeSha256="0" * 64),
            lambda value: value["results"][0].update(checks=0, assertions=[]),
            lambda value: value["results"][0]["assertions"][0].update(ok=False),
            lambda value: value["device"].update(environment={}),
            lambda value: value["device"]["environment"].update(sdkApiVersion=20),
            lambda value: value.update(totalChecks=999),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                changed = deepcopy(valid)
                mutate(changed)
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaises(ValueError):
                    driver.validate_report(path, self.files, parameters)

    def test_failure_after_launch_targets_stop_without_force_stopping_bundle(self):
        stage = self.root / "stage"
        stage.mkdir()
        for name, payload in self.files.items():
            (stage / name).write_bytes(payload)
        for kind in ("production", "test"):
            fixture_archive(self.root / (kind + ".hap"), kind, self.files)
        sign_tool = self.root / "sign.jar"
        sign_tool.write_bytes(b"fixture")
        calls = []

        class FakeDevice:
            def __init__(self, executable, target):
                pass

            def require_live(self):
                calls.append(("require-live",))

            def call(self, *arguments):
                calls.append(arguments)
                if arguments[:3] == ("shell", "param", "get"):
                    return dict(zip(driver.PARAMETERS, ("OpenHarmony-fixture", "24", "phone")))[arguments[3]]
                if arguments[0] == "install":
                    return "install bundle successfully"
                if arguments[:3] == ("shell", "aa", "start"):
                    return "start ability successfully."
                if arguments == ("fport", "ls"):
                    return ""
                raise ValueError("injected forwarding failure after test-ability launch")

        report = self.root / "cleanup.md"
        arguments = ["driver", "--device", "chosen", "--production-hap", str(self.root / "production.hap"),
                     "--test-hap", str(self.root / "test.hap"), "--run", "--report", str(report),
                     "--hdc", "hdc", "--java", "java", "--node", "node"]
        with patch.object(sys, "argv", arguments), patch.object(driver, "Device", FakeDevice), \
                patch.object(driver, "OUTPUT", stage), patch.object(driver, "staged_files", return_value=self.files), \
                patch.object(driver, "find_sign_tool", return_value=sign_tool), \
                patch.object(driver.socket, "socket"), \
                patch.object(driver, "verify_signature", return_value={"certificateChainSha256": "same-fixture-signer"}):
            self.assertEqual(driver.main(), 1)
        stops = [call for call in calls if "qfliCatalogStop" in call]
        self.assertEqual(len(stops), 1)
        self.assertFalse(any("force-stop" in call for call in calls))
        evidence = json.loads(report.with_suffix(".device.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["cleanup"], ["targeted test ability stop requested"])
        self.assertEqual(evidence["status"], "failed")


if __name__ == "__main__":
    unittest.main()
