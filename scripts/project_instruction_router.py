from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


INSTRUCTION_NAMES = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".codex/instructions.md",
    "project-rules.md",
]

BEGIN = "<!-- skill-router:start -->"
END = "<!-- skill-router:end -->"

ROUTING_BLOCK = f"""\
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

Use `skill-router-cartographer` when skill choice is unclear, after installing new skills, or when this project's instructions need an updated skill route map. Use `ecc-guide` or `using-superpowers` as fallback routers for their ecosystems.

Default routing:
- Research, competitive analysis, and cited reports: `market-research`, `deep-research`, `research-ops`.
- Product definition, PRD, spec-in, and implementation packages: `spec-driven-vibe-coding`, `product-lens`, `product-capability`.
- Design, prototypes, slides, and visual direction: Open Design skills such as `creative-director`, `design-brief`, `artifacts-builder`.
- Codebase context packing and onboarding: `repomix`, `repo-scan`, `codebase-onboarding`.
- Debugging, TDD, and completion checks: `systematic-debugging`, `tdd-workflow`, `verification-loop`.
{END}
"""


def find_instruction(project: Path) -> Path:
    for name in INSTRUCTION_NAMES:
        candidate = project / name
        if candidate.exists():
            return candidate
    return project / "AGENTS.md"


def upsert_block(old: str) -> tuple[str, bool]:
    if BEGIN in old and END in old:
        start = old.index(BEGIN)
        end = old.index(END, start) + len(END)
        new = old[:start].rstrip() + "\n\n" + ROUTING_BLOCK.rstrip() + "\n\n" + old[end:].lstrip()
        return new, True
    if "skill-router-cartographer" in old:
        return old, False
    return old.rstrip() + "\n\n" + ROUTING_BLOCK + "\n", True


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest or apply project instruction skill-routing guidance.")
    parser.add_argument("--project", default=".")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    instruction = find_instruction(project)
    old = instruction.read_text(encoding="utf-8", errors="replace") if instruction.exists() else ""
    new, changed = upsert_block(old)

    print(f"instruction={instruction}")
    if not changed:
        print("already_configured=true")
        return 0

    print("--- suggested block ---")
    print(ROUTING_BLOCK)

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
