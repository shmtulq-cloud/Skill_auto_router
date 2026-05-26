---
name: skill-auto-router
description: Also known as Skill Auto Router, Skill_auto_router, or legacy skill-router-cartographer. Use before substantial work when installed skills should be selected, audited, mapped, reflected into project instructions, or reviewed for routing mistakes. Scans local Codex-compatible skills, extracts descriptions/triggers/scenarios/overlaps, routes the current task to a short list of best-fit skills, shows visible skill usage/conflict/correction notices, records local feedback traces, and safely suggests or applies project-instruction guidance.
metadata:
  short-description: Route work to installed skills
---

# Skill Auto Router

Name policy:

- Public name: `Skill Auto Router`.
- Repository slug: `Skill_auto_router`.
- Canonical skill id in traces and instructions: `skill-auto-router`.
- Legacy alias: `skill-router-cartographer`.

Normalize old aliases to `skill-auto-router` in feedback traces so health reports do not split the same skill into multiple names.

Use this skill as a lightweight router before substantial work, especially when many skills are installed or when the user asks why a skill did or did not trigger. It can be used from Codex, Claude Code, Kiro, Antigravity, OpenCode, OpenClaw, Hermes, and other agents that can read Markdown instruction files.

## Workflow

1. Understand the user's task.
2. Refresh the local skill map when missing, stale, or after new skill installs.
3. Route the task to:
   - one primary workflow skill
   - zero to three supporting domain/tool skills
   - one verification or review skill when useful
4. Load only the selected skills' full `SKILL.md` files.
5. If project instructions need routing guidance, propose a patch first. Apply only after user approval.

## Post-Install Onboarding

After this skill is installed, after new skills are installed, or on first use in a project, check whether the project or user instructions already have skill-routing guidance:

```bash
python scripts/onboarding_check.py --project <path> --host all --scope both
```

If guidance is missing, show the user why this matters and ask before changing anything. The key reason is simple: installing a skill makes it available, but many IDEs/agents will not proactively call it unless their project or user-level instructions tell them to route work through installed skills.

Use this exact prompt shape:

```text
Setup Notice: skill-auto-router is installed, but this project/user profile does not yet ask agents to route work through installed skills.
Why: without a short instruction block, the skill may be installed but rarely triggered.
Recommended: add it to the project instruction file first so it only affects this workspace. Add it globally only if you want skill routing across all projects on this machine.
Apply project-level guidance, global guidance, both, or skip?
```

Prefer project instructions first because they affect only the current project. Offer global instructions only when the user wants the behavior across all projects. Never silently edit global or project instructions. If the user says yes, use `scripts/project_instruction_router.py --apply`; it writes a backup when updating an existing instruction file.

## Host Profiles

Use `--host` to target a specific IDE or agent:

- `codex` - project `AGENTS.md`, global `~/.codex/AGENTS.md`, skills in `~/.codex/skills`.
- `claude-code` - project `CLAUDE.md` or `.claude/CLAUDE.md`, global `~/.claude/CLAUDE.md`, skills in `~/.claude/skills`.
- `kiro` - project `.kiro/steering/skill-routing.md` with always-on steering frontmatter, global `~/.kiro/steering/AGENTS.md`.
- `antigravity` - project `AGENTS.md` first, with `GEMINI.md` and `.agents/rules/skill-routing.md` as existing-file fallbacks.
- `opencode` - project `AGENTS.md`, global `~/.config/opencode/AGENTS.md`, with Claude Code fallbacks.
- `openclaw` - project `AGENTS.md`; keep `SOUL.md` and other persona files for identity instead of routing rules.
- `hermes` - project `AGENTS.md` or `HERMES.md`, global `~/.hermes/AGENTS.md`; Hermes can use `skills_list` and `skill_view` when available.
- `universal` - portable `AGENTS.md` profile for unknown or mixed hosts.

Use `--host all` only for audits and scans. Apply instruction patches one host at a time so the user can approve the exact file being changed.

## Required Visibility

For every non-trivial response, show a compact skill-routing note before doing the work:

```text
Skill Route: <primary skill> + <supporting skills> + <verification skill>
Why: <one short reason>
```

If no skill is useful, say:

```text
Skill Route: none
Why: task is trivial / no installed skill adds value
```

At completion, include a short review when skills affected the work:

```text
Skill Usage Review: used <skills>; fit was <good/partial>; missed/next <skill or none>.
```

Keep this brief. The visibility note should make routing auditable without turning every answer into a skill catalog.

## Usage Notices

Show notices immediately when routing quality affects the task:

```text
Skill Usage Notice: <info|warning|correction|blocker> - <what went wrong or changed>; action: <what happens next>
```

