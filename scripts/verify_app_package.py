#!/usr/bin/env python3
"""Check that an application package carries the Flutter payload and the
product native runtime, then record its SHA-256.

A check lists the members the product really ships. Correct a wrong path to the
real layout; never drop a member to obtain a pass. A pass proves archive
content only: it is not an installation, signing or device result.

A Windows installer is installed silently into a temporary directory, its
installed payload is compared file by file with the archive that was built from
the same tree, and it is removed afterwards. A Debian package is extracted with
`dpkg-deb --extract` and checked for its payload, desktop entry and launcher.
"""

import argparse
import hashlib
import os
from pathlib import Path
import posixpath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile


NGINX_MARKER = b"nginx/1.31.6"
SYNTAX_MARKER = b"QuickJS 2026-06-04"
ANDROID_ABIS = ["arm64-v8a", "armeabi-v7a", "x86_64"]
OHOS_ABIS = ["arm64-v8a"]
# ZIP containers the product ships under a platform extension.
ZIP_SUFFIXES = (".zip", ".apk", ".ipa", ".hap")
TAR_SUFFIXES = (".tar.gz", ".tgz", ".tar")
LINUX_DEB_PREFIX = "opt/qfli-webforge"
LINUX_DEB_LAUNCHER = "usr/bin/qfli-webforge"
LINUX_DEB_DESKTOP = "usr/share/applications/qfli-webforge.desktop"
LINUX_DEB_ICON = "data/flutter_assets/assets/app_icon.png"
_WINDOWS_UNINSTALLER_FILES = {"unins000.exe", "unins000.dat", "unins000.msg"}
PLATFORM_LABELS = {
    "android": "Android",
    "ios": "iOS",
    "ohos": "OHOS",
    "linux": "Linux",
    "windows": "Windows",
    "macos": "macOS",
}


class PackageError(RuntimeError):
    pass


def validate_member_name(name, is_dir=False, label="archive"):
    """Reject non-canonical paths before using an archive member name."""
    if not name or "\\" in name or "\0" in name:
        raise PackageError(f"invalid {label} member path: {name!r}")
    if is_dir and name.endswith("/"):
        name = name[:-1]
    if (not name or name.startswith("/") or
            (len(name) >= 2 and name[1] == ":")):
        raise PackageError(f"unsafe {label} member path: {name!r}")
    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise PackageError(f"non-canonical {label} member path: {name!r}")
    if posixpath.normpath(name) != name:
        raise PackageError(f"non-canonical {label} member path: {name!r}")
    return name


def reject_duplicate_name(name, seen, label, case_insensitive=False):
    key = name.casefold() if case_insensitive else name
    if key in seen:
        raise PackageError(f"duplicate {label} member path: {name}")
    seen.add(key)


def read_zip(path, platform):
    """Return safe member sizes, a reader and a close callback for a ZIP."""
    archive = zipfile.ZipFile(path)
    try:
        sizes, entries, seen = {}, {}, set()
        path_keys, file_keys = set(), set()
        for info in archive.infolist():
            name = validate_member_name(info.filename, info.is_dir(), "ZIP")
            reject_duplicate_name(name, seen, "ZIP",
                                  case_insensitive=platform == "windows")
            key = name.casefold() if platform == "windows" else name
            is_dir = info.is_dir()
            parent = posixpath.dirname(key)
            while parent:
                if parent in file_keys:
                    raise PackageError(f"conflicting ZIP member path: {name}")
                parent = posixpath.dirname(parent)
            if not is_dir and any(existing.startswith(key + "/") for existing in path_keys):
                raise PackageError(f"conflicting ZIP member path: {name}")
            path_keys.add(key)
            if not is_dir:
                file_keys.add(key)
                entries[key] = info
                entries[name] = info
                sizes[name] = info.file_size

        def read(name):
            info = entries.get(name)
            if info is None and platform == "windows":
                info = entries.get(name.casefold())
            if info is None:
                raise PackageError(f"no archive member: {name}")
            with archive.open(info) as stream:
                return stream.read()

        return sizes, read, archive.close
    except Exception:
        archive.close()
        raise


