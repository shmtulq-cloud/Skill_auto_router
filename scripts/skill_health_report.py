from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from host_profiles import known_hosts, profiles_for
from onboarding_check import check_target
from skill_router_common import clean_skill_list, default_out_dir, load_known_skill_names, load_trace_events, router_identity


def top(counter: Counter[str], limit: int = 10) -> list[dict[str, object]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a health report for skill-routing feedback.")
    parser.add_argument("--out-dir", default=str(default_out_dir()))
    parser.add_argument("--project", default=".", help="Project folder used for onboarding status checks.")
    parser.add_argument("--host", default="codex", choices=known_hosts() + ["all"], help="Host profile to check for onboarding.")
    parser.add_argument("--scope", default="project", choices=["project", "global", "both"], help="Instruction scope for onboarding checks.")
    parser.add_argument("--threshold", type=int, default=3, help="Count that triggers instruction-update recommendations.")
    parser.add_argument("--skip-onboarding", action="store_true", help="Do not merge onboarding status into the health report.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    trace_path = out_dir / "skill-trace.jsonl"
    events, invalid_lines = load_trace_events(trace_path)
    known_names = load_known_skill_names(out_dir)

    missed = Counter()
    overused = Counter()
    conflicts = Counter()
    conflict_clusters = Counter()
    severity_counts = Counter()
    patch_suggestions = Counter()
    data_quality = Counter()
    notices_required = 0
    notices_missing = 0
    corrections_taken = 0

    recent_attention: list[str] = []

    for event in events:
        normalization = event.get("normalization")
        if isinstance(normalization, dict):
            for notes in normalization.values():
                if isinstance(notes, list):
                    data_quality.update(str(note) for note in notes)

        task = str(event.get("task", "")).strip()
        severity = str(event.get("severity", "info"))
        severity_counts[severity] += 1

        event_missed, notes = clean_skill_list(event.get("missed"), known_names)
        data_quality.update(notes)
        event_overused, notes = clean_skill_list(event.get("overused"), known_names)
        data_quality.update(notes)
        event_conflicts, notes = clean_skill_list(event.get("conflicts"), known_names)
        data_quality.update(notes)
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

    onboarding_targets: list[dict[str, object]] = []
    onboarding_missing: list[dict[str, object]] = []
    if not args.skip_onboarding:
        project_root = Path(args.project).expanduser().resolve()
        for profile in profiles_for(args.host):
            if args.scope in {"project", "both"}:
                onboarding_targets.append(check_target(profile.id, "project", project_root))
            if args.scope in {"global", "both"}:
                onboarding_targets.append(check_target(profile.id, "global", project_root))
        onboarding_missing = [target for target in onboarding_targets if not bool(target["configured"])]

    instruction_recommendations = []
    for target in onboarding_missing:
        instruction_recommendations.append(
            f"Add skill-routing onboarding to `{target['instruction']}` for {target['host_name']} ({target['label']} scope)."
        )
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
    if notices_missing or missed or conflicts or invalid_lines or onboarding_missing:
        health = "needs_attention"
    if severity_counts.get("blocker", 0):
        health = "blocked"
    confidence = "medium"
    if len(events) < 30:
        confidence = "low"
    if len(events) >= 100:
        confidence = "high"

    report = {
        "trace_file": str(trace_path),
        "router_identity": router_identity(),
        "events": len(events),
        "invalid_json_lines": invalid_lines,
        "health": health,
        "confidence": confidence,
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
        "data_quality": top(data_quality),
        "onboarding": {
            "targets": onboarding_targets,
            "missing": onboarding_missing,
        },
        "instruction_recommendations": instruction_recommendations,
        "recent_attention": recent_attention[-10:],
    }

    report_path = out_dir / "skill-health-report.md"
    lines = [
        "# Skill Routing Health Report",
        "",
        f"Trace file: `{trace_path}`",
        f"Router identity: `{router_identity()['canonical_skill_id']}` ({router_identity()['display_name']})",
        f"Events: {len(events)}",
        f"Invalid JSONL lines: {len(invalid_lines)}",
        f"Health: `{health}`",
        f"Confidence: `{confidence}`",
        "",
        "> Confidence is about sample size and data quality. This report is a routing diagnostic, not a statistically valid accuracy score.",
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
    lines.extend(["", "## Data Quality", ""])
    if invalid_lines:
        lines.append(f"- invalid JSONL lines: {len(invalid_lines)}")
        for item in invalid_lines[:5]:
            lines.append(f"  - line {item['line']}: {item['error']}")
    if report["data_quality"]:
        lines.extend([f"- `{item['name']}`: {item['count']}" for item in report["data_quality"]])
    if not invalid_lines and not report["data_quality"]:
        lines.append("- none")
    lines.extend(["", "## Onboarding Status", ""])
    if not onboarding_targets:
        lines.append("- skipped")
    else:
        for target in onboarding_targets:
            status = "configured" if target["configured"] else "missing"
            lines.append(f"- `{target['host']}` {target['label']}: {status} - `{target['instruction']}`")
    lines.extend(["", "## Instruction Recommendations", ""])
    lines.extend([f"- {item}" for item in instruction_recommendations] or ["- none"])
    lines.extend(["", "## Recent Attention Items", ""])
    lines.extend([f"- {item}" for item in recent_attention[-10:]] or ["- none"])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"events={len(events)}")
        if invalid_lines:
            print(f"invalid_json_lines={len(invalid_lines)}")
        print(f"health={health}")
        print(f"confidence={confidence}")
        print(f"report={report_path}")
        if notices_missing:
            print(f"missing_notices={notices_missing}")
        if instruction_recommendations:
            print(f"instruction_recommendations={len(instruction_recommendations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
