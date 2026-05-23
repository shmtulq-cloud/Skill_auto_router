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
python .\scripts\record_trace.py --task "HVAC market report" --recommended "spec-driven-vibe-coding,market-research" --used "market-research" --missed "verification-loop" --fit partial
python .\scripts\summarize_traces.py
```

## What It Does

- Reads installed `SKILL.md` frontmatter.
- Extracts names, descriptions, triggers, topics, and keywords.
- Generates a local route map.
- Ranks likely skills for a task.
- Records optional local feedback about used/missed/overused skills.
- Summarizes feedback trends.
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
python .\scripts\record_trace.py --task "short task summary" --recommended "skill-a,skill-b" --used "skill-a" --missed "skill-b" --fit partial --note "short non-sensitive note"
```

Summarize feedback:

```powershell
python .\scripts\summarize_traces.py
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

## License

MIT
