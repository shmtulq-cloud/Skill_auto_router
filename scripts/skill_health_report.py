from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from host_profiles import known_hosts, profiles_for
from onboarding_check import check_target
from skill_router_common import clean_skill_list, default_out_dir, load_known_skill_names, load_trace_events, router_identity


REVIEW_EVENT_TYPES = {"usage_review", "correction", "manual_feedback", "legacy_usage_review"}


def top(counter: Counter[str], limit: int = 10) -> list[dict[str, object]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def event_type(event: dict[str, object]) -> str:
    value = str(event.get("event_type", "") or "").strip()
    return value or "legacy_usage_review"


def route_id(event: dict[str, object]) -> str:
    return str(event.get("route_id", "") or "").strip()


def coverage_status(route_decisions: list[dict[str, object]], reviews: list[dict[str, object]], paired_count: int) -> str:
    if not route_decisions and not reviews:
        return "empty"
    if not route_decisions:
        return "feedback_only"
    if not reviews:
        return "decisions_without_reviews"
    if paired_count == len(route_decisions) == len(reviews) and paired_count < 3:
        return "too_few_paired_events"
    if paired_count < max(3, int(len(route_decisions) * 0.3)):
        return "decision_review_gap"
    return "tracked"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an observability-first health report for skill routing traces.")
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

    route_decisions = [event for event in events if event_type(event) == "route_decision"]
    reviews = [event for event in events if event_type(event) in REVIEW_EVENT_TYPES]
    legacy_reviews = [event for event in reviews if event_type(event) == "legacy_usage_review"]

    decision_ids = {route_id(event) for event in route_decisions if route_id(event)}
    review_ids = {route_id(event) for event in reviews if route_id(event)}
    paired_ids = decision_ids & review_ids
    unreviewed_ids = decision_ids - review_ids
    orphan_review_ids = review_ids - decision_ids

    event_types = Counter(event_type(event) for event in events)
    missed = Counter()
    overused = Counter()
    conflicts = Counter()
    conflict_clusters = Counter()
    severity_counts = Counter()
    route_levels = Counter()
    patch_suggestions = Counter()
    data_quality = Counter()
    notices_required = 0
    notices_missing = 0
    corrections_taken = 0
    recent_attention: list[str] = []

    for event in reviews:
        normalization = event.get("normalization")
        if isinstance(normalization, dict):
            for notes in normalization.values():
                if isinstance(notes, list):
                    data_quality.update(str(note) for note in notes)

        task = str(event.get("task", "")).strip()
        severity = str(event.get("severity", "info") or "info")
        severity_counts[severity] += 1
        route_levels[str(event.get("route_level", "unknown") or "unknown")] += 1

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
    if coverage_status(route_decisions, reviews, len(paired_ids)) != "tracked":
        instruction_recommendations.append(
            "Improve trace coverage: record route decisions with `route_task.py --trace`, then record completion reviews with the same `--route-id`."
        )
    for skill, count in missed.most_common():
        if count >= args.threshold:
            instruction_recommendations.append(f"Add a default route hint for `{skill}` because it was missed {count} times in reviews.")
    for skill, count in overused.most_common():
        if count >= args.threshold:
            instruction_recommendations.append(f"Add a caution note for `{skill}` because it was overused {count} times in reviews.")
    for cluster, count in conflict_clusters.most_common():
        if count >= 2:
            instruction_recommendations.append(f"Add a conflict-order rule for `{cluster}` because this conflict appeared {count} times.")
    for patch, count in patch_suggestions.most_common():
        if count >= 1:
            instruction_recommendations.append(f"Suggested instruction patch ({count}x): {patch}")

    repeated_missed = any(count >= args.threshold for count in missed.values())
    repeated_overused = any(count >= args.threshold for count in overused.values())
    repeated_conflicts = any(count >= args.threshold for count in conflicts.values())
    repeated_conflict_clusters = any(count >= 2 for count in conflict_clusters.values())
    observability = coverage_status(route_decisions, reviews, len(paired_ids))

    health = "good"
    if (
        observability != "tracked"
        or len(reviews) < 30
        or invalid_lines
    ):
        health = "insufficient_data"
    if (
        notices_missing
        or onboarding_missing
        or repeated_missed
        or repeated_overused
        or repeated_conflicts
        or repeated_conflict_clusters
    ):
        health = "needs_attention"
    if severity_counts.get("blocker", 0):
        health = "blocked"

    confidence = "low"
    if observability == "tracked" and len(reviews) >= 30:
        confidence = "medium"
    if observability == "tracked" and len(reviews) >= 100:
        confidence = "high"

    coverage = {
        "observability": observability,
        "total_events": len(events),
        "route_decisions": len(route_decisions),
        "usage_reviews": len(reviews),
        "legacy_review_only_events": len(legacy_reviews),
        "paired_route_ids": len(paired_ids),
        "unreviewed_route_decisions": len(unreviewed_ids),
        "reviews_without_matching_decision": len(orphan_review_ids),
        "decisions_without_route_id": sum(1 for event in route_decisions if not route_id(event)),
        "reviews_without_route_id": sum(1 for event in reviews if not route_id(event)),
    }

    report = {
        "trace_file": str(trace_path),
        "router_identity": router_identity(),
        "health": health,
        "confidence": confidence,
        "coverage": coverage,
        "event_types": dict(event_types),
        "invalid_json_lines": invalid_lines,
        "severity_counts": dict(severity_counts),
        "route_levels": dict(route_levels),
        "attention_thresholds": {
            "skill_count_threshold": args.threshold,
            "conflict_cluster_threshold": 2,
        },
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
        "# Skill Routing Observability Report",
        "",
        f"Trace file: `{trace_path}`",
        f"Router identity: `{router_identity()['canonical_skill_id']}` ({router_identity()['display_name']})",
        f"Health: `{health}`",
        f"Confidence: `{confidence}`",
        f"Observability: `{observability}`",
        "",
        "> This report is a routing observability diagnostic. It cannot count total skill invocations unless route decisions and completion reviews are both recorded.",
        "",
        "## What This Report Can Say",
        "",
        "- It can analyze recorded route decisions, completion reviews, misses, overuse, conflicts, and onboarding status.",
        "- It can identify repeated recorded problems after enough paired data exists.",
        "- It cannot infer real skill usage rate, total token usage, or all tasks performed outside the trace.",
        "",
        "## Trace Coverage",
        "",
        f"- Total trace events: {coverage['total_events']}",
        f"- Route decisions: {coverage['route_decisions']}",
        f"- Completion/feedback reviews: {coverage['usage_reviews']}",
        f"- Paired route ids: {coverage['paired_route_ids']}",
        f"- Unreviewed route decisions: {coverage['unreviewed_route_decisions']}",
        f"- Reviews without matching decision: {coverage['reviews_without_matching_decision']}",
        f"- Legacy review-only events: {coverage['legacy_review_only_events']}",
        f"- Invalid JSONL lines: {len(invalid_lines)}",
        "",
        "## Event Types",
        "",
    ]
    lines.extend([f"- `{name}`: {count}" for name, count in event_types.most_common()] or ["- none"])
    lines.extend([
        "",
        "## Notice Coverage (Review Events Only)",
        "",
        f"- Required: {notices_required}",
        f"- Shown: {notices_required - notices_missing}",
        f"- Missing: {notices_missing}",
        f"- Corrections taken: {corrections_taken}",
        "",
        "## Repeated Misses (Review Events Only)",
        "",
    ])
    lines.extend([f"- `{item['name']}`: {item['count']}" for item in report["repeated_missed"]] or ["- none"])
    lines.extend(["", "## Overuse Patterns (Review Events Only)", ""])
    lines.extend([f"- `{item['name']}`: {item['count']}" for item in report["repeated_overused"]] or ["- none"])
    lines.extend(["", "## Route Levels (Review Events Only)", ""])
    lines.extend([f"- `{name}`: {count}" for name, count in route_levels.most_common()] or ["- none"])
    lines.extend(["", "## Conflict Clusters (Review Events Only)", ""])
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
        print(f"health={health}")
        print(f"confidence={confidence}")
        print(f"observability={observability}")
        print(f"route_decisions={len(route_decisions)}")
        print(f"usage_reviews={len(reviews)}")
        print(f"paired_route_ids={len(paired_ids)}")
        print(f"report={report_path}")
        if instruction_recommendations:
            print(f"instruction_recommendations={len(instruction_recommendations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
