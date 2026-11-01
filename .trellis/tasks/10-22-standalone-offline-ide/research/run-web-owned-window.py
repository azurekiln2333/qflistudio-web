"""Bound the existing focused worker with an owned Windows Job, then hand off."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[4]
RESEARCH = Path(__file__).resolve().parent
CHANNEL = "qfli-core-release-sync"

# Windows Job primitive copied from Note425 helper SHA256
# 4211215945697d48e105eb19faa2e1c349a37689065ffe9f44350bb6ed532d8b.
class Limits(C.Structure):
    _fields_ = [("processTime", C.c_longlong), ("jobTime", C.c_longlong), ("flags", W.DWORD),
                ("minWs", C.c_size_t), ("maxWs", C.c_size_t), ("activeLimit", W.DWORD),
                ("affinity", C.c_size_t), ("priority", W.DWORD), ("scheduling", W.DWORD)]


class ExtendedLimits(C.Structure):
    _fields_ = [("basic", Limits), ("io", C.c_ulonglong * 6),
                ("processMemory", C.c_size_t), ("jobMemory", C.c_size_t),
                ("peakProcess", C.c_size_t), ("peakJob", C.c_size_t)]


class Accounting(C.Structure):
    _fields_ = [("times", C.c_longlong * 4), ("faults", W.DWORD),
                ("total", W.DWORD), ("active", W.DWORD), ("terminated", W.DWORD)]


class OwnedJob:
    """Assign while suspended: every descendant stays in this private job."""
    def __init__(self):
        self.k = C.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([C.c_void_p, W.LPCWSTR], W.HANDLE),
            "SetInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
            "QueryInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p], W.BOOL),
            "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
            "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
            "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
            "ResumeThread": ([W.HANDLE], W.DWORD), "CloseHandle": ([W.HANDLE], W.BOOL),
            "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
            "GetExitCodeProcess": ([W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
            "GetProcessId": ([W.HANDLE], W.DWORD),
            "GetProcessTimes": ([W.HANDLE] + [C.POINTER(W.FILETIME)] * 4, W.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.k, name)
            function.argtypes, function.restype = args, result
        self.job, self.process, self.record = self.k.CreateJobObjectW(None, None), None, {}
        if not self.job:
            raise C.WinError(C.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        self.check(self.k.SetInformationJobObject(self.job, 9, C.byref(limits), C.sizeof(limits)))

    @staticmethod
    def check(value):
        if not value:
            raise C.WinError(C.get_last_error())

    def start(self, command, directory, env, stdout, stderr):
        import _winapi
        import msvcrt
        with open(os.devnull, "rb") as null:
            handles = [msvcrt.get_osfhandle(f.fileno()) for f in (null, stdout, stderr)]
            previous = [os.get_handle_inheritable(h) for h in handles]
            try:
                for handle in handles:
                    os.set_handle_inheritable(handle, True)
                startup = subprocess.STARTUPINFO()
                startup.dwFlags = subprocess.STARTF_USESTDHANDLES
                startup.hStdInput, startup.hStdOutput, startup.hStdError = handles
                startup.lpAttributeList = {"handle_list": list(dict.fromkeys(handles))}
                hp, ht, pid, tid = _winapi.CreateProcess(None, subprocess.list2cmdline(command),
                    None, None, True, 0x4 | 0x08000000, env, str(directory), startup)
                self.process = hp
                self.record = {"pid": pid, "threadId": tid, "createdSuspended": True,
                               "assignedBeforeResume": False, "terminal": False}
                try:
                    stamps = [W.FILETIME() for _ in range(4)]
                    self.check(self.k.GetProcessTimes(hp, *(C.byref(s) for s in stamps)))
                    self.record["creationFiletime100ns"] = str((stamps[0].dwHighDateTime << 32) | stamps[0].dwLowDateTime)
                    if self.k.GetProcessId(hp) != pid:
                        raise RuntimeError("Exact owned process handle identity mismatch")
                    self.check(self.k.AssignProcessToJobObject(self.job, hp))
                    self.record["assignedBeforeResume"] = True
                    if self.k.ResumeThread(ht) != 1:
                        raise RuntimeError("Suspended root did not resume from its single suspension")
                finally:
                    self.k.CloseHandle(ht)
            finally:
                for handle, inherit in zip(handles, previous):
                    os.set_handle_inheritable(handle, inherit)

    def empty(self):
        info = Accounting()
        self.check(self.k.QueryInformationJobObject(self.job, 1, C.byref(info), C.sizeof(info), None))
        self.record["jobActiveProcesses"] = int(info.active)
        terminal = self.process is None or self.k.WaitForSingleObject(self.process, 0) == 0
        self.record["terminal"] = terminal
        if terminal and self.process:
            code = W.DWORD()
            self.check(self.k.GetExitCodeProcess(self.process, C.byref(code)))
            self.record["exitCode"] = int(code.value)
        return terminal and info.active == 0

    def stop(self):
        self.check(self.k.TerminateJobObject(self.job, 124))
        if self.process and not self.record.get("assignedBeforeResume"):
            self.check(self.k.TerminateProcess(self.process, 124))  # Own never-resumed root only.

    def close(self):
        if self.process:
            self.k.CloseHandle(self.process)
        self.k.CloseHandle(self.job)


def channel_command(message, next_owner):
    shim = shutil.which("trellis.cmd") or shutil.which("trellis.ps1")
    if not shim:
        raise FileNotFoundError("Installed Trellis shim missing")
    entry = Path(shim).parent / "node_modules/@mindfoldhq/trellis/bin/trellis.js"
    node = shutil.which("node.exe")
    if not entry.is_file() or not node:
        raise FileNotFoundError("Installed Trellis node/CLI entry missing")
    return [node, str(entry), "channel", "send", CHANNEL, "--scope", "global", "--as",
            "web-offline-1022", "--to", next_owner, "--text-file", str(message)]



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grant', required=True)
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--next-owner', required=True)
    args = parser.parse_args()
    if (not args.grant.strip() or not re.fullmatch(r'[a-zA-Z0-9_-]+', args.run_name)
            or not re.fullmatch(r'[a-z][a-z0-9_-]+', args.next_owner)):
        raise ValueError('Explicit grant, valid evidence name and one next owner required')
    report_path = RESEARCH / f'{args.run_name}-job.json'
    for suffix in ('job.json', 'runner.log', 'runner-errors.log', 'result.json',
                   'format.log', 'tests.log', 'analysis.log', 'source-before.json',
                   'source-after.json', 'release.txt', 'channel.log'):
        existing = RESEARCH / f'{args.run_name}-{suffix}'
        if existing.exists():
            raise FileExistsError(existing)
    report = {'grant': args.grant, 'nextOwner': args.next_owner,
              'startedUtc': datetime.now(timezone.utc).isoformat(), 'errors': []}
    command = [shutil.which('powershell.exe'), '-NoLogo', '-NoProfile',
               '-ExecutionPolicy', 'Bypass', '-File',
               str(RESEARCH / 'run-web-focused-window.ps1'), '-NextOwner', args.next_owner,
               '-RunName', args.run_name, '-Worker']
    started = time.monotonic()
    job = None
    terminal = False
    try:
        job = OwnedJob()
        with (RESEARCH / f'{args.run_name}-runner.log').open('xb', buffering=0) as out, \
             (RESEARCH / f'{args.run_name}-runner-errors.log').open('xb', buffering=0) as err:
            job.start(command, ROOT, os.environ.copy(), out, err)
            print(json.dumps({'root': job.record, 'report': str(report_path)}), flush=True)
            while time.monotonic() - started < 96 and not job.empty():
                time.sleep(0.1)
            report['deadlineReached'] = not job.empty()
    except BaseException as exc:
        report['errors'].append(f'{type(exc).__name__}: {exc}')
    finally:
        try:
            if job is not None and not job.empty():
                job.stop()
                while time.monotonic() - started < 104 and not job.empty():
                    time.sleep(0.05)
            terminal = job is None or job.empty()
        except BaseException as exc:
            report['errors'].append(f'Cleanup: {type(exc).__name__}: {exc}')
        report.update(root=job.record if job is not None else {}, terminalConfirmed=terminal,
                      status='RELEASE' if terminal else 'HOLD/UNRELEASED',
                      elapsedSeconds=round(time.monotonic() - started, 3))
        result_path = RESEARCH / f'{args.run_name}-result.json'
        if result_path.exists():
            try:
                report['worker'] = json.loads(result_path.read_text(encoding='utf-8-sig'))
            except (ValueError, OSError) as exc:
                report['errors'].append(f'Worker result: {type(exc).__name__}: {exc}')
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        message_path = RESEARCH / f'{args.run_name}-release.txt'
        message_path.write_text(
            f"Web {report['status']} -> {args.next_owner}; grant {args.grant}. "
            f"Exact owned root/job {json.dumps(report['root'])}; empty job confirmed={terminal}. "
            f"Worker results {json.dumps(report.get('worker'))}; elapsed={report['elapsedSeconds']}s. "
            f"Evidence research/{args.run_name}-*. No native/HAP/device/core write.\n", encoding='utf-8')
        publisher = None
        try:
            publish_command = channel_command(message_path, args.next_owner)
            publisher = OwnedJob()
            with (RESEARCH / f'{args.run_name}-channel.log').open('xb', buffering=0) as log:
                publisher.start(publish_command, ROOT, os.environ.copy(), log, log)
                publish_deadline = min(started + 109, time.monotonic() + 4)
                while time.monotonic() < publish_deadline and not publisher.empty():
                    time.sleep(0.05)
                if not publisher.empty():
                    publisher.stop()
                    while time.monotonic() - started < 110 and not publisher.empty():
                        time.sleep(0.02)
                report['publication'] = {'root': publisher.record, 'terminal': publisher.empty()}
                report['publication']['delivered'] = (
                    report['publication']['terminal'] and publisher.record.get('exitCode') == 0)
                if not report['publication']['delivered']:
                    report['errors'].append('Channel publication failed; manual relay required')
        except BaseException as exc:
            report['errors'].append(f'Publication: {type(exc).__name__}: {exc}')
        finally:
            if publisher is not None:
                publisher.close()
            if job is not None:
                job.close()
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report), flush=True)
    return 0 if (terminal and report['root'].get('exitCode') == 0 and not report['errors']
                 and report.get('publication', {}).get('delivered') is True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
