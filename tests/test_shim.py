"""Broken-precondition tests for ``bin/tmux-fleet``.

The shim is bootstrap only. Its whole job is to fail LOUD with an exact remedy
when the environment it needs is broken -- a missing pack-private venv, an
absent ``tmux``, or a venv that is present but from which the tool cannot be
imported. These tests prove each refusal path, and prove the one exemption that
keeps the tool's own contract intact: ``--help`` is NOT blocked by the tmux
gate (``doctor`` and ``--help`` must run in a tmux-less environment).

None of this requires the real smart tool to be installed: the refusals happen
before (or instead of) a successful tool import, so a real ``python3`` standing
in for the venv interpreter is enough to exercise every path.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIM_SRC = REPO_ROOT / "bin" / "tmux-fleet"

# Every external command the shim invokes before it would exec the tool.
# (``pwd``/``command``/``test`` are sh builtins; these are the externals.)
_SHIM_EXTERNALS = ("readlink", "dirname", "cat", "env")


def _make_pack(tmp_path: Path) -> Path:
    """A throwaway pack dir with a real copy of the shim at ``bin/tmux-fleet``."""
    pack = tmp_path / "pack"
    (pack / "bin").mkdir(parents=True)
    dst = pack / "bin" / "tmux-fleet"
    shutil.copy2(SHIM_SRC, dst)
    dst.chmod(0o755)
    return pack


def _make_fakebin(tmp_path: Path, *, tmux: bool) -> Path:
    """A PATH dir with the shim's coreutils, and tmux present or absent.

    Isolating PATH is how we control ``command -v tmux`` deterministically:
    the fakebin carries every external the shim needs, and ``tmux`` only when
    asked for.
    """
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    for name in _SHIM_EXTERNALS:
        real = shutil.which(name)
        assert real, f"test host is missing required coreutil {name!r}"
        os.symlink(real, fakebin / name)
    if tmux:
        # A stub is enough: the shim only probes presence (`command -v tmux`),
        # it never executes tmux itself.
        stub = fakebin / "tmux"
        stub.write_text("#!/bin/sh\nexit 0\n")
        stub.chmod(0o755)
    return fakebin


def _install_fake_venv(pack: Path, *, python: bool) -> None:
    """Create ``.venv/bin/``; optionally an interpreter symlinked to real python3."""
    venv_bin = pack / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    if python:
        os.symlink(sys.executable, venv_bin / "python")


def _run(pack: Path, fakebin: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(pack / "bin" / "tmux-fleet"), *args],
        capture_output=True,
        text=True,
        env={"PATH": str(fakebin)},
    )


def test_shim_is_executable_and_valid_posix_sh() -> None:
    assert os.access(SHIM_SRC, os.X_OK), "bin/tmux-fleet must have the exec bit set"
    # `sh -n` parses without executing -- a syntax error here is a broken shim.
    proc = subprocess.run(["sh", "-n", str(SHIM_SRC)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_missing_venv_refuses_with_rebuild_remedy(tmp_path: Path) -> None:
    pack = _make_pack(tmp_path)  # no .venv/
    fakebin = _make_fakebin(tmp_path, tmux=True)

    proc = _run(pack, fakebin, "sessions")

    assert proc.returncode != 0
    assert proc.returncode == 69
    assert "private virtualenv is missing" in proc.stderr
    # The exact remedy command, copy-pasteable:
    assert "uv venv" in proc.stderr
    assert "uv pip install --python" in proc.stderr
    # It must NOT silently provision itself:
    assert "will NOT build one mid-turn" in proc.stderr


def test_tmux_absent_refuses_work_verb_with_install_remedy(tmp_path: Path) -> None:
    pack = _make_pack(tmp_path)
    _install_fake_venv(pack, python=True)  # venv present, so the venv gate passes
    fakebin = _make_fakebin(tmp_path, tmux=False)

    proc = _run(pack, fakebin, "sessions")

    assert proc.returncode == 69
    assert "`tmux` is not on PATH" in proc.stderr
    assert "sudo apt-get install tmux" in proc.stderr
    # The venv interpreter is never executed when the tmux gate fires, so this
    # is the tmux remedy, not the import remedy:
    assert "failed to import" not in proc.stderr


def test_help_is_not_blocked_by_the_tmux_gate(tmp_path: Path) -> None:
    # --help must work in a tmux-less environment (cli.v1 rule 1). With tmux
    # absent, the shim must NOT emit the tmux remedy for --help; it proceeds to
    # the interpreter, where (a bare python3 standing in for the venv) the tool
    # import fails and we get the IMPORT remedy instead -- proving the gate was
    # bypassed for --help.
    pack = _make_pack(tmp_path)
    _install_fake_venv(pack, python=True)
    fakebin = _make_fakebin(tmp_path, tmux=False)

    proc = _run(pack, fakebin, "--help")

    assert "`tmux` is not on PATH" not in proc.stderr, (
        "the tmux gate must not block --help"
    )
    # It got past the gate to the import guard:
    assert "failed to import" in proc.stderr


def test_broken_venv_import_refuses_with_rebuild_remedy(tmp_path: Path) -> None:
    # venv present + tmux present, but the interpreter cannot import the tool
    # (a real python3 with no tmux_fleet installed stands in for a broken venv).
    pack = _make_pack(tmp_path)
    _install_fake_venv(pack, python=True)
    fakebin = _make_fakebin(tmp_path, tmux=True)

    proc = _run(pack, fakebin, "sessions")

    assert proc.returncode == 70
    assert "failed to import" in proc.stderr
    assert "rebuild it" in proc.stderr
    assert "uv pip install --python" in proc.stderr
    # The underlying cause is surfaced, not swallowed:
    assert "underlying error:" in proc.stderr


@pytest.mark.parametrize("verb", ["sessions", "read", "send", "create", "attention"])
def test_missing_venv_refuses_every_work_verb(tmp_path: Path, verb: str) -> None:
    # Whatever the verb, a missing venv is a refusal -- the shim never reaches
    # the tool with a broken environment.
    pack = _make_pack(tmp_path)
    fakebin = _make_fakebin(tmp_path, tmux=True)

    proc = _run(pack, fakebin, verb)

    assert proc.returncode == 69
    assert "private virtualenv is missing" in proc.stderr
