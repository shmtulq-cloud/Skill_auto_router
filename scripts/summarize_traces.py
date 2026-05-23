from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize local skill-routing feedback traces.")
    parser.add_argument("--out-dir", default=str(default_out_dir()))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.out_dir).expanduser().resolve() / "skill-trace.jsonl"
    events = load_events(path)

    fits = Counter(str(event.get("fit", "unknown")) for event in events)
    recommended = Counter()
    used = Counter()
    missed = Counter()
    overused = Counter()
    severities = Counter()
    conflicts = Counter()
    conflict_clusters = Counter()
    recommended_but_unused = Counter()
    used_without_recommendation = Counter()
    notices_required = 0
    notices_shown = 0
    corrections_taken = 0

    pair_stats: dict[str, Counter[str]] = defaultdict(Counter)

    for event in events:
        rec = set(as_list(event.get("recommended")))
        use = set(as_list(event.get("used")))
        miss = set(as_list(event.get("missed")))
        over = set(as_list(event.get("overused")))
        conflict = set(as_list(event.get("conflicts")))
        severity = str(event.get("severity", "info"))
        recommended.update(rec)
        used.update(use)
        missed.update(miss)
        overused.update(over)
        severities[severity] += 1
        conflicts.update(conflict)
        if len(conflict) > 1:
            conflict_clusters[", ".join(sorted(conflict))] += 1
        if severity != "info":
            notices_required += 1
            if bool(event.get("notice_shown", False)):
                notices_shown += 1
        if bool(event.get("correction_taken", False)):
            corrections_taken += 1
        recommended_but_unused.update(rec - use)
        used_without_recommendation.update(use - rec)
        for skill in rec | use | miss | over | conflict:
            if skill in rec:
                pair_stats[skill]["recommended"] += 1
            if skill in use:
                pair_stats[skill]["used"] += 1
            if skill in miss:
                pair_stats[skill]["missed"] += 1
            if skill in over:
                pair_stats[skill]["overused"] += 1
            if skill in conflict:
                pair_stats[skill]["conflict"] += 1

    summary = {
        "trace_file": str(path),
        "events": len(events),
        "fit_counts": dict(fits),
        "severity_counts": dict(severities),
        "notice_coverage": {
            "required": notices_required,
            "shown": notices_shown,
            "missing": notices_required - notices_shown,
        },
        "corrections_taken": corrections_taken,
        "top_recommended": recommended.most_common(20),
        "top_used": used.most_common(20),
        "top_missed": missed.most_common(20),
        "top_overused": overused.most_common(20),
        "top_conflicts": conflicts.most_common(20),
        "conflict_clusters": conflict_clusters.most_common(20),
        "recommended_but_unused": recommended_but_unused.most_common(20),
        "used_without_recommendation": used_without_recommendation.most_common(20),
        "per_skill": {skill: dict(stats) for skill, stats in sorted(pair_stats.items())},
    }

    report_path = Path(args.out_dir).expanduser().resolve() / "skill-trace-summary.md"
    lines = [
        "# Skill Routing Feedback Summary",
        "",
        f"Trace file: `{path}`",
        f"Events: {len(events)}",
        "",
        "## Fit Counts",
        "",
    ]
    for fit, count in fits.most_common():
        lines.append(f"- `{fit}`: {count}")
    lines.extend(["", "## Severity Counts", ""])
    if not severities:
        lines.append("- none")
    else:
        for severity, count in severities.most_common():
            lines.append(f"- `{severity}`: {count}")
    lines.extend([
        "",
        "## Notice Coverage",
        "",
        f"- Required: {notices_required}",
        f"- Shown: {notices_shown}",
        f"- Missing: {notices_required - notices_shown}",
        f"- Corrections taken: {corrections_taken}",
    ])
    for title, counter in [
        ("Top Recommended", recommended),
        ("Top Used", used),
        ("Top Missed", missed),
        ("Top Overused", overused),
        ("Top Conflicts", conflicts),
        ("Conflict Clusters", conflict_clusters),
        ("Recommended But Unused", recommended_but_unused),
        ("Used Without Recommendation", used_without_recommendation),
    ]:
        lines.extend(["", f"## {title}", ""])
        if not counter:
            lines.append("- none")
        else:
            for skill, count in counter.most_common(20):
                lines.append(f"- `{skill}`: {count}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"events={len(events)}")
        print(f"summary={report_path}")
        print(f"trace={path}")
        if missed:
            print("top_missed=" + ", ".join(f"{skill}:{count}" for skill, count in missed.most_common(5)))
        if overused:
            print("top_overused=" + ", ".join(f"{skill}:{count}" for skill, count in overused.most_common(5)))
        if notices_required - notices_shown:
            print(f"missing_notices={notices_required - notices_shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
