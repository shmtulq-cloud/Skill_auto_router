from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from host_profiles import find_instruction, known_hosts, profile_for

BEGIN = "<!-- skill-router:start -->"
END = "<!-- skill-router:end -->"

ROUTING_BLOCK_TEMPLATE = """\
{frontmatter}\
{BEGIN}
## Skill Routing

Before substantial work, check whether an installed skill fits the task. If a relevant skill exists, use it or briefly explain why it is not needed.

Do not wait for the user to explicitly mention or @ a skill. Infer likely skills from the user's intent and route proactively.

Beginner-friendly trigger mode: the user should not need to remember skill names. Treat ordinary phrases as routing intent. Examples: "查一下/研究一下/找资料" means research; "写文章/公众号/润色/排版" means writing/content; "做图/封面/PPT/视觉/UI" means design/media; "做个网站/修报错/跑不起来" means coding/debugging; "看不懂项目/代码地图/审查代码" means codebase onboarding/review; "上传 GitHub/提交/PR/issue" means Git/GitHub workflow; "整理表格/数据分析/PDF/网页转资料" means data/document/local-corpus workflow. Ask at most one plain-language question when routing is genuinely ambiguous.

For every non-trivial task, show a compact route note before doing the work:

```text
Skill Route: <primary skill> + <supporting skills> + <verification skill>
Route Level: none | light | workflow | heavy
Why: <one short reason>
```

If no skill is useful, write `Skill Route: none` with a short reason.

No-skill gate: before routing, decide whether opening a skill is worth the overhead. Do not use a skill for simple direct-answer tasks such as single-sentence rewriting, basic concept explanation, short keyword brainstorming, translation, or lightweight naming unless the user asks for a workflow, source verification, files, code, tools, or a concrete deliverable.

Mid-task reroute checkpoint: during non-trivial work, re-check routing whenever the task changes phase or reveals a new deliverable, such as research, source verification, code/debugging, tests, visuals, document/data extraction, GitHub/open-source work, deployment, privacy/security review, or business/product workflow. Also reroute when the user corrects direction, a skill was missed, the agent gets stuck, or verification becomes necessary. Show:

```text
Skill Route Update: <old route> -> <new route>
Route Level: none | light | workflow | heavy
Why: <what changed>
Action: <continue/add/replace/verify>
```

At completion, include a brief `Skill Usage Review` only when it adds useful accountability, such as after a correction, conflict, verification decision, or substantial workflow task.

Trace discipline: default behavior is routing, not logging. Do not spend extra effort writing trace events during ordinary tasks. Only record `route_decision`, `correction`, or `usage_review` events when the user explicitly asks to audit routing telemetry, when maintaining the router, or when investigating repeated missed/overused/conflicting routes. Do not treat trace output as full skill-usage analytics.

If skill routing quality affects the task, show a visible notice immediately:

```text
Skill Usage Notice: <info|warning|correction|blocker> - <issue>; action: <what happens next>
```

If multiple skills conflict, show:

```text
Skill Conflict Notice: <skill-a> conflicts with <skill-b>; chosen order: <primary workflow> -> <supporting skill> -> <verification>.
```

If a verification skill was missed before claiming completion, stop and verify or clearly say verification could not be completed. If the same missed skill appears repeatedly, suggest updating these project instructions.

Use `skill-auto-router` when skill choice is unclear, after installing new skills, or when this project's instructions need an updated skill route map. Legacy name: `skill-router-cartographer`. Use `ecc-guide` or `using-superpowers` as fallback routers for their ecosystems.

Default routing:
- Research, competitive analysis, and cited reports: `market-research`, `deep-research`, `research-ops`.
- Product definition, PRD, spec-in, and implementation packages: `spec-driven-vibe-coding`, `product-lens`, `product-capability`.
- Business building, one-person company, side business, business validation, MVP validation, conversion loops, asset ops, and operating reviews: the OPC skill family. Prefer `opc-orchestrator` for broad or first-time workflows; use a specific OPC stage skill only when the user clearly asks for that stage.
- Writing, WeChat drafts, article shaping, copywriting, and polishing: `article-writing`, `writing-shape`, `content-engine`, `copywriting`, and WeChat-specific skills when installed.
- Local source capture, PDFs, webpages, and reusable research packs: `anything-to-local-data`, document/PDF skills, and data-report skills.
- GitHub, commits, branches, issues, PRs, and open-source publishing: `git-workflow`, `github-ops`, `opensource-pipeline`.
- Design, prototypes, slides, and visual direction: Open Design skills such as `creative-director`, `design-brief`, `artifacts-builder`.
- Codebase context packing and onboarding: `repomix`, `repo-scan`, `codebase-onboarding`.
- Reusable code review memory, code indexes, or avoiding repeated full-repo reads: route to locally installed codebase scanning, onboarding, knowledge/memory, note-taking, review, and verification skills. Do not assume those exact skills exist on every machine.
- Debugging, TDD, and completion checks: `systematic-debugging`, `tdd-workflow`, `verification-loop`.

Host profile: `{host_id}` ({host_name}). {host_note}
{END}
"""


def routing_block(host: str, include_frontmatter: bool = True) -> str:
    profile = profile_for(host)
    return ROUTING_BLOCK_TEMPLATE.format(
        frontmatter=profile.steering_frontmatter if include_frontmatter else "",
        BEGIN=BEGIN,
        END=END,
        host_id=profile.id,
        host_name=profile.display_name,
        host_note=profile.note,
    )


def upsert_block(old: str, block: str) -> tuple[str, bool]:
    if BEGIN in old and END in old:
        start = old.index(BEGIN)
        end = old.index(END, start) + len(END)
        new = old[:start].rstrip() + "\n\n" + block.rstrip() + "\n\n" + old[end:].lstrip()
        return new, True
    if "skill-auto-router" in old or "skill-router-cartographer" in old:
        return old, False
    if old.strip():
        return old.rstrip() + "\n\n" + block + "\n", True
    return block + "\n", True


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest or apply project instruction skill-routing guidance.")
    parser.add_argument("--project", default=".")
    parser.add_argument("--host", default="codex", choices=known_hosts())
    parser.add_argument("--scope", default="project", choices=["project", "global"])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    profile = profile_for(args.host)
    instruction = find_instruction(project, profile, args.scope)
    old = instruction.read_text(encoding="utf-8", errors="replace") if instruction.exists() else ""
    block = routing_block(args.host, include_frontmatter=not old.strip())
    new, changed = upsert_block(old, block)

    print(f"host={profile.id}")
    print(f"scope={args.scope}")
    print(f"instruction={instruction}")
    if not changed:
        print("already_configured=true")
        return 0

    print("--- suggested block ---")
    print(block)

    if not args.apply:
        print("apply=false")
        return 0

    instruction.parent.mkdir(parents=True, exist_ok=True)
    if instruction.exists():
        backup = instruction.with_suffix(instruction.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
        backup.write_text(old, encoding="utf-8")
        print(f"backup={backup}")
    instruction.write_text(new, encoding="utf-8")
    print("apply=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
