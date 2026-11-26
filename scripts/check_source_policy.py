#!/usr/bin/env python3
"""Hosted, source-only gates; never import product code or inspect local caches."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from pathlib import Path, PurePosixPath
import hashlib
import re
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
OPERATIONAL_ROOTS = ("scripts/", "native/", "test/", "tool/", ".github/", ".trellis/scripts/")
GENERATED_PARTS = {
    "build", ".build", ".dart_tool", ".gradle", ".hvigor", ".cxx", "node_modules",
    "oh_modules", "__pycache__", ".pub-cache", ".pub", "Pods", "ephemeral",
    ".cache", "cache", ".npm", ".venv", "venv", "target", "dist", "out",
}
RUNTIME_ROOTS = (
    ".trellis/.runtime/", ".dsh/", ".pi/agent/sessions/", ".pi/agent/logs/",
    ".claude/sessions/", ".claude/cache/",
)
INTEGRATION_ROOTS = (".agents/", ".pi/", ".claude/", ".codex/", ".gemini/", ".opencode/")
PORTABLE_INTEGRATION_ROOTS = (
    ".agents/agents/", ".agents/skills/",
    ".pi/extensions/", ".pi/prompts/", ".pi/skills/", ".pi/themes/",
    ".claude/agents/", ".claude/commands/", ".claude/hooks/", ".claude/skills/",
    ".codex/agents/", ".codex/skills/",
    ".gemini/agents/", ".gemini/commands/", ".gemini/skills/",
    ".opencode/agents/", ".opencode/commands/", ".opencode/skills/",
)
ARTIFACT_SUFFIXES = (
    ".log", ".pyc", ".pyo", ".class", ".o", ".obj", ".a", ".so", ".dll",
    ".dylib", ".exe", ".apk", ".aab", ".hap", ".ipa", ".msi", ".msix",
    ".dmg", ".deb", ".rpm", ".zip", ".tar.gz", ".tar.xz", ".tgz", ".7z",
)
PRIVATE_SUFFIXES = (".key", ".jks", ".keystore", ".p12", ".pfx", ".mobileprovision")
PRIVATE_NAMES = {"key.properties", "local.properties", "id_rsa", "id_ed25519", ".netrc"}
PRIVATE_KEY = re.compile(rb"(?m)^\s*-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----\s*$")
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def paths(data: bytes) -> set[str]:
    return {item.decode("utf-8") for item in data.split(b"\0") if item}


def blob(revision: str, path: str) -> bytes:
    return git("show", f"{revision}:{path}")


class UniqueLoader(yaml.BaseLoader):
    """Keep YAML keys such as GitHub's `on` literal and reject duplicates."""