def read_tar(path):
    """Return safe member sizes and a reader for a tar archive."""
    mode = "r:gz" if path.name.lower().endswith((".tar.gz", ".tgz")) else "r:*"
    archive = tarfile.open(path, mode)
    try:
        files, links, seen = {}, {}, set()
        file_paths, all_paths = set(), set()
        for member in archive.getmembers():
            name = validate_member_name(member.name, member.isdir(), "tar")
            reject_duplicate_name(name, seen, "tar")
            is_file = member.isfile() or member.issym() or member.islnk()
            parent = posixpath.dirname(name)
            while parent:
                if parent in file_paths:
                    raise PackageError(f"conflicting tar member path: {name}")
                parent = posixpath.dirname(parent)
            if is_file and any(existing.startswith(name + "/") for existing in all_paths):
                raise PackageError(f"conflicting tar member path: {name}")
            all_paths.add(name)
            if is_file:
                file_paths.add(name)
            if member.isfile():
                files[name] = member
            elif member.issym() or member.islnk():
                target = member.linkname
                if not target or "\\" in target or "\0" in target or target.startswith("/"):
                    raise PackageError(f"unsafe tar link target for {name}: {target!r}")
                if member.islnk():
                    target = validate_member_name(target, label="tar hard-link")
                else:
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
                    if target == ".." or target.startswith("../"):
                        raise PackageError(f"tar link escapes archive root: {name} -> {member.linkname}")
                    target = validate_member_name(target, label="tar symlink")
                links[name] = (member, target)

        def read(name, seen_links=None):
            if name in files:
                handle = archive.extractfile(files[name])
                if handle is None:
                    raise PackageError(f"cannot read archive member: {name}")
                with handle:
                    return handle.read()
            link = links.get(name)
            if link is None:
                raise PackageError(f"no archive member: {name}")
            seen_links = set() if seen_links is None else seen_links
            if name in seen_links:
                raise PackageError(f"symlink loop at archive member: {name}")
            seen_links.add(name)
            return read(link[1], seen_links)

        sizes = {name: member.size for name, member in files.items()}
        # File links are content members too. Directory links are not followed.
        for name, (member, target) in links.items():
            try:
                data = read(name)
            except PackageError:
                continue
            sizes[name] = len(data)
        return sizes, read, archive.close
    except Exception:
        archive.close()
        raise


def read_directory(path):
    root = Path(path).resolve(strict=True)
    sizes, names = {}, set()
    for item in root.rglob("*"):
        name = item.relative_to(root).as_posix()
        try:
            resolved = item.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise PackageError(f"cannot resolve directory member {name}: {error}") from error
        try:
            resolved.relative_to(root)
        except ValueError as error:
            raise PackageError(f"directory member escapes package root: {name}") from error
        if not item.is_file():
            continue
        validate_member_name(name, label="directory")
        reject_duplicate_name(name, names, "directory", case_insensitive=os.name == "nt")
        sizes[name] = item.stat().st_size

    def read(name):
        if name not in sizes:
            raise PackageError(f"no directory member: {name}")
        target = (root / name).resolve(strict=True)
        try:
            target.relative_to(root)
        except ValueError as error:
            raise PackageError(f"directory member escapes package root: {name}") from error
        return target.read_bytes()

    return sizes, read, lambda: None


def strip_single_root(sizes, read):
    """Desktop archives wrap the bundle in one top-level directory."""
    roots = {name.split("/", 1)[0] for name in sizes}
    if len(roots) != 1 or any("/" not in name for name in sizes):
        raise PackageError("archive must contain exactly one top-level directory")
    prefix = roots.pop() + "/"
    stripped = {name[len(prefix):]: size for name, size in sizes.items()}
    if not stripped or any(not name for name in stripped):
        raise PackageError("archive has no files below its top-level directory")
    return stripped, lambda name: read(prefix + name)


def android_requirements(abis):
    required, markers = [], {}
    for abi in abis:
        base = f"lib/{abi}/"
        required += [base + "libapp.so", base + "libflutter.so",
                     base + "libnginx_exec.so", base + "libqfli_web_syntax.so"]
        markers[base + "libnginx_exec.so"] = NGINX_MARKER
        markers[base + "libqfli_web_syntax.so"] = SYNTAX_MARKER
    required += ["AndroidManifest.xml", "classes.dex",
                 "assets/flutter_assets/AssetManifest.bin"]
    return required, markers


