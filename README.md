# Skill Auto Router

`skill-router-cartographer` is a Codex-compatible meta-skill for people who install many skills and want better routing.

It scans local skills, builds a route map, recommends skills for the current task, and can add a concise routing block to project instructions.

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

## Usage

Refresh the skill map:

```powershell
python .\scripts\scan_skills.py
```

Route a task:

```powershell
python .\scripts\route_task.py "make a cited Philippines HVAC spec-in market report"
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
python .\scripts\project_instruction_router.py --project D:\path\to\project
```

Apply the patch:

```powershell
python .\scripts\project_instruction_router.py --project D:\path\to\project --apply
```

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
