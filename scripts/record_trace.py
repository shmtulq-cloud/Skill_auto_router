from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from skill_router_common import default_out_dir


VALID_FIT = {"good", "partial", "wrong", "unknown"}


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def trace_file(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / "skill-trace.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a local skill-routing feedback event.")
    parser.add_argument("--task", required=True, help="Short task summary. Avoid private full prompts.")
    parser.add_argument("--recommended", default="", help="Comma-separated recommended skill names.")
    parser.add_argument("--used", default="", help="Comma-separated actually used skill names.")
    parser.add_argument("--missed", default="", help="Comma-separated skills that should have been used but were missed.")
    parser.add_argument("--overused", default="", help="Comma-separated skills that were used but probably unnecessary.")
    parser.add_argument("--fit", default="unknown", choices=sorted(VALID_FIT), help="Overall fit: good, partial, wrong, unknown.")
    parser.add_argument("--note", default="", help="Short non-sensitive note.")
    parser.add_argument("--out-dir", default=str(default_out_dir()))
    args = parser.parse_args()

    event = {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "task": args.task.strip()[:500],
        "recommended": split_csv(args.recommended),
        "used": split_csv(args.used),
        "missed": split_csv(args.missed),
        "overused": split_csv(args.overused),
        "fit": args.fit,
        "note": args.note.strip()[:500],
    }
    path = trace_file(Path(args.out_dir).expanduser().resolve())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"trace={path}")
    print(f"id={event['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