def ohos_requirements(abis):
    required, markers = [], {}
    for abi in abis:
        base = f"libs/{abi}/"
        required += [base + "libapp.so", base + "libflutter.so",
                     base + "libqfli_nginx_napi.so", base + "libqfli_web_syntax.so",
                     base + "libqfli_web_cdp_transport.so"]
        markers[base + "libqfli_nginx_napi.so"] = NGINX_MARKER
        markers[base + "libqfli_web_syntax.so"] = SYNTAX_MARKER
    required += ["module.json", "resources/rawfile/flutter_assets/AssetManifest.bin"]
    return required, markers


def ios_requirements():
    app = "Payload/Runner.app/"
    required = [app + "Runner", app + "Info.plist",
                app + "Frameworks/App.framework/App",
                app + "Frameworks/Flutter.framework/Flutter",
                app + "Frameworks/App.framework/flutter_assets/AssetManifest.bin"]
    # Nginx and the syntax bridge are static archives linked into Runner, so
    # they have no member of their own. Their string constants prove the link.
    markers = {app + "Runner": [NGINX_MARKER, SYNTAX_MARKER]}
    return required, markers


def linux_requirements():
    required = ["qfli_web", "lib/libapp.so", "lib/libflutter_linux_gtk.so",
                "lib/libqfli_web_syntax.so", "data/nginx/nginx", "data/icudtl.dat",
                "data/flutter_assets/AssetManifest.bin"]
    markers = {"data/nginx/nginx": NGINX_MARKER,
               "lib/libqfli_web_syntax.so": SYNTAX_MARKER}
    return required, markers


def windows_requirements():
    required = ["qfli_web.exe", "flutter_windows.dll", "qfli_web_syntax.dll",
                "data/app.so", "data/icudtl.dat", "data/nginx/nginx.exe",
                "data/flutter_assets/AssetManifest.bin"]
    markers = {"data/nginx/nginx.exe": NGINX_MARKER,
               "qfli_web_syntax.dll": SYNTAX_MARKER}
    return required, markers


def macos_requirements():
    frameworks = "Contents/Frameworks/"
    required = ["Contents/Info.plist", "Contents/Helpers/nginx",
                frameworks + "libqfli_web_syntax.dylib",
                frameworks + "App.framework/App",
                frameworks + "FlutterMacOS.framework/FlutterMacOS",
                # Real path: directory symlinks (Resources) are not followed.
                frameworks + "App.framework/Versions/A/Resources/flutter_assets/AssetManifest.bin"]
    markers = {"Contents/Helpers/nginx": NGINX_MARKER,
               frameworks + "libqfli_web_syntax.dylib": SYNTAX_MARKER}
    return required, markers


def requirements_for(platform, abis):
    if platform == "android":
        return android_requirements(abis or ANDROID_ABIS)
    if platform == "ohos":
        return ohos_requirements(abis or OHOS_ABIS)
    return {
        "ios": ios_requirements,
        "linux": linux_requirements,
        "windows": windows_requirements,
        "macos": macos_requirements,
    }[platform]()


def load_package(platform, package, strip):
    """Return the member sizes and a reader for one package form.

    A directory is read as a tree. ZIP containers include .apk, .ipa and .hap.
    Tar containers include .tar.gz and .tgz.
    """
    path = Path(package)
    if path.is_dir():
        return read_directory(path)
    lowered = path.name.lower()
    if lowered.endswith(ZIP_SUFFIXES):
        sizes, read, close = read_zip(path, platform)
    elif lowered.endswith(TAR_SUFFIXES):
        sizes, read, close = read_tar(path)
    else:
        raise PackageError(
            f"unsupported package form for {platform}: {path.name}; "
            f"expected one of {', '.join(ZIP_SUFFIXES + TAR_SUFFIXES)} or a directory")
    try:
        if strip:
            # Desktop archives wrap the bundle in one top-level directory.
            sizes, read = strip_single_root(sizes, read)
        return sizes, read, close
    except Exception:
        close()
        raise


