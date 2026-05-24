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

For every non-trivial task, show a compact route note before doing the work:

```text
Skill Route: <primary skill> + <supporting skills> + <verification skill>
Why: <one short reason>
```

If no skill is useful, write `Skill Route: none` with a short reason.

At completion, include a brief `Skill Usage Review` stating which skills were used, whether the fit was correct, and any missed or next-step skill.

If skill routing quality affects the task, show a visible notice immediately:

```text
Skill Usage Notice: <info|warning|correction|blocker> - <issue>; action: <what happens next>
```

If multiple skills conflict, show:

```text
Skill Conflict Notice: <skill-a> conflicts with <skill-b>; chosen order: <primary workflow> -> <supporting skill> -> <verification>.
```

If a verification skill was missed before claiming completion, stop and verify or clearly say verification could not be completed. If the same missed skill appears repeatedly, suggest updating these project instructions.

Use `skill-router-cartographer` when skill choice is unclear, after installing new skills, or when this project's instructions need an updated skill route map. Use `ecc-guide` or `using-superpowers` as fallback routers for their ecosystems.

Default routing:
- Research, competitive analysis, and cited reports: `market-research`, `deep-research`, `research-ops`.
- Product definition, PRD, spec-in, and implementation packages: `spec-driven-vibe-coding`, `product-lens`, `product-capability`.
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
    if "skill-router-cartographer" in old:
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
