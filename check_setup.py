"""ECE 105 (Fall 2026) -- Lab 0 environment checker.

Run this once you think your environment is set up:

    python check_setup.py

It reports on every tool and package this course needs, and prints a one-line
fix for anything that is missing. Nothing here is installed or changed -- the
script only looks.

This file deliberately uses the standard library only, so that it still runs
on a machine where numpy and friends have not been installed yet.
"""

import importlib
import os
import shutil
import subprocess
import sys

# Packages we use this term, in the order they show up in the course.
PACKAGES = [
    ("numpy", "arrays and vectorized math"),
    ("matplotlib", "plotting"),
    ("pandas", "data frames"),
    ("scipy", "optimization and curve fitting"),
    ("networkx", "graphs and network simulation"),
    ("pytest", "unit testing"),
]

MIN_PYTHON = (3, 10)

CONDA_FIX = (
    "conda install -c conda-forge numpy matplotlib pandas scipy networkx pytest"
)

results = []  # (ok, label, detail, fix) -- fix is only shown when ok is False


def record(ok, label, detail, fix=""):
    results.append((ok, label, detail, fix))


def run(cmd):
    """Run a command, return its first line of output, or None if it failed.

    Returns None rather than raising for any reason a student machine might
    give us: the program is missing, it hangs, it exits non-zero, or it prints
    bytes we cannot decode.
    """
    # On Windows "git" and "code" are .exe/.cmd shims; hand subprocess the full
    # path which() resolved, or it may fail to find them.
    resolved = shutil.which(cmd[0])
    if resolved is None:
        return None
    cmd = [resolved] + cmd[1:]
    try:
        out = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    text = (out.stdout or out.stderr).strip()
    return text.splitlines()[0].strip() if text else None


def check_python():
    v = sys.version_info
    version = f"{v.major}.{v.minor}.{v.micro}"
    if v[:2] >= MIN_PYTHON:
        record(True, "Python", version)
    else:
        record(
            False,
            "Python",
            f"{version} -- too old",
            f"This course needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer. "
            "Install Miniforge: https://conda-forge.org/download/",
        )


def check_environment():
    """Are we running inside a conda environment, and is it the course one?"""
    if shutil.which("conda") is None:
        record(
            False,
            "conda",
            "not found on PATH",
            "Install Miniforge from https://conda-forge.org/download/, then open a "
            "new terminal (on Windows, the Miniforge Prompt).",
        )
        return

    env = os.environ.get("CONDA_DEFAULT_ENV")
    if env is None:
        record(
            False,
            "conda environment",
            "not active",
            "Open the Miniforge Prompt (Windows) or your terminal (macOS/Linux) "
            'and run "conda activate ece105".',
        )
    elif env == "base":
        record(
            False,
            "conda environment",
            'base -- use a course environment instead',
            'conda create -n ece105 python numpy matplotlib pandas scipy '
            'networkx pytest, then "conda activate ece105".',
        )
    else:
        record(True, "conda environment", env)


def check_packages():
    for name, purpose in PACKAGES:
        try:
            mod = importlib.import_module(name)
        except ImportError:
            record(False, name, f"MISSING ({purpose})", CONDA_FIX)
            continue
        except Exception as exc:  # installed, but broken
            record(False, name, f"installed but fails to import: {exc}", CONDA_FIX)
            continue
        version = getattr(mod, "__version__", "version unknown")
        record(True, name, version)


def check_git():
    if shutil.which("git") is None:
        record(
            False,
            "git",
            "not found on PATH",
            "Install Git from https://git-scm.com/downloads "
            "(on macOS you can also run: xcode-select --install).",
        )
        return

    version = run(["git", "--version"]) or "installed"
    record(True, "git", version)

    for key, label, example in [
        ("user.name", "git user.name", '"Ada Lovelace"'),
        ("user.email", "git user.email", '"abc123@drexel.edu"'),
    ]:
        # No --global here: read the effective value from whatever scope set it,
        # so a student who configured Git through VS Code or GitHub Desktop passes.
        value = run(["git", "config", key])
        if value:
            record(True, label, value)
        else:
            record(
                False,
                label,
                "not set",
                f"git config --global {key} {example}",
            )


def check_vscode():
    # VS Code ships the "code" launcher; on macOS it needs to be added to PATH
    # from inside VS Code (Command Palette -> "Shell Command: Install 'code'").
    if shutil.which("code") is None:
        record(
            False,
            "VS Code (code)",
            "not found on PATH",
            "Install VS Code (https://code.visualstudio.com/). On macOS, open the "
            "Command Palette and run \"Shell Command: Install 'code' command in PATH\". "
            "This one is optional -- VS Code still works if 'code' is not on PATH.",
        )
        return
    record(True, "VS Code (code)", run(["code", "--version"]) or "installed")


def main():
    print()
    print("ECE 105 (Fall 2026) -- Lab 0 environment check")
    print("=" * 62)

    check_python()
    check_environment()
    check_packages()
    check_git()
    check_vscode()

    width = max(len(label) for _, label, _, _ in results)
    for ok, label, detail, _ in results:
        mark = "ok  " if ok else "FAIL"
        print(f"  [{mark}] {label.ljust(width)}  {detail}")

    print("=" * 62)

    problems = [r for r in results if not r[0]]
    if not problems:
        print("All checks passed. You are ready for Lab 1. Show this to the TA.")
        print()
        return 0

    print(f"{len(problems)} item(s) need attention:\n")
    # Several missing packages share one fix -- list that fix once.
    fixes = {}
    for _, label, _, fix in problems:
        fixes.setdefault(fix, []).append(label)
    for fix, labels in fixes.items():
        print(f"  {', '.join(labels)}:")
        print(f"      {fix}\n")
    print("Fix these, then run this script again. Ask the TA if you get stuck.")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