def check_members(platform, sizes, read, abis, label):
    required, markers = requirements_for(platform, abis)
    problems = []
    for member in required:
        if member not in sizes:
            problems.append(f"missing member: {member}")
        elif sizes[member] == 0:
            problems.append(f"empty member: {member}")
        else:
            print(f"PASS member: {label} {member} ({sizes[member]} bytes)")
    if platform in ("android", "ohos"):
        prefix = "lib/" if platform == "android" else "libs/"
        actual_abis = sorted({
            parts[1]
            for name in sizes if name.startswith(prefix)
            for parts in [name.split("/")]
            if len(parts) >= 3 and parts[1]
        })
        if not actual_abis:
            problems.append(f"missing {platform} ABI native members")
        for abi in actual_abis:
            abi_required, abi_markers = requirements_for(platform, [abi])
            for member in abi_required:
                if member.startswith(prefix + abi + "/"):
                    if member not in sizes:
                        problems.append(f"ABI {abi} is missing member: {member}")
                    elif sizes[member] == 0:
                        problems.append(f"ABI {abi} has empty member: {member}")
            for member, expected in abi_markers.items():
                if member not in sizes or sizes[member] == 0:
                    continue
                data = read(member)
                for marker in expected if isinstance(expected, list) else [expected]:
                    if marker not in data:
                        problems.append(
                            f"ABI {abi}: content marker '{marker.decode('ascii')}' not found in {member}")
        if platform == "ohos":
            forbidden = sorted(name for name in sizes if (
                name.rsplit("/", 1)[-1].lower() in {
                    "nginx", "nginx.exe", "libnginx_exec.so"}))
            if forbidden:
                problems.append("OHOS package contains forbidden process Nginx executable(s): "
                                + ", ".join(forbidden))
    if platform == "macos":
        executables = sorted(name for name in sizes if name.startswith("Contents/MacOS/"))
        if not executables:
            problems.append("missing member: Contents/MacOS/<executable>")
        else:
            print(f"PASS member: {label} {executables[0]} ({sizes[executables[0]]} bytes)")
    # Check non-ABI native markers once. Mobile markers were checked per actual ABI.
    if platform not in ("android", "ohos"):
        for member, expected in markers.items():
            if member not in sizes or sizes[member] == 0:
                continue
            data = read(member)
            for marker in expected if isinstance(expected, list) else [expected]:
                text = marker.decode("ascii")
                if marker in data:
                    print(f"PASS content: {label} {member} contains '{text}'")
                else:
                    problems.append(f"content marker '{text}' not found in {member}")
    if problems:
        raise PackageError(f"{label} content check failed:\n  " + "\n  ".join(problems))


def verify(platform, package, abis, label="package", strip=False):
    path = Path(package)
    if not path.exists():
        raise PackageError(f"{label} not found: {path}")
    if path.is_file() and path.stat().st_size == 0:
        raise PackageError(f"empty {label}: {path}")
    if platform == "macos" and not path.is_dir():
        raise PackageError("macOS verification reads the .app directory, not the dmg")
    sizes, read, close = load_package(platform, path, strip)
    try:
        check_members(platform, sizes, read, abis, label)
        return sizes, read, close
    except Exception:
        close()
        raise


def tree_digests(sizes, read):
    """Return {relative path: sha256} for every file of a tree."""
    return {name: hashlib.sha256(read(name)).hexdigest() for name in sorted(sizes)}


def compare_tree(reference, installed, reference_label, installed_label,
                 allowed_extra=None):
    """Require byte-identical trees, except named uninstaller files."""
    allowed_extra = set() if allowed_extra is None else set(allowed_extra)
    missing = sorted(set(reference) - set(installed))
    differing = sorted(name for name in reference
                       if name in installed and reference[name] != installed[name])
    extra = sorted(set(installed) - set(reference))
    unexpected = sorted(set(extra) - allowed_extra)
    problems = []
    if missing:
        problems.append(f"{len(missing)} file(s) missing from {installed_label}: "
                        + ", ".join(missing[:10]))
    if differing:
        problems.append(f"{len(differing)} file(s) differ between {reference_label} and "
                        f"{installed_label}: " + ", ".join(differing[:10]))
    if unexpected:
        problems.append(f"{len(unexpected)} unexpected file(s) in {installed_label}: "
                        + ", ".join(unexpected[:10]))
    if problems:
        raise PackageError("Payload differs from the built tree:\n  " + "\n  ".join(problems))
    if extra:
        print(f"PASS allowed uninstaller files: {', '.join(extra)}")
    print(f"PASS payload: {len(reference)} file(s) of {installed_label} match "
          f"{reference_label} byte for byte")


