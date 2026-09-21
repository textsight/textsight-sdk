"""Command line: python -m textsight detect file.txt"""

import argparse
import json
import sys

from . import TextSight, TextSightError


def main() -> int:
    p = argparse.ArgumentParser(prog="textsight", description="TextSight AI detector / humanizer")
    p.add_argument("command", choices=["detect", "score", "rewrite"])
    p.add_argument("file", nargs="?", help="text file (default: stdin)")
    p.add_argument("--tone", default="conversational")
    p.add_argument("--strength", type=int, default=3)
    a = p.parse_args()
    text = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    try:
        ts = TextSight()
        if a.command == "rewrite":
            out = ts.rewrite(text, tone=a.tone, strength=a.strength)
        else:
            out = getattr(ts, a.command)(text)
    except (TextSightError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
