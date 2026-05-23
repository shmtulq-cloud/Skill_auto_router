from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from skill_router_common import default_out_dir


VALID_FIT = {"good", "partial", "wrong", "unknown"}
VALID_SEVERITY = {"info", "warning", "correction", "blocker"}


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def trace_file(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / "skill-trace.jsonl"


def infer_severity(
    fit: str,
    missed: list[str],
    overused: list[str],
    conflicts: list[str],
    correction_taken: bool,
) -> str:
    if correction_taken:
        return "correction"
    if fit == "wrong":
        return "correction"
    if conflicts:
        return "warning"
    if fit == "partial" or missed or overused:
        return "warning"
    return "info"


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a local skill-routing feedback event.")
    parser.add_argument("--task", required=True, help="Short task summary. Avoid private full prompts.")
    parser.add_argument("--recommended", default="", help="Comma-separated recommended skill names.")
    parser.add_argument("--used", default="", help="Comma-separated actually used skill names.")
    parser.add_argument("--missed", default="", help="Comma-separated skills that should have been used but were missed.")
    parser.add_argument("--overused", default="", help="Comma-separated skills that were used but probably unnecessary.")
    parser.add_argument("--fit", default="unknown", choices=sorted(VALID_FIT), help="Overall fit: good, partial, wrong, unknown.")
    parser.add_argument("--severity", choices=sorted(VALID_SEVERITY), help="User-facing severity. Defaults to an inferred value.")
    parser.add_argument("--notice-shown", action="store_true", help="Set when a visible notice was shown to the user.")
    parser.add_argument("--correction-taken", action="store_true", help="Set when the agent corrected the route or behavior during the task.")
    parser.add_argument("--conflicts", default="", help="Comma-separated skills or skill groups that conflicted.")
    parser.add_argument("--next-instruction-patch", default="", help="Short suggested project-instruction patch. Avoid private content.")
    parser.add_argument("--note", default="", help="Short non-sensitive note.")
    parser.add_argument("--out-dir", default=str(default_out_dir()))
    args = parser.parse_args()

    recommended = split_csv(args.recommended)
    used = split_csv(args.used)
    missed = split_csv(args.missed)
    overused = split_csv(args.overused)
    conflicts = split_csv(args.conflicts)
    severity = args.severity or infer_severity(args.fit, missed, overused, conflicts, args.correction_taken)

    event = {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "task": args.task.strip()[:500],
        "recommended": recommended,
        "used": used,
        "missed": missed,
        "overused": overused,
        "fit": args.fit,
        "severity": severity,
        "notice_shown": bool(args.notice_shown),
        "correction_taken": bool(args.correction_taken),
        "conflicts": conflicts,
        "next_instruction_patch": args.next_instruction_patch.strip()[:1000],
        "note": args.note.strip()[:500],
    }
    path = trace_file(Path(args.out_dir).expanduser().resolve())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"trace={path}")
    print(f"id={event['id']}")
    print(f"severity={severity}")
    if severity != "info" and not args.notice_shown:
        print("notice_needed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
