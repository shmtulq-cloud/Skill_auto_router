# Skill Auto Router

`skill-router-cartographer` is a Codex-compatible meta-skill for people who install many skills and want better routing. It also includes host profiles for Claude Code, Kiro, Antigravity, OpenCode, OpenClaw, Hermes, and portable AGENTS.md-based agents.

It scans local skills, builds a route map, recommends skills for the current task, and can add a concise routing block to project instructions.
It does not bundle or depend on the author's personal skill inventory; each machine is routed against its own installed `SKILL.md` files.

It also encourages always-visible routing:

```text
Skill Route: <primary skill> + <supporting skills> + <verification skill>
Why: <one short reason>
```

and a short completion review:

```text
Skill Usage Review: used <skills>; fit was <good/partial>; missed/next <skill or none>.
```

It can optionally record a local feedback loop so the route map improves over time:

```powershell
python .\scripts\record_trace.py --task "HVAC market report" --recommended "spec-driven-vibe-coding,market-research" --used "market-research" --missed "verification-loop" --fit partial --severity warning --notice-shown
python .\scripts\summarize_traces.py
python .\scripts\skill_health_report.py
```

## What It Does

- Reads installed `SKILL.md` frontmatter.
- Extracts names, descriptions, triggers, topics, and keywords.
- Generates a local route map.
- Ranks likely skills for a task.
- Records optional local feedback about used/missed/overused skills.
- Records visible notices, corrections, and skill conflicts.
- Summarizes feedback trends and health issues.
- Suggests or applies safe project instruction guidance.

## Install

Copy this repository folder into your Codex skills directory:

```powershell
Copy-Item -Recurse . "$env:USERPROFILE\.codex\skills\skill-router-cartographer"
```

Restart Codex after installing.

Then run the post-install onboarding check. This is important: installing the skill makes it available, but most IDEs/agents will not reliably call it unless project or user-level instructions tell them to route work through installed skills.

```powershell
python .\scripts\onboarding_check.py --project D:\path\to\project --host all --scope both
```

If it reports missing guidance, ask the user before applying any change:

```text
Setup Notice: skill-router-cartographer is installed, but this project/user profile does not yet ask agents to route work through installed skills.
Why: without a short instruction block, the skill may be installed but rarely triggered.
Recommended: add it to the project instruction file first so it only affects this workspace. Add it globally only if you want skill routing across all projects on this machine.
Apply project-level guidance, global guidance, both, or skip?
```

Project-level setup is recommended first; global setup is useful only when the user wants this behavior in every project. The apply command writes a backup before updating an existing instruction file.

## Usage

Check onboarding state:

```powershell
python .\scripts\onboarding_check.py --project D:\path\to\project --host all --scope both
```

Refresh the skill map:

```powershell
python .\scripts\scan_skills.py
```

Refresh across known host skill roots:

```powershell
python .\scripts\scan_skills.py --host all --project D:\path\to\project
```

Route a task:

```powershell
python .\scripts\route_task.py "make a cited Philippines HVAC spec-in market report"
```

Route a codebase knowledge workflow:

```powershell
python .\scripts\route_task.py "审核已有代码并生成代码索引，避免每次全量阅读代码"
```

Record feedback after a task:

```powershell
python .\scripts\record_trace.py --task "short task summary" --recommended "skill-a,skill-b" --used "skill-a" --missed "skill-b" --fit partial --severity warning --notice-shown --note "short non-sensitive note"
```

Summarize feedback:

```powershell
python .\scripts\summarize_traces.py
```

Create a health report:

```powershell
python .\scripts\skill_health_report.py
```

Suggest a project instruction patch:

```powershell
python .\scripts\project_instruction_router.py --host codex --project D:\path\to\project
```

Apply the patch:

```powershell
python .\scripts\project_instruction_router.py --host codex --project D:\path\to\project --apply
```

## Host Profiles

Use `--host` when checking, scanning, or installing instruction guidance:

| Host | Default project instruction | Global instruction | Notes |
|---|---|---|---|
| `codex` | `AGENTS.md` | `~/.codex/AGENTS.md` | OpenAI Codex default. |
| `claude-code` | `CLAUDE.md` | `~/.claude/CLAUDE.md` | Claude Code memory/instructions. |
| `kiro` | `.kiro/steering/skill-routing.md` | `~/.kiro/steering/AGENTS.md` | Writes always-on steering frontmatter for new steering files. |
| `antigravity` | `AGENTS.md` | `~/.gemini/GEMINI.md` | Portable profile; also detects `GEMINI.md`, `.agents/rules`, and `.agents/skills`. |
| `opencode` | `AGENTS.md` | `~/.config/opencode/AGENTS.md` | Uses OpenCode AGENTS.md plus Claude Code fallbacks. |
| `openclaw` | `AGENTS.md` | `~/.openclaw/AGENTS.md` | Keeps persona files such as `SOUL.md` out of default edits. |
| `hermes` | `AGENTS.md` | `~/.hermes/AGENTS.md` | Works with Hermes skill discovery when available. |
| `universal` | `AGENTS.md` | `~/AGENTS.md` | Fallback for mixed or unknown agents. |

Compatibility references used for the defaults:

- Claude Code memory/instructions: https://docs.anthropic.com/en/docs/claude-code/memory
- Claude Code skills: https://docs.anthropic.com/en/docs/claude-code/skills
- Kiro steering and AGENTS.md: https://kiro.dev/docs/steering/
- OpenCode AGENTS.md rules: https://opencode.ai/docs/rules/
- OpenCode skills: https://opencode.ai/docs/skills/
- Antigravity skills: https://antigravity.google/docs/skills

## Safety

- Report and suggest by default.
- Applying project instruction changes writes a backup.
- It does not mutate installed skills.
- It does not paste a huge catalog into project instructions.
- Feedback traces are local and should contain short summaries only, not secrets or full prompts.

## User-Facing Notices

Use these short notices when the route is not clean:

```text
Skill Usage Notice: warning - verification-loop was missed for a completion claim; action: verify before finishing.
```

```text
Skill Conflict Notice: creative-director conflicts with frontend-design on visual direction; chosen order: creative-director -> frontend-design -> browser-qa.
```

```text
Correction: switching from market-research only to market-research + deep-research + verification-loop because the task needs sourced claims.
```

## Health Report

`skill_health_report.py` writes `skill-health-report.md` next to the trace files. It highlights:

- repeated missed skills
- overused skills
- conflict clusters
- missing user-facing notices
- corrections taken
- project-instruction update recommendations

## License

MIT
