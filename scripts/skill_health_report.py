from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from skill_router_common import default_out_dir


def load_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def as_list(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def top(counter: Counter[str], limit: int = 10) -> list[dict[str, object]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a health report for skill-routing feedback.")
    parser.add_argument("--out-dir", default=str(default_out_dir()))
    parser.add_argument("--threshold", type=int, default=3, help="Count that triggers instruction-update recommendations.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    trace_path = out_dir / "skill-trace.jsonl"
    events = load_events(trace_path)

    missed = Counter()
    overused = Counter()
    conflicts = Counter()
    conflict_clusters = Counter()
    severity_counts = Counter()
    patch_suggestions = Counter()
    notices_required = 0
    notices_missing = 0
    corrections_taken = 0

    recent_attention: list[str] = []

    for event in events:
        task = str(event.get("task", "")).strip()
        severity = str(event.get("severity", "info"))
        severity_counts[severity] += 1

        event_missed = as_list(event.get("missed"))
        event_overused = as_list(event.get("overused"))
        event_conflicts = as_list(event.get("conflicts"))
        missed.update(event_missed)
        overused.update(event_overused)
        conflicts.update(event_conflicts)

        if len(event_conflicts) > 1:
            conflict_clusters[", ".join(sorted(event_conflicts))] += 1
        if severity != "info":
            notices_required += 1
            if not bool(event.get("notice_shown", False)):
                notices_missing += 1
            if task:
                recent_attention.append(f"{severity}: {task[:120]}")
        if bool(event.get("correction_taken", False)):
            corrections_taken += 1
        patch = str(event.get("next_instruction_patch", "")).strip()
        if patch:
            patch_suggestions[patch] += 1

    instruction_recommendations = []
    for skill, count in missed.most_common():
        if count >= args.threshold:
            instruction_recommendations.append(
                f"Add a default route hint for `{skill}` because it was missed {count} times."
            )
    for skill, count in overused.most_common():
        if count >= args.threshold:
            instruction_recommendations.append(
                f"Add a caution note for `{skill}` because it was overused {count} times."
            )
    for cluster, count in conflict_clusters.most_common():
        if count >= 2:
            instruction_recommendations.append(
                f"Add a conflict-order rule for `{cluster}` because this conflict appeared {count} times."
            )
    for patch, count in patch_suggestions.most_common():
        if count >= 1:
            instruction_recommendations.append(f"Suggested instruction patch ({count}x): {patch}")

    health = "good"
    if notices_missing or missed or conflicts:
        health = "needs_attention"
    if severity_counts.get("blocker", 0):
        health = "blocked"

    report = {
        "trace_file": str(trace_path),
        "events": len(events),
        "health": health,
        "severity_counts": dict(severity_counts),
        "notice_coverage": {
            "required": notices_required,
            "missing": notices_missing,
            "shown": notices_required - notices_missing,
        },
        "corrections_taken": corrections_taken,
        "repeated_missed": top(missed),
        "repeated_overused": top(overused),
        "conflicts": top(conflicts),
        "conflict_clusters": top(conflict_clusters),
        "instruction_recommendations": instruction_recommendations,
        "recent_attention": recent_attention[-10:],
    }

    report_path = out_dir / "skill-health-report.md"
    lines = [
        "# Skill Routing Health Report",
        "",
        f"Trace file: `{trace_path}`",
        f"Events: {len(events)}",
        f"Health: `{health}`",
        "",
        "## Notice Coverage",
        "",
        f"- Required: {notices_required}",
        f"- Shown: {notices_required - notices_missing}",
        f"- Missing: {notices_missing}",
        f"- Corrections taken: {corrections_taken}",
        "",
        "## Repeated Misses",
        "",
    ]
    lines.extend([f"- `{item['name']}`: {item['count']}" for item in report["repeated_missed"]] or ["- none"])
    lines.extend(["", "## Overuse Patterns", ""])
    lines.extend([f"- `{item['name']}`: {item['count']}" for item in report["repeated_overused"]] or ["- none"])
    lines.extend(["", "## Conflict Clusters", ""])
    lines.extend([f"- `{item['name']}`: {item['count']}" for item in report["conflict_clusters"]] or ["- none"])
    lines.extend(["", "## Instruction Recommendations", ""])
    lines.extend([f"- {item}" for item in instruction_recommendations] or ["- none"])
    lines.extend(["", "## Recent Attention Items", ""])
    lines.extend([f"- {item}" for item in recent_attention[-10:]] or ["- none"])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"events={len(events)}")
        print(f"health={health}")
        print(f"report={report_path}")
        if notices_missing:
            print(f"missing_notices={notices_missing}")
        if instruction_recommendations:
            print(f"instruction_recommendations={len(instruction_recommendations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