def verify_linux_installer(path, reference):
    """Extract the Deb and compare payload, desktop entry and launcher."""
    if path.suffix.lower() != ".deb":
        raise PackageError(f"Linux installer must be a .deb: {path}")
    with tempfile.TemporaryDirectory(prefix="qfli-deb-inspect-") as destination:
        subprocess.run(["dpkg-deb", "--extract", str(path), destination],
                       check=True, capture_output=True, text=True, timeout=900)
        root = Path(destination)
        payload = root / LINUX_DEB_PREFIX
        if not payload.is_dir():
            raise PackageError(f"Debian package has no {LINUX_DEB_PREFIX} payload")
        if not os.access(payload / "qfli_web", os.X_OK):
            raise PackageError("Debian payload qfli_web is not executable")

        desktop = root / LINUX_DEB_DESKTOP
        if not desktop.is_file():
            raise PackageError(f"Debian package has no desktop entry: {LINUX_DEB_DESKTOP}")
        entry = desktop.read_text(encoding="utf8", errors="replace")
        values = {}
        for line in entry.splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values.setdefault(key, []).append(value)
        expected_values = {
            "Type": "Application",
            "Exec": "/opt/qfli-webforge/qfli_web",
            "Icon": f"/opt/qfli-webforge/{LINUX_DEB_ICON}",
        }
        for key, value in expected_values.items():
            if values.get(key) != [value]:
                raise PackageError(f"Desktop entry requires exactly {key}={value}")
        if not (payload / LINUX_DEB_ICON).is_file():
            raise PackageError(f"Debian payload has no referenced icon: {LINUX_DEB_ICON}")
        print(f"PASS desktop entry and icon: {LINUX_DEB_DESKTOP}")

        launcher = root / LINUX_DEB_LAUNCHER
        expected_launcher = (
            b'#!/bin/sh\n'
            b'# Launcher installed by the qfli-webforge Debian package.\n'
            b'exec /opt/qfli-webforge/qfli_web "$@"\n'
        )
        if not launcher.is_file() or launcher.is_symlink():
            raise PackageError(f"Debian launcher must be a regular shell script: {LINUX_DEB_LAUNCHER}")
        if launcher.read_bytes() != expected_launcher:
            raise PackageError(f"Debian launcher has unexpected contents: {LINUX_DEB_LAUNCHER}")
        if not os.access(launcher, os.X_OK):
            raise PackageError(f"Debian launcher is not executable: {LINUX_DEB_LAUNCHER}")
        print(f"PASS launcher: {LINUX_DEB_LAUNCHER} has the expected shell contents")

        installed_sizes, installed_read, installed_close = read_directory(payload)
        try:
            check_members("linux", installed_sizes, installed_read, None, "Debian payload")
            installed = tree_digests(installed_sizes, installed_read)
        finally:
            installed_close()
        reference_sizes, reference_read = reference
        built = tree_digests(reference_sizes, reference_read)
        compare_tree(built, installed, "Linux tar.gz payload", "Debian payload")
        return installed


