## Skill Auto Router Project Instructions

This repository maintains `skill-auto-router`, a meta-skill that routes work to locally installed skills. Keep it memoryless: do not hard-code the maintainer's personal skill inventory or private project assumptions.

For every non-trivial task in this repository, use visible routing:

```text
Skill Route: <primary skill> + <supporting skills> + <verification skill>
Route Level: none | light | workflow | heavy
Why: <one short reason>
```

Use the no-skill gate before opening any skill. Simple direct-answer tasks should stay at `Route Level: none`; multi-step research, code, GitHub, data, design, business, or verification work can use `light`, `workflow`, or `heavy`.

When changing routing logic, protect these behaviors:

- Ordinary Chinese phrases should trigger useful workflows without requiring the user to remember skill names.
- Simple rewriting, basic explanations, short keyword brainstorming, translation, and lightweight naming should not trigger skill overhead.
- Broad business-building prompts such as "商业验证 + MVP + 试卖" should prefer `opc-orchestrator`; narrow MVP-stage prompts should prefer `opc-mvp-designer`.
- Feedback traces must normalize aliases to `skill-auto-router` and must not store secrets, full prompts, raw files, or private conversation text.

Before finishing routing changes, run:

```powershell
python .\scripts\router_smoke_tests.py
python .\scripts\skill_health_report.py --project . --host codex --scope project
```

Also run a syntax check for changed Python scripts and `git diff --check`.
