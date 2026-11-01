"""Report the OHOS local-dependency resolution gap. Never start OHPM.

This supervisor has no execution path. It cannot prove that OHPM resolves the
declared local dependency without registry access, so it refuses to run OHPM at
all. The precondition is missing, not tested: the declared
`libqfli_web_cdp_transport.so` is absent from the generated resolution surfaces,
so the source graph is incomplete before any tool runs.

Modes:
* `--snapshot-only` reads and hashes the local resolution surfaces. No grant, no
  process, no file write.
* `--grant <id> --run-name <fresh>` writes one refusal report for that named
  grant and exits blocked. No process starts and no lock, junction, manifest,
  platform file or existing runner is modified.
* No arguments prints the same blocker without writing anything.

There is deliberately no option that authorizes registry access and no deferred
"later network" path. A future window needs a new reviewed design.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True  # Snapshot mode must not write even bytecode.

RESEARCH = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
OHOS = ROOT / "ohos"
PACKAGE = "libqfli_web_cdp_transport.so"
NGINX = "libqfli_nginx_napi.so"
TYPES = OHOS / "entry/src/main/cpp/types/libqfli_web_cdp_transport"
SELF_PROOF = OHOS / "entry/src/ohosTest/ets/testability/SelfCdpProof.ets"
ENTRY_MANIFEST = OHOS / "entry/oh-package.json5"
ENTRY_LOCK = OHOS / "entry/oh-package-lock.json5"
ROOT_LOCK = OHOS / "oh-package-lock.json5"
MODULE_MAP = OHOS / "oh_modules/.ohpm/lock.json5"
DEP_MAP = OHOS / ".hvigor/dependencyMap"
ENTRY_MODULES = OHOS / "entry/oh_modules"
BLOCKER = ("source graph incomplete: the declared local dependency is absent from "
           "the generated resolution surfaces, so local-only OHPM resolution is "
           "unproven; OHPM is not started")


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read(path):
    return path.read_text(encoding="utf-8-sig", errors="replace") if path.is_file() else ""


def section(text, marker):
    """Return the text from `marker` to end of file; used for coarse section scope."""
    index = text.find(marker)
    return "" if index < 0 else text[index:]


def surfaces():
    """Read every local resolution surface. No process, no write."""
    manifest = read(ENTRY_MANIFEST)
    entry_lock = read(ENTRY_LOCK)
    root_lock = read(ROOT_LOCK)
    module_map = read(MODULE_MAP)
    types_manifest = read(TYPES / "oh-package.json5")
    types_index = read(TYPES / "index.d.ts")
    proof = read(SELF_PROOF)
    declared = re.search(r'"%s"\s*:\s*"file:[^"]+"' % re.escape(PACKAGE), manifest)
    return {
        "inputs": {
            "entryManifest": str(ENTRY_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
            "entryLock": str(ENTRY_LOCK.relative_to(ROOT)).replace("\\", "/"),
            "rootLock": str(ROOT_LOCK.relative_to(ROOT)).replace("\\", "/"),
            "moduleMap": str(MODULE_MAP.relative_to(ROOT)).replace("\\", "/"),
            "dependencyMap": sorted(str(path.relative_to(ROOT)).replace("\\", "/")
                                    for path in DEP_MAP.glob("*.json5")),
            "typesPackage": sorted(str(path.relative_to(ROOT)).replace("\\", "/")
                                   for path in TYPES.glob("*") if path.is_file()),
        },
        "declared": {
            "entryManifestCdp": bool(declared),
            "entryManifestSpecifier": declared.group(0) if declared else None,
            "entryManifestNginx": bool(re.search(r'"%s"' % re.escape(NGINX), manifest)),
            "proofImportsCdp": bool(re.search(
                r"from\s+'%s'" % re.escape(PACKAGE), proof)),
        },
        "typesPackage": {
            "name": (re.search(r'"name"\s*:\s*"([^"]+)"', types_manifest) or [None, None])[1],
            "version": (re.search(r'"version"\s*:\s*"([^"]+)"', types_manifest) or [None, None])[1],
            "types": (re.search(r'"types"\s*:\s*"([^"]+)"', types_manifest) or [None, None])[1],
            "exports": sorted(set(re.findall(r"export function (\w+)", types_index))),
        },
        "resolved": {
            "entryLockCdp": PACKAGE + "@" in entry_lock,
            "entryLockNginx": NGINX + "@" in entry_lock,
            "rootLockCdp": PACKAGE + "@" in root_lock,
            "moduleMapOverrideCdp": PACKAGE in section(module_map, '"overrideDependencyMap"'),
            "moduleMapModulesCdp": PACKAGE in section(module_map, '"modules"'),
            "moduleMapPackagesCdp": PACKAGE in section(module_map, '"packages"'),
            "entryOhModulesCdp": (ENTRY_MODULES / PACKAGE).exists(),
            "entryOhModulesNginx": (ENTRY_MODULES / NGINX).exists(),
        },
        "registryUrls": sorted(set(re.findall(r"https?://[^\s\"']+",
                                             entry_lock + root_lock + module_map))),
    }


def gap(state):
    """List every surface that still lacks the local CDP dependency."""
    missing = []
    if not state["declared"]["entryManifestCdp"]:
        missing.append("entry/oh-package.json5 declaration")
    for key, label in (("entryLockCdp", "entry/oh-package-lock.json5"),
                       ("moduleMapOverrideCdp", "oh_modules/.ohpm overrideDependencyMap"),
                       ("moduleMapModulesCdp", "oh_modules/.ohpm modules"),
                       ("moduleMapPackagesCdp", "oh_modules/.ohpm packages"),
                       ("entryOhModulesCdp", "entry/oh_modules junction")):
        if not state["resolved"][key]:
            missing.append(label)
    return missing


def snapshot():
    files = [ENTRY_MANIFEST, ENTRY_LOCK, ROOT_LOCK, MODULE_MAP, SELF_PROOF,
             TYPES / "index.d.ts", TYPES / "oh-package.json5",
             OHOS / "entry/src/main/cpp/CMakeLists.txt", OHOS / "build-profile.json5",
             OHOS / "entry/build-profile.json5"]
    files.extend(sorted(DEP_MAP.glob("*.json5")))
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    return {"files": [
        {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
         "bytes": path.stat().st_size, "sha256": file_hash(path)}
        for path in sorted(files, key=lambda item: str(item).casefold())]}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot-only", action="store_true",
                        help="Hash local surfaces only; no grant, process or file write")
    parser.add_argument("--grant", help="Named grant to record in a refusal report")
    parser.add_argument("--run-name", help="Fresh evidence name for that refusal report")
    args = parser.parse_args()

    if args.snapshot_only:
        if args.grant or args.run_name:
            parser.error("Snapshot-only preflight takes no grant arguments")
        state = surfaces()
        print(json.dumps({"snapshotOnly": True, "blocker": BLOCKER,
                          "runnable": False, "surfaces": state, "gap": gap(state),
                          "source": snapshot()}, indent=2))
        return 0

    if not args.grant and not args.run_name:
        print(json.dumps({"status": "BLOCKED", "reason": BLOCKER, "runnable": False,
                          "ohpmStarted": False,
                          "next": "the resolution source graph must be regenerated "
                                  "before any window can exist"}, indent=2))
        return 1

    if not args.grant or not args.grant.strip() or not args.run_name \
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", args.run_name):
        parser.error("A refusal report needs one --grant and one fresh --run-name")

    directory = RESEARCH / args.run_name
    directory.mkdir(exist_ok=False)
    state = surfaces()
    report = {"schemaVersion": 2, "status": "BLOCKED", "runnable": False,
              "grant": args.grant, "runName": args.run_name,
              "reason": BLOCKER, "ohpmStarted": False, "processStarted": False,
              "executionPath": "none", "startedUtc": utc(),
              "gap": gap(state), "surfaces": state, "source": snapshot(),
              "networkPolicy": "not introduced; no registry authorization exists",
              "finishedUtc": utc()}
    write_json(directory / "refusal.json", report)
    print(json.dumps({key: report[key] for key in
                      ("status", "reason", "runnable", "ohpmStarted", "gap")}, indent=2))
    print(f"refusal report: {directory.relative_to(ROOT).as_posix()}/refusal.json")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