def unique_mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str) or key in result:
            raise ValueError(f"duplicate or non-scalar YAML key at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def check_syntax(tracked: set[str], changed: set[str], errors: list[str]) -> None:
    python_count = yaml_count = 0
    for path in sorted(tracked):
        operational = path.startswith(OPERATIONAL_ROOTS) or "/" not in path
        if not operational and path not in changed:
            continue  # Historical research snapshots are evidence, not live CI code.
        try:
            if path.endswith(".py"):
                ast.parse((ROOT / path).read_bytes(), filename=path)
                python_count += 1
            elif path.endswith((".yaml", ".yml")):
                documents = list(yaml.load_all((ROOT / path).read_text(encoding="utf-8"), Loader=UniqueLoader))
                if path.startswith(".github/") and (
                    len(documents) != 1 or not isinstance(documents[0], dict)
                ):
                    raise ValueError("GitHub YAML requires one mapping document")
                yaml_count += 1
        except (SyntaxError, UnicodeError, ValueError, yaml.YAMLError) as error:
            # Do not echo arbitrary source lines, which could contain credentials.
            errors.append(f"{path}: invalid source ({type(error).__name__})")
    print(f"Parsed {python_count} Python files and {yaml_count} YAML files without executing them.")


def is_hashed_product_input(path: str, tracked: set[str]) -> bool:
    """Require an exact, normalized repo-relative manifest entry and matching digest."""
    try:
        candidate_digest = hashlib.sha256(blob("HEAD", path)).hexdigest()
    except subprocess.CalledProcessError:
        return False

    manifests = paths(git("ls-files", "-z", "--", "vendor/**/HASHES.sha256"))
    for manifest in manifests:
        content = (ROOT / manifest).read_text(encoding="utf-8")
        manifest_dir = PurePosixPath(manifest).parent
        for line in content.splitlines():
            fields = line.strip().split()
            if len(fields) < 2 or fields[0].startswith("#"):
                continue
            expected_digest, declared_path = fields[0].lower(), fields[-1]
            if declared_path.startswith("*"):
                declared_path = declared_path[1:]
            if not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
                continue
            if not declared_path or "\\" in declared_path or declared_path.startswith("/"):
                continue
            components = declared_path.split("/")
            if any(part in ("", ".", "..") for part in components):
                continue
            manifest_path = PurePosixPath(declared_path).as_posix()
            if manifest_path.startswith("vendor/") or manifest_path in tracked:
                repo_path = manifest_path
            else:
                repo_path = (manifest_dir / manifest_path).as_posix()
            if repo_path != path or repo_path not in tracked:
                continue
            if candidate_digest == expected_digest:
                continue
            if candidate_digest == expected_digest:
                return True
    return False


def is_portable_integration_source(path: str) -> bool:
    return path.startswith(PORTABLE_INTEGRATION_ROOTS)


def check_artifacts(tracked: set[str], changed: set[str], added: set[str], errors: list[str]) -> None:
    for path in sorted(changed):
        parts = PurePosixPath(path).parts
        name = parts[-1].lower()
        if path.startswith(INTEGRATION_ROOTS) and not (
            is_portable_integration_source(path) or path.startswith(RUNTIME_ROOTS)
        ):
            errors.append(f"{path}: agent integration files must use an approved portable source directory")
        if path.startswith(RUNTIME_ROOTS):
            errors.append(f"{path}: private agent runtime/session data")
        if path.endswith((".local.json", ".local.yaml", ".local.yml")) or name in PRIVATE_NAMES or name.endswith(PRIVATE_SUFFIXES) or name in {".env", "settings.local.json", "settings.local.yaml"} or (name.startswith(".env.") and name not in {".env.example", ".env.sample"}):
            errors.append(f"{path}: private signing, credentials or machine-local file")
        if PRIVATE_KEY.search(blob("HEAD", path)):
            errors.append(f"{path}: private-key block (contents suppressed)")
        if path not in added:
            continue  # Existing research logs and retained native inputs remain legal.
        if any(part != part.strip() for part in parts) or any(ord(char) < 32 for char in path):
            errors.append(f"{path!r}: malformed or control-character path")
        if GENERATED_PARTS.intersection(parts) or path.startswith(RUNTIME_ROOTS):
            errors.append(f"{path}: newly tracked generated/cache/private runtime output")
        elif name.endswith(ARTIFACT_SUFFIXES) and not is_hashed_product_input(path, tracked):
            errors.append(f"{path}: newly tracked build/archive/log output without a retained-input checksum")
    print(f"Reviewed {len(changed)} changed paths, including {len(added)} additions; baseline artifacts retained.")


def chinese_findings(text: str) -> list[dict]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/ste-lint-zh.py"), "--json"],
        input=text, text=True, encoding="utf-8", capture_output=True, cwd=ROOT,
    )
    if result.returncode not in (0, 1):
        raise ValueError("controlled-Chinese linter could not analyze the document")
    import json

    return [finding for finding in json.loads(result.stdout) if finding["severity"] == "hard"]


def check_chinese(base: str, changed: set[str], added: set[str], errors: list[str]) -> None:
    count = 0
    for path in sorted(changed):
        # Product docs only: never rewrite AGENTS, user rules or task evidence.
        product_doc = path.startswith("docs/") or ("/" not in path and path.startswith("README"))
        if not product_doc or not path.endswith(".md"):
            continue
        current = blob("HEAD", path).decode("utf-8-sig")
        if not CJK.search(current):
            continue
        previous = "" if path in added else blob(base, path).decode("utf-8-sig")
        before = Counter((item["rule"], item["match"]) for item in chinese_findings(previous))
        findings = chinese_findings(current)
        after = Counter((item["rule"], item["match"]) for item in findings)
        added_findings = after - before
        for finding in findings:
            key = (finding["rule"], finding["match"])
            if added_findings[key]:
                errors.append(f"{path}:{finding['line']}: added controlled-Chinese violation ({finding['rule']})")
                added_findings[key] -= 1
        count += 1
    print(f"Chinese lint: {count} changed product documents; only added hard violations fail.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Reviewed comparison SHA/tree; never a PR title or branch name")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.base):
        parser.error("--base must be a full Git SHA")
    git("rev-parse", "--verify", f"{args.base}^{{tree}}")
    tracked = paths(git("ls-files", "-z"))
    changed = paths(git("diff", "--no-renames", "--name-only", "--diff-filter=ACM", "-z", args.base, "HEAD", "--"))
    added = paths(git("diff", "--no-renames", "--name-only", "--diff-filter=A", "-z", args.base, "HEAD", "--"))
    print(f"Source: {git('rev-parse', 'HEAD').decode().strip()}\nComparison: {args.base}")
    errors: list[str] = []
    check_syntax(tracked, changed, errors)
    check_artifacts(tracked, changed, added, errors)
    check_chinese(args.base, changed, added, errors)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"Source policy: {len(errors)} error(s).")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
