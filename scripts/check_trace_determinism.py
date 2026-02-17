#!/usr/bin/env python
"""Generate demo trace and fail if it differs from the golden fixture."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.determinism_ci import assert_no_trace_diff


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    generated = repo_root / "trace_demo.ndjson"
    golden = repo_root / "tests" / "golden" / "trace_demo.ndjson"
    if generated.exists():
        generated.unlink()

    subprocess.run(
        [sys.executable, "examples/trace_demo.py"],
        cwd=repo_root,
        check=True,
    )
    assert_no_trace_diff(golden, generated)
    print("Determinism check passed: generated trace matches golden fixture.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
