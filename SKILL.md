---
name: skill-router-cartographer
description: Use before substantial work when installed skills should be selected, audited, mapped, or reflected into project instructions. Scans local Codex-compatible skills, extracts descriptions/triggers/scenarios/overlaps, routes the current task to a short list of best-fit skills, and safely suggests or applies project-instruction guidance.
metadata:
  short-description: Route work to installed skills
---

# Skill Router Cartographer

Use this skill as a lightweight router before substantial work, especially when many skills are installed or when the user asks why a skill did or did not trigger.

## Workflow

1. Understand the user's task.
2. Refresh the local skill map when missing, stale, or after new skill installs.
3. Route the task to:
   - one primary workflow skill
   - zero to three supporting domain/tool skills
   - one verification or review skill when useful
4. Load only the selected skills' full `SKILL.md` files.
5. If project instructions need routing guidance, propose a patch first. Apply only after user approval.

## Commands

Refresh the local route map:

```bash
python scripts/scan_skills.py
```

Route a task:

```bash
python scripts/route_task.py "make a cited Philippines HVAC spec-in market report"
```

Suggest project instruction guidance:

```bash
python scripts/project_instruction_router.py --project <path>
```

Apply the project instruction guidance only after approval:

```bash
python scripts/project_instruction_router.py --project <path> --apply
```

## Output Files

By default scripts write private local outputs to:

```text
~/.codex/skill-router/
```

- `skill-map.json` - machine-readable inventory.
- `skill-roadmap.md` - human-readable route map.
- `overlaps.md` - likely exact and topic-level overlaps.

## Routing Hints

- Market research, competitive intelligence, cited reports: `market-research`, `deep-research`, `research-ops`.
- Product definition, spec-in, PRD, implementation packages: `spec-driven-vibe-coding`, `product-lens`, `product-capability`.
- Design, prototypes, slides, artifacts, visual direction: Open Design skills such as `creative-director`, `design-brief`, `artifacts-builder`.
- Codebase context and repo packing: `repomix`, `repo-scan`, `codebase-onboarding`.
- Debugging, TDD, completion checks: `systematic-debugging`, `tdd-workflow`, `verification-loop`, `verification-before-completion`.
- Local Codex state maintenance: `keep-codex-fast`.
- Information tracking and digests: `follow-builders`.
- Unknown ECC component choice: `ecc-guide`.
- Unknown Superpowers workflow choice: `using-superpowers`.

## Safety

- Do not force skill use for trivial tasks.
- Do not paste a giant skill catalog into project instructions.
- Do not overwrite instructions without a backup.
- Treat generated maps as local/private unless the user chooses to share them.