def verify_windows_installer(path, reference):
    """Install the EXE silently, compare its payload and check uninstall."""
    if path.suffix.lower() != ".exe":
        raise PackageError(f"Windows installer must be a .exe: {path}")
    destination = Path(tempfile.mkdtemp(prefix="qfli-exe-inspect-"))
    log_dir = Path.cwd() / "build" / "ci" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / "windows-installer-verification.log"
    lines = []

    def run_logged(command, timeout):
        result = subprocess.run(command, check=False, capture_output=True,
                                 text=True, timeout=timeout)
        lines.append(f"$ {' '.join(map(str, command))} (exit {result.returncode})\n")
        lines.append(result.stdout or "")
        lines.append(result.stderr or "")
        log.write_text("".join(lines), encoding="utf8", newline="\n")
        return result

    def preserve_inno_log(source, name):
        if source.is_file():
            shutil.copy2(source, log_dir / name)

    try:
        installer_log = destination.with_name(destination.name + "-install.log")
        uninstall_log = destination.with_name(destination.name + "-uninstall.log")
        result = run_logged(
            [str(path), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
             "/SP-", f"/DIR={destination}", f"/LOG={installer_log}"], 1800)
        preserve_inno_log(installer_log, "windows-inno-install.log")
        if result.returncode != 0:
            raise PackageError(f"Windows installer exited {result.returncode}; see {log}")
        executables = sorted(destination.rglob("qfli_web.exe"))
        if len(executables) != 1:
            raise PackageError(
                f"Windows installer must place exactly one qfli_web.exe; found {len(executables)}")
        if executables[0].parent != destination:
            raise PackageError("Windows installer placed qfli_web.exe outside its target directory")
        sizes, read, close = read_directory(destination)
        try:
            check_members("windows", sizes, read, None, "Windows installer payload")
            installed = tree_digests(sizes, read)
        finally:
            close()
        reference_sizes, reference_read = reference
        built = tree_digests(reference_sizes, reference_read)
        uninstaller_files = {"unins000.exe", "unins000.dat", "unins000.msg"}
        allowed_extra = set()
        for name in set(installed) - set(built):
            if "/" in name or name.casefold() not in uninstaller_files:
                raise PackageError(f"unexpected Windows installer payload file: {name}")
            allowed_extra.add(name)
        compare_tree(built, installed, "built tree", "installed payload", allowed_extra)

        uninstallers = sorted(destination.glob("unins*.exe"))
        if len(uninstallers) != 1 or uninstallers[0].name.casefold() != "unins000.exe":
            raise PackageError(
                f"Windows installer must create exactly one unins000.exe; found {len(uninstallers)}")
        result = run_logged(
            [str(uninstallers[0]), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
             f"/LOG={uninstall_log}"], 300)
        preserve_inno_log(uninstall_log, "windows-inno-uninstall.log")
        if result.returncode != 0:
            raise PackageError(f"Windows uninstaller exited {result.returncode}; see {log}")
        remaining = sorted(name for name in built if (destination / name).exists())
        if remaining:
            raise PackageError("Windows uninstaller left payload files: "
                               + ", ".join(remaining[:10]))
        print(f"PASS uninstaller: exit 0; logs preserved in {log_dir}")
    except subprocess.TimeoutExpired as error:
        lines.append(f"process timeout: {error}\n")
        log.write_text("".join(lines), encoding="utf8", newline="\n")
        raise PackageError(f"Windows installer verification timed out; see {log}") from error
    finally:
        shutil.rmtree(destination, ignore_errors=True)
        for transient_log in (destination.with_name(destination.name + "-install.log"),
                              destination.with_name(destination.name + "-uninstall.log")):
            transient_log.unlink(missing_ok=True)


def verify_installer(platform, installer, reference=None):
    path = Path(installer)
    if not path.is_file() or path.stat().st_size == 0:
        raise PackageError(f"Installer not found or empty: {path}")
    if platform == "linux":
        if reference is None:
            raise PackageError("Linux installer verification needs the tar.gz payload")
        return verify_linux_installer(path, reference)
    if platform == "windows":
        if reference is None:
            raise PackageError("Windows installer verification needs the built tree")
        return verify_windows_installer(path, reference)
    raise PackageError(f"Unsupported installer platform: {platform}")


