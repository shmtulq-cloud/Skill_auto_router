from __future__ import annotations

import argparse
from pathlib import Path
import json

from host_profiles import known_hosts, profiles_for, skill_roots_for
from skill_router_common import (
    ROUTER_CANONICAL_ID,
    SKILL_ALIASES,
    default_out_dir,
    default_skills_dir,
    load_map,
    normalize_skill_item,
    scan_skills,
    tokenize,
    write_map,
)


VERIFICATION_HINTS = {
    "verification-loop",
    "verification-before-completion",
    "systematic-debugging",
    "tdd-workflow",
    "security-review",
}

CURATED_BOOSTS = [
    (ROUTER_CANONICAL_ID, ["skill", "auto", "router"], 64, "curated: public project name"),
    (ROUTER_CANONICAL_ID, ["skill_auto_router"], 64, "curated: repository slug"),
    (ROUTER_CANONICAL_ID, ["skills_auto_router"], 60, "curated: router alias"),
    (ROUTER_CANONICAL_ID, ["skill_auto_router"], 60, "curated: router alias"),
    (ROUTER_CANONICAL_ID, ["skill-auto-router"], 60, "curated: router alias"),
    (ROUTER_CANONICAL_ID, ["skills-auto-router"], 60, "curated: router alias"),
    (ROUTER_CANONICAL_ID, ["skill", "router"], 42, "curated: skill routing"),
    (ROUTER_CANONICAL_ID, ["auto", "router"], 42, "curated: auto skill router"),
    (ROUTER_CANONICAL_ID, ["健康报告"], 40, "curated: router health report"),
    (ROUTER_CANONICAL_ID, ["健康状态"], 40, "curated: router health status"),
    (ROUTER_CANONICAL_ID, ["路由健康"], 40, "curated: router health"),
    (ROUTER_CANONICAL_ID, ["技能路由"], 40, "curated: skill routing"),
    ("market-research", ["market", "research"], 28, "curated: market research"),
    ("deep-research", ["research"], 18, "curated: deep/cited research"),
    ("deep-research", ["cited"], 12, "curated: citations requested"),
    ("research-ops", ["source"], 16, "curated: evidence/source discipline"),
    ("research-ops", ["cited"], 14, "curated: evidence/source discipline"),
    ("spec-driven-vibe-coding", ["spec"], 24, "curated: spec-driven work"),
    ("spec-driven-vibe-coding", ["spec-in"], 30, "curated: spec-in work"),
    ("product-lens", ["product"], 12, "curated: product framing"),
    ("product-capability", ["product"], 12, "curated: product capability"),
    ("creative-director", ["design"], 14, "curated: visual direction"),
    ("design-brief", ["design"], 12, "curated: design brief"),
    ("artifacts-builder", ["visual"], 10, "curated: artifact building"),
    ("wechat-director", ["公众号"], 36, "curated: WeChat visual direction"),
    ("wechat-director", ["配图"], 34, "curated: WeChat article illustrations"),
    ("wechat-director", ["生图"], 28, "curated: image generation for WeChat visuals"),
    ("wechat-director", ["插图"], 24, "curated: article illustrations"),
    ("wechat-director", ["封面"], 18, "curated: article cover visual"),
    ("imagegen", ["生图"], 24, "curated: bitmap image generation"),
    ("imagegen", ["图片"], 18, "curated: bitmap image generation"),
    ("imagegen", ["插图"], 14, "curated: illustration generation"),
    ("poster-hero", ["封面"], 18, "curated: cover/poster image"),
    ("verification-loop", ["verify"], 16, "curated: verification"),
    ("verification-loop", ["complete"], 10, "curated: completion check"),
    ("verification-loop", ["report"], 8, "curated: report verification"),
    ("verification-loop", ["spec"], 8, "curated: spec verification"),
    ("systematic-debugging", ["bug"], 22, "curated: debugging"),
    ("tdd-workflow", ["test"], 16, "curated: testing/TDD"),
    ("keep-codex-fast", ["codex", "slow"], 30, "curated: Codex maintenance"),
    ("follow-builders", ["digest"], 24, "curated: builder digest"),
    ("follow-builders", ["track"], 12, "curated: information tracking"),
]

QUERY_EXPANSIONS = [
    (
        ["代码索引"],
        ["source", "asset", "audit", "file", "module", "repository", "codebase", "index", "map"],
    ),
    (
        ["知识图谱"],
        ["knowledge", "graph", "memory", "mcp", "relations", "relationship", "retrieval", "semantic"],
    ),
    (
        ["全量阅读"],
        ["scan", "audit", "summary", "map", "overview", "onboarding", "recall", "memory"],
    ),
    (
        ["全量扫描"],
        ["scan", "audit", "summary", "map", "overview", "onboarding", "recall", "memory"],
    ),
    (
        ["模块关系"],
        ["module", "architecture", "dependency", "relationship", "map", "graph"],
    ),
    (
        ["依赖图"],
        ["dependency", "graph", "architecture", "module", "map"],
    ),
    (
        ["调用图"],
        ["call", "graph", "dependency", "architecture", "module", "map"],
    ),
    (
        ["接手项目"],
        ["onboarding", "unfamiliar", "codebase", "architecture", "entry", "conventions"],
    ),
    (
        ["理解代码"],
        ["onboarding", "codebase", "architecture", "entry", "map", "walkthrough"],
    ),
    (
        ["项目记忆"],
        ["memory", "notes", "save", "recall", "knowledge", "project", "context"],
    ),
    (
        ["架构记忆"],
        ["architecture", "memory", "notes", "knowledge", "context", "decision"],
    ),
    (
        ["踩坑记录"],
        ["notes", "gotchas", "recall", "remember", "save", "knowledge"],
    ),
    (
        ["增量审查"],
        ["review", "diff", "changes", "incremental", "verification", "security", "tests"],
    ),
    (
        ["增量审核"],
        ["review", "diff", "changes", "incremental", "verification", "security", "tests"],
    ),
]


