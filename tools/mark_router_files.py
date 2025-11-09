#!/usr/bin/env python3
import sys
from pathlib import Path

HEADER = "# pyright: reportUnusedFunction=none\n"


def should_mark(p: Path) -> bool:
    name = p.name.lower()
    parts = {s.lower() for s in p.parts}
    return (
        "routers" in parts
        or "routes" in parts
        or name.endswith(("_routes.py", "_router.py"))
    )


def main():
    bases = sys.argv[1:] or ["src", "services", "app"]
    for base in bases:
        b = Path(base)
        if not b.exists():
            continue
        for py in b.rglob("*.py"):
            if not should_mark(py):
                continue
            text = py.read_text(encoding="utf-8")
            if text.startswith(HEADER):
                continue
            py.write_text(HEADER + text, encoding="utf-8")
            print(f"[mark-router] added header to {py}")


if __name__ == "__main__":
    main()
