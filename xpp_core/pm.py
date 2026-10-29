"""
X++ Package Management System (XPM) - v0.4.6
Handles delocalized GitHub repositories, dependency resolution, lockfiles,
and package installations.

Usage via CLI:
  x install github.com/<owner>/<repo>
  x install <owner>/<repo>
  x install                        # install all deps in xpp.json
  x remove <package>
  x update [package]
  x list
  x init [name]
"""

import os
import sys
import json
import shutil
import subprocess
import urllib.request
import re
from pathlib import Path

GLOBAL_PKG_DIR = os.path.expanduser("~/.xpp/packages")
LOCAL_PKG_DIR_NAME = "xpp_packages"
MANIFEST_FILE = "xpp.json"
LOCK_FILE = "xpp.lock"


def normalize_repo_url(target: str):
    """
    Normalizes a repository identifier into (canonical_url, clone_url, pkg_name, tag).
    Examples:
      github.com/user/lib -> https://github.com/user/lib.git, name: lib
      user/lib            -> https://github.com/user/lib.git, name: lib
      https://github.com/user/lib@v1.0 -> url, tag: v1.0
    """
    raw = target.strip()
    tag = None
    if "@" in raw:
        raw, tag = raw.rsplit("@", 1)

    raw = re.sub(r"^git\+https?://", "", raw)
    raw = re.sub(r"^https?://", "", raw)
    raw = re.sub(r"\.git$", "", raw)

    parts = [p for p in raw.split("/") if p]
    if len(parts) == 2:
        host = "github.com"
        owner, repo = parts[0], parts[1]
    elif len(parts) >= 3 and "github.com" in parts[0]:
        host = "github.com"
        owner, repo = parts[1], parts[2]
    else:
        owner = parts[0] if parts else "unknown"
        repo = parts[-1] if parts else "pkg"
        host = "github.com"

    canonical = f"{host}/{owner}/{repo}"
    clone_url = f"https://{host}/{owner}/{repo}.git"
    pkg_name = repo.lower().replace("-", "_").replace(".", "_")

    return canonical, clone_url, pkg_name, tag


def get_target_dir(pkg_name: str, is_global: bool = False, cwd: str = ".") -> str:
    if is_global:
        os.makedirs(GLOBAL_PKG_DIR, exist_ok=True)
        return os.path.join(GLOBAL_PKG_DIR, pkg_name)
    local_dir = os.path.abspath(os.path.join(cwd, LOCAL_PKG_DIR_NAME))
    os.makedirs(local_dir, exist_ok=True)
    return os.path.join(local_dir, pkg_name)


def load_manifest(cwd: str = ".") -> dict:
    mf_path = os.path.join(cwd, MANIFEST_FILE)
    if os.path.exists(mf_path):
        try:
            with open(mf_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "name": os.path.basename(os.path.abspath(cwd)),
        "version": "0.1.0",
        "description": "X++ project",
        "main": "main.xp",
        "dependencies": {}
    }


