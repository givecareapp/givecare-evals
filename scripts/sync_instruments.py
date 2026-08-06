#!/usr/bin/env python3
"""Materialize one exact verified gc-tools Hound instrument projection."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
GIVECARE_ROOT = ROOT.parent
TOOLS_ROOT = GIVECARE_ROOT / "gc-tools"
PROTOCOL_CLI = GIVECARE_ROOT / "scripts" / "givecare_protocol.py"
TARGET = ROOT / "data" / "instruments.json"

sys.path.insert(0, str(SCRIPTS))
from validate import resolve_verified_tools_projection  # noqa: E402


class SyncError(Exception):
    pass


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def materialize(
    *,
    run_dir: Path,
    tools_root: Path = TOOLS_ROOT,
    protocol_cli: Path = PROTOCOL_CLI,
    target: Path = TARGET,
) -> bool:
    """Write exact verified bytes to the fixed consumer path. Return whether changed."""
    _run, _source, content = resolve_verified_tools_projection(
        tools_root=tools_root,
        run_dir=run_dir,
        protocol_cli=protocol_cli,
    )
    if target.is_symlink() or target.parent.is_symlink():
        raise SyncError("instrument materialization path must not contain a symlink")
    if target.exists() and not target.is_file():
        raise SyncError("instrument materialization target must be a regular file")
    if target.is_file() and target.read_bytes() == content:
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.sync-", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, target)
        _fsync_directory(target.parent)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sync the exact verified gc-tools instrument projection."
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    changed = materialize(run_dir=args.run_dir)
    print("updated data/instruments.json" if changed else "data/instruments.json is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