def expand_query_tokens(query_tokens: set[str], query_text: str) -> set[str]:
    expanded = set(query_tokens)
    for terms, additions in QUERY_EXPANSIONS:
        if all(term in query_tokens or term in query_text for term in terms):
            expanded.update(additions)
    return expanded


def score_skill(
    query_tokens: set[str],
    query_text: str,
    skill,
    raw_query_tokens: set[str] | None = None,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    name = skill.name.lower()
    canonical_name = SKILL_ALIASES.get(name, name)
    description = skill.description.lower()
    keywords = set(skill.keywords)
    raw_query_tokens = raw_query_tokens or query_tokens

    if name in query_text:
        score += 20
        reasons.append("name mentioned")

    overlap = sorted(query_tokens & keywords)
    if overlap:
        score += min(20, len(overlap) * 3)
        reasons.append("keyword overlap: " + ", ".join(overlap[:6]))

    for topic in skill.topics:
        if topic in query_tokens or topic in query_text:
            score += 6
            reasons.append(f"topic: {topic}")

    for trigger in skill.triggers:
        trigger_tokens = set(tokenize(trigger))
        if query_tokens & trigger_tokens:
            score += min(8, len(query_tokens & trigger_tokens) * 2)

    for skill_name, terms, boost, reason in CURATED_BOOSTS:
        if canonical_name == skill_name and all(term in raw_query_tokens or term in query_text for term in terms):
            score += boost
            reasons.append(reason)

    return score, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a task to likely installed skills.")
    parser.add_argument("task", nargs="+")
    parser.add_argument("--map", default=str(default_out_dir() / "skill-map.json"))
    parser.add_argument("--host", default="codex", choices=known_hosts() + ["all"])
    parser.add_argument("--project", default=".", help="Project folder used to resolve project-local skill roots.")
    parser.add_argument("--skills-dir", action="append", help="Explicit skill directory. Can be passed more than once.")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    query_text = " ".join(args.task).lower()
    raw_query_tokens = set(tokenize(query_text))
    query_tokens = expand_query_tokens(raw_query_tokens, query_text)
    map_path = Path(args.map).expanduser().resolve()

    if args.refresh or not map_path.exists():
        project = Path(args.project).expanduser().resolve()
        if args.skills_dir:
            skill_dirs = [Path(item).expanduser().resolve() for item in args.skills_dir]
        else:
            skill_dirs = []
            for profile in profiles_for(args.host):
                skill_dirs.extend(skill_roots_for(profile, project))
            if not skill_dirs:
                skill_dirs = [default_skills_dir()]
        deduped_dirs = []
        seen_dirs: set[str] = set()
        for skills_dir in skill_dirs:
            key = str(skills_dir.expanduser().resolve() if skills_dir.exists() else skills_dir.expanduser())
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            deduped_dirs.append(skills_dir)
        skill_dirs = deduped_dirs
        records = []
        seen_records: set[tuple[str, str]] = set()
        for skills_dir in skill_dirs:
            for record in scan_skills(skills_dir):
                key = (record.name.lower(), record.description.strip().lower())
                if key in seen_records:
                    continue
                seen_records.add(key)
                records.append(record)
        write_map(records, map_path.parent)
    else:
        records = load_map(map_path)

    ranked_by_name = {}
    for skill in records:
        score, reasons = score_skill(query_tokens, query_text, skill, raw_query_tokens)
        if score > 0:
            key = normalize_skill_item(skill.name)[0] or skill.name.lower()
            item = {"skill": skill, "score": score, "reasons": reasons}
            if key not in ranked_by_name or score > ranked_by_name[key]["score"]:
                ranked_by_name[key] = item
    ranked = list(ranked_by_name.values())
    ranked.sort(key=lambda item: (-item["score"], item["skill"].name.lower()))
    top = ranked[: args.limit]

    def route_name(name: str) -> str:
        return normalize_skill_item(name)[0] or name

    primary = route_name(top[0]["skill"].name) if top else None
    verification = next((route_name(item["skill"].name) for item in top if route_name(item["skill"].name) in VERIFICATION_HINTS), None)
    if verification is None:
        verification = next((route_name(item["skill"].name) for item in ranked if route_name(item["skill"].name) in VERIFICATION_HINTS), None)

    payload = {
        "task": " ".join(args.task),
        "primary": primary,
        "verification": verification,
        "recommended": [
            {
                "name": route_name(item["skill"].name),
                "source_name": item["skill"].name,
                "folder": item["skill"].folder,
                "score": item["score"],
                "topics": item["skill"].topics,
                "reasons": item["reasons"],
                "description": item["skill"].description,
            }
            for item in top
        ],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"task={payload['task']}")
        print(f"primary={primary or 'none'}")
        print(f"verification={verification or 'none'}")
        print("recommended:")
        for item in payload["recommended"]:
            print(f"- {item['name']} score={item['score']} reasons={'; '.join(item['reasons'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