def verify_macos_image(image, reference_path):
    """Mount the hosted DMG and compare its actual .app tree to the source."""
    image = Path(image)
    reference_path = Path(reference_path)
    if not image.is_file() or image.stat().st_size == 0:
        raise PackageError(f"macOS image not found or empty: {image}")
    if not reference_path.is_dir():
        raise PackageError("macOS image comparison requires the source .app directory")
    reference_sizes, reference_read, reference_close = read_directory(reference_path)
    try:
        reference = tree_digests(reference_sizes, reference_read)
    finally:
        reference_close()

    with tempfile.TemporaryDirectory(prefix="qfli-dmg-mount-") as mount_name:
        mount = Path(mount_name)
        attached = False
        try:
            result = subprocess.run(
                ["hdiutil", "attach", "-readonly", "-nobrowse", "-mountpoint",
                 str(mount), str(image)],
                check=False, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise PackageError(
                    "hdiutil attach failed: " + (result.stderr or result.stdout).strip())
            attached = True
            apps = sorted(item for item in mount.iterdir()
                          if item.is_dir() and item.suffix.lower() == ".app")
            if len(apps) != 1:
                raise PackageError(
                    f"DMG must contain exactly one .app at its root; found {len(apps)}")
            image_sizes, image_read, image_close = read_directory(apps[0])
            try:
                actual = tree_digests(image_sizes, image_read)
            finally:
                image_close()
            compare_tree(reference, actual, "source .app", "mounted DMG .app")
            print(f"PASS image: mounted {image.name} and matched {apps[0].name}")
        finally:
            if attached:
                result = subprocess.run(
                    ["hdiutil", "detach", str(mount)],
                    check=False, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    raise PackageError(
                        "hdiutil detach failed: " + (result.stderr or result.stdout).strip())


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_checksum(path):
    digest = sha256_of(path)
    path.with_name(path.name + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="utf8", newline="\n")
    print(f"PASS checksum: {digest}  {path.name}")
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORM_LABELS))
    parser.add_argument("--package", required=True, action="append", dest="packages",
                        help="Archive or directory to check. Repeat for every upload "
                             "form; for macOS pass the .app directory and use --image")
    parser.add_argument("--image",
                        help="macOS only: the dmg built from the verified .app")
    parser.add_argument("--installer",
                        help="Linux .deb or Windows .exe built from the verified payload")
    parser.add_argument("--abi", action="append", dest="abis",
                        help="Android/OHOS ABI to require; repeat for several (default: all shipped ABIs)")
    parser.add_argument("--signing",
                        help="Signing state to record in the run summary, for example 'debug key'")
    parser.add_argument("--native-provenance", required=True,
                        help="State whether the native runtime was source-built in this run "
                             "or came from a tracked prebuilt")
    args = parser.parse_args()

    if args.image and args.platform != "macos":
        parser.error("--image applies to macOS only")
    if args.platform == "macos" and not args.image:
        parser.error("macOS package verification requires --image")
    if args.installer and args.platform not in ("linux", "windows"):
        parser.error("--installer applies to Linux .deb and Windows .exe packages")
    if args.installer and len(args.packages) < 1:
        parser.error("--installer requires a reference --package")
    try:
        primary = None
        readers = []
        for index, package in enumerate(args.packages):
            strip = args.platform in ("linux", "windows") and index == 0
            sizes, read, close = verify(args.platform, package, args.abis,
                                        label="package", strip=strip)
            readers.append(close)
            if index == 0:
                primary = (sizes, read)
        if args.installer:
            verify_installer(args.platform, args.installer, reference=primary)
        if args.image:
            verify_macos_image(args.image, args.packages[0])
        artifacts = [Path(item) for item in args.packages]
        if args.installer:
            artifacts.append(Path(args.installer))
        if args.image:
            artifacts.append(Path(args.image))
        hashed = [item for item in artifacts if item.is_file()]
        if not hashed:
            raise PackageError("No package file to hash")
        print(f"PASS: {args.platform} package content: "
              + ", ".join(item.name for item in artifacts))
        digests = [(item, write_checksum(item)) for item in hashed]
    except (PackageError, zipfile.BadZipFile, tarfile.TarError,
            subprocess.SubprocessError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    finally:
        for close in locals().get("readers", []):
            close()

    if args.signing:
        label = PLATFORM_LABELS[args.platform]
        core = os.environ.get("QFLI_CORE_COMMIT", "unknown")
        flutter = os.environ.get("QFLI_FLUTTER_REVISION", "unknown")
        provenance = args.native_provenance
        names = "<br>".join(f"`{item.name}`" for item, _ in digests)
        sums = "<br>".join(f"`{digest}`" for _, digest in digests)
        row = (f"| {label} | {names} | {args.signing} | `{core}` "
               f"| `{flutter}` | {provenance} | {sums} |\n")
        # The release job joins these rows into the release notes, so the file
        # must stay beside the packages that the job uploads.
        summary_file = hashed[0].parent / f"{args.platform}.summary.md"
        summary_file.write_text(row, encoding="utf8", newline="\n")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf8", newline="\n") as stream:
                stream.write("\n| Platform | Package | Signing | qflistudio-core "
                             "| Flutter fork | Native provenance | SHA-256 |\n")
                stream.write("| --- | --- | --- | --- | --- | --- | --- |\n")
                stream.write(row)
                stream.write("\nContent check passed. No device, store or signing acceptance ran.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())