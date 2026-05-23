from __future__ import annotations

import argparse
from pathlib import Path
import json

from skill_router_common import default_out_dir, default_skills_dir, load_map, scan_skills, tokenize, write_map


VERIFICATION_HINTS = {
    "verification-loop",
    "verification-before-completion",
    "systematic-debugging",
    "tdd-workflow",
    "security-review",
}

CURATED_BOOSTS = [
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


def score_skill(query_tokens: set[str], query_text: str, skill) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    name = skill.name.lower()
    description = skill.description.lower()
    keywords = set(skill.keywords)

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
        if skill.name == skill_name and all(term in query_tokens or term in query_text for term in terms):
            score += boost
            reasons.append(reason)

    return score, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a task to likely installed skills.")
    parser.add_argument("task", nargs="+")
    parser.add_argument("--map", default=str(default_out_dir() / "skill-map.json"))
    parser.add_argument("--skills-dir", default=str(default_skills_dir()))
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    query_text = " ".join(args.task).lower()
    query_tokens = set(tokenize(query_text))
    map_path = Path(args.map).expanduser().resolve()

    if args.refresh or not map_path.exists():
        records = scan_skills(Path(args.skills_dir).expanduser().resolve())
        write_map(records, map_path.parent)
    else:
        records = load_map(map_path)

    ranked = []
    for skill in records:
        score, reasons = score_skill(query_tokens, query_text, skill)
        if score > 0:
            ranked.append({"skill": skill, "score": score, "reasons": reasons})
    ranked.sort(key=lambda item: (-item["score"], item["skill"].name.lower()))
    top = ranked[: args.limit]

    primary = top[0]["skill"].name if top else None
    verification = next((item["skill"].name for item in top if item["skill"].name in VERIFICATION_HINTS), None)
    if verification is None:
        verification = next((item["skill"].name for item in ranked if item["skill"].name in VERIFICATION_HINTS), None)

    payload = {
        "task": " ".join(args.task),
        "primary": primary,
        "verification": verification,
        "recommended": [
            {
                "name": item["skill"].name,
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