Use these levels:

- `info` - useful visibility only.
- `warning` - a skill may have been missed, overused, or in tension with another skill.
- `correction` - the route was wrong or incomplete and has been corrected during the task.
- `blocker` - do not claim completion until the missing verification, source check, or conflict decision is handled.

When multiple skills conflict, show the conflict and the chosen order:

```text
Skill Conflict Notice: <skill-a> conflicts with <skill-b>; chosen order: <primary workflow> -> <domain/tool support> -> <verification>.
```

If a verification skill was missed before completion, stop and verify, or clearly state why verification cannot be completed. If the same missed skill appears three or more times in the feedback history, recommend updating project instructions.

## Feedback Loop

When the user gives feedback about skill use, or when a task clearly reveals a missed, overused, conflicting, or corrected skill route, record a compact local trace:

```bash
python scripts/record_trace.py --task "<short summary>" --recommended "skill-a,skill-b" --used "skill-a" --missed "skill-b" --fit partial --severity warning --notice-shown --note "<short non-sensitive note>"
```

Use `--required` for skills that were mandatory and `--optional` for candidates. Leave empty lists empty; do not record `none`, `n/a`, or status phrases inside skill-name fields. Put route state in `--status`, for example `--status pending`.

Use `fit` values:

- `good` - route matched the task.
- `partial` - useful but missed or overused something.
- `wrong` - route was clearly bad.
- `unknown` - worth recording but not enough evidence.

Summarize feedback history:

```bash
python scripts/summarize_traces.py
```

Create a health report when the user asks how routing is performing, when many skills appear to overlap, or after several routing corrections:

```bash
python scripts/skill_health_report.py --project <path> --host codex --scope project
```

Health reports include sample-size confidence, invalid JSONL rows, normalized trace pollution, onboarding status, repeated misses, overuse patterns, conflicts, and instruction recommendations. Treat them as diagnostic evidence, not a statistically valid accuracy score.

This writes:

```text
~/.codex/skill-router/skill-trace.jsonl
~/.codex/skill-router/skill-trace-summary.md
~/.codex/skill-router/skill-health-report.md
```

Privacy rule: record short task summaries and skill names, not full user prompts, secrets, raw files, or private conversation text.

## Commands

Refresh the local route map:

```bash
python scripts/scan_skills.py
```

Refresh a route map across known host skill roots:

```bash
python scripts/scan_skills.py --host all --project <path>
```

Check onboarding state:

```bash
python scripts/onboarding_check.py --project <path> --host all --scope both
```

If the check reports missing guidance, ask the user whether to install project-level or user/global instructions before doing substantial work.

Route a task:

```bash
python scripts/route_task.py "make a cited Philippines HVAC spec-in market report"
```

Route using another host's skill roots:

```bash
python scripts/route_task.py "debug a failing build" --host claude-code --refresh
```

Record routing feedback:

```bash
python scripts/record_trace.py --task "HVAC market report" --recommended "spec-driven-vibe-coding,market-research" --used "market-research" --missed "verification-loop" --fit partial --severity warning --notice-shown
```

Summarize routing feedback:

```bash
python scripts/summarize_traces.py
```

Create routing health report:

```bash
python scripts/skill_health_report.py
```

Suggest project instruction guidance:

```bash
python scripts/project_instruction_router.py --host codex --project <path>
```

Apply the project instruction guidance only after approval:

```bash
python scripts/project_instruction_router.py --host codex --project <path> --apply
```

## Output Files

By default scripts write private local outputs to:

```text
~/.codex/skill-router/
```

- `skill-map.json` - machine-readable inventory.
- `skill-roadmap.md` - human-readable route map.
- `overlaps.md` - likely exact and topic-level overlaps.
- `skill-trace.jsonl` - compact private feedback events.
- `skill-trace-summary.md` - aggregate feedback summary.
- `skill-health-report.md` - user-facing attention items, conflicts, and instruction recommendations.

## Routing Hints

- Market research, competitive intelligence, cited reports: `market-research`, `deep-research`, `research-ops`.
- Product definition, spec-in, PRD, implementation packages: `spec-driven-vibe-coding`, `product-lens`, `product-capability`.
- Design, prototypes, slides, artifacts, visual direction: Open Design skills such as `creative-director`, `design-brief`, `artifacts-builder`.
- Codebase context and repo packing: `repomix`, `repo-scan`, `codebase-onboarding`.
- Reusable code review memory, code indexes, or "avoid reading the whole repo every time": route to locally installed codebase scanning, onboarding, knowledge/memory, note-taking, review, and verification skills. Do not assume those exact skills exist on every machine.
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