def save_manifest(manifest: dict, cwd: str = "."):
    mf_path = os.path.join(cwd, MANIFEST_FILE)
    with open(mf_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_lockfile(cwd: str = ".") -> dict:
    lf_path = os.path.join(cwd, LOCK_FILE)
    if os.path.exists(lf_path):
        try:
            with open(lf_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": 1, "packages": {}}


def save_lockfile(lock: dict, cwd: str = "."):
    lf_path = os.path.join(cwd, LOCK_FILE)
    with open(lf_path, "w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2)


def fetch_github_tarball(canonical: str, tag: str, dest_dir: str):
    """Fallback when git command is not available: downloads release or tarball."""
    parts = canonical.split("/")
    owner, repo = parts[1], parts[2]
    branch = tag or "main"
    tar_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.tar.gz"
    import tarfile, tempfile
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_name = tmp.name
        try:
            req = urllib.request.Request(tar_url, headers={"User-Agent": "XPP-PackageManager/0.4.6"})
            with urllib.request.urlopen(req) as resp, open(tmp_name, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
            os.makedirs(dest_dir, exist_ok=True)
            with tarfile.open(tmp_name, "r:gz") as tar:
                # Extract stripping top-level directory
                for member in tar.getmembers():
                    parts = member.name.split("/", 1)
                    if len(parts) > 1 and parts[1]:
                        member.name = parts[1]
                        tar.extract(member, path=dest_dir)
            return True
        except Exception as e:
            return False
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)


def clone_repo(clone_url: str, canonical: str, tag: str, dest_dir: str) -> bool:
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir, ignore_errors=True)

    git_bin = shutil.which("git")
    if git_bin:
        cmd = [git_bin, "clone", "--depth", "1"]
        if tag:
            cmd.extend(["--branch", tag])
        cmd.extend([clone_url, dest_dir])
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True

    # Fallback to tarball
    return fetch_github_tarball(canonical, tag, dest_dir)


def install_package(target: str, is_global: bool = False, cwd: str = ".", verbose: bool = True) -> bool:
    canonical, clone_url, pkg_name, tag = normalize_repo_url(target)
    dest_dir = get_target_dir(pkg_name, is_global, cwd)

    if verbose:
        print(f"[XPM] Installing '{canonical}' into {dest_dir}...")

    success = clone_repo(clone_url, canonical, tag, dest_dir)
    if not success:
        if verbose:
            print(f"[XPM] Error: failed to clone/download {canonical}", file=sys.stderr)
        return False

    # Check for package manifest inside package
    pkg_meta = load_manifest(dest_dir)
    actual_name = pkg_meta.get("name", pkg_name).lower().replace("-", "_")

    # Record in manifest and lockfile if project-local
    if not is_global:
        manifest = load_manifest(cwd)
        manifest.setdefault("dependencies", {})[actual_name] = target
        save_manifest(manifest, cwd)

        lock = load_lockfile(cwd)
        commit_hash = "head"
        git_dir = os.path.join(dest_dir, ".git")
        if os.path.exists(git_dir):
            try:
                res = subprocess.run(["git", "-C", dest_dir, "rev-parse", "HEAD"],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    commit_hash = res.stdout.strip()
            except Exception:
                pass
        lock.setdefault("packages", {})[actual_name] = {
            "source": canonical,
            "version": pkg_meta.get("version", "0.1.0"),
            "commit": commit_hash,
            "installed_at": dest_dir
        }
        save_lockfile(lock, cwd)

    # Recursively install dependencies of the installed package
    sub_deps = pkg_meta.get("dependencies", {})
    for sub_name, sub_target in sub_deps.items():
        if verbose:
            print(f"[XPM] Installing sub-dependency '{sub_name}' ({sub_target})...")
        install_package(sub_target, is_global=is_global, cwd=cwd, verbose=verbose)

    if verbose:
        print(f"[XPM] + Successfully installed '{actual_name}' (v{pkg_meta.get('version', '0.1.0')})")
    return True


def install_all(cwd: str = ".", verbose: bool = True) -> bool:
    manifest = load_manifest(cwd)
    deps = manifest.get("dependencies", {})
    if not deps:
        if verbose:
            print("[XPM] No dependencies found in xpp.json")
        return True
    all_ok = True
    for name, target in deps.items():
        ok = install_package(target, is_global=False, cwd=cwd, verbose=verbose)
        if not ok:
            all_ok = False
    return all_ok


def remove_package(pkg_name: str, is_global: bool = False, cwd: str = ".", verbose: bool = True) -> bool:
    dest_dir = get_target_dir(pkg_name, is_global, cwd)
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir, ignore_errors=True)
        if verbose:
            print(f"[XPM] Removed directory {dest_dir}")
    else:
        if verbose:
            print(f"[XPM] Warning: package directory {dest_dir} not found")

    if not is_global:
        manifest = load_manifest(cwd)
        if pkg_name in manifest.get("dependencies", {}):
            del manifest["dependencies"][pkg_name]
            save_manifest(manifest, cwd)
        lock = load_lockfile(cwd)
        if pkg_name in lock.get("packages", {}):
            del lock["packages"][pkg_name]
            save_lockfile(lock, cwd)

    if verbose:
        print(f"[XPM] - Successfully uninstalled '{pkg_name}'")
    return True


def list_packages(cwd: str = "."):
    print("X++ Package Registry:")
    local_dir = os.path.abspath(os.path.join(cwd, LOCAL_PKG_DIR_NAME))
    print(f"\nProject Packages ({local_dir}):")
    if os.path.exists(local_dir):
        entries = sorted(os.listdir(local_dir))
        count = 0
        for entry in entries:
            pkg_path = os.path.join(local_dir, entry)
            if os.path.isdir(pkg_path):
                meta = load_manifest(pkg_path)
                ver = meta.get("version", "unknown")
                desc = meta.get("description", "")
                print(f"  * {entry} (v{ver}) - {desc}")
                count += 1
        if count == 0:
            print("  (none)")
    else:
        print("  (none)")

    print(f"\nGlobal Packages ({GLOBAL_PKG_DIR}):")
    if os.path.exists(GLOBAL_PKG_DIR):
        entries = sorted(os.listdir(GLOBAL_PKG_DIR))
        count = 0
        for entry in entries:
            pkg_path = os.path.join(GLOBAL_PKG_DIR, entry)
            if os.path.isdir(pkg_path):
                meta = load_manifest(pkg_path)
                ver = meta.get("version", "unknown")
                desc = meta.get("description", "")
                print(f"  * {entry} (v{ver}) - {desc}")
                count += 1
        if count == 0:
            print("  (none)")
    else:
        print("  (none)")


def update_package(pkg_name: str = None, is_global: bool = False, cwd: str = ".", verbose: bool = True):
    if not pkg_name:
        manifest = load_manifest(cwd)
        for name, target in manifest.get("dependencies", {}).items():
            update_package(name, is_global, cwd, verbose)
        return

    dest_dir = get_target_dir(pkg_name, is_global, cwd)
    if not os.path.exists(dest_dir):
        if verbose:
            print(f"[XPM] Package '{pkg_name}' is not installed; installing...")
        manifest = load_manifest(cwd)
        target = manifest.get("dependencies", {}).get(pkg_name, f"github.com/{pkg_name}")
        install_package(target, is_global, cwd, verbose)
        return

    git_dir = os.path.join(dest_dir, ".git")
    if os.path.exists(git_dir):
        if verbose:
            print(f"[XPM] Pulling latest changes for '{pkg_name}'...")
        res = subprocess.run(["git", "-C", dest_dir, "pull"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if verbose:
            print(res.stdout.strip() or "Up to date.")
    else:
        manifest = load_manifest(cwd)
        target = manifest.get("dependencies", {}).get(pkg_name, f"github.com/{pkg_name}")
        install_package(target, is_global, cwd, verbose)


def init_project(name: str = None, cwd: str = "."):
    prj_name = name or os.path.basename(os.path.abspath(cwd)) or "my_xpp_project"
    manifest = {
        "name": prj_name,
        "version": "0.1.0",
        "description": "An X++ v0.4.6 project",
        "main": "main.xp",
        "dependencies": {}
    }
    save_manifest(manifest, cwd)
    main_file = os.path.join(cwd, "main.xp")
    if not os.path.exists(main_file):
        with open(main_file, "w", encoding="utf-8") as f:
            f.write('RNM=ZITR\nout "Welcome to ' + prj_name + ' in X++ v0.4.6!"\n')
    print(f"[XPM] Initialized new X++ project '{prj_name}' with xpp.json and main.xp")


def resolve_package(name: str, cwd: str = "."):
    """
    Resolves package name or repo identifier to its root path and entry file.
    Returns (package_root, entry_file_path) or None.
    """
    clean_name = name.lower().replace("-", "_").replace(".", "_")
    if clean_name.startswith("github_com_"):
        parts = clean_name.split("_")
        clean_name = parts[-1]

    candidates = [
        os.path.join(cwd, LOCAL_PKG_DIR_NAME, clean_name),
        os.path.join(cwd, LOCAL_PKG_DIR_NAME, name),
        os.path.join(GLOBAL_PKG_DIR, clean_name),
        os.path.join(GLOBAL_PKG_DIR, name),
        os.path.join(cwd, name),
    ]

    for c in candidates:
        if os.path.isdir(c):
            # Find entry point
            mf = os.path.join(c, MANIFEST_FILE)
            entry = "main.xp"
            if os.path.exists(mf):
                try:
                    with open(mf, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        entry = meta.get("main", "main.xp")
                except Exception:
                    pass
            for cand_entry in [entry, "main.xp", f"{clean_name}.xp", f"{name}.xp", "lib.xp", "index.xp"]:
                ep = os.path.join(c, cand_entry)
                if os.path.isfile(ep):
                    return c, ep
            # If any .xp file in dir:
            for f in os.listdir(c):
                if f.endswith(".xp"):
                    return c, os.path.join(c, f)
            return c, None

    # Check if direct file exists
    direct_file = os.path.join(cwd, f"{name}.xp")
    if os.path.isfile(direct_file):
        return cwd, direct_file

    return None
