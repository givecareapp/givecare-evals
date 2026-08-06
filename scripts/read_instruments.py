#!/usr/bin/env python3
"""Emit the public instrument records from the Tools projection plus Evals overlay."""

from __future__ import annotations

import json

from validate import build_instrument_records


def main() -> None:
    print(json.dumps(build_instrument_records(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
