# Skill Auto Router

`skill-auto-router` is a Codex-compatible meta-skill for people who install many skills and want better routing. It also includes host profiles for Claude Code, Kiro, Antigravity, OpenCode, OpenClaw, Hermes, and portable AGENTS.md-based agents.

Name policy:

- Public name: `Skill Auto Router`.
- Repository slug: `Skill_auto_router`.
- Canonical skill id in traces and instructions: `skill-auto-router`.
- Legacy alias: `skill-router-cartographer`.

Old aliases are normalized to `skill-auto-router` in feedback traces so health reports do not split one skill into several names.

It scans local skills, builds a route map, recommends skills for the current task, and can add a concise routing block to project instructions.
It does not bundle or depend on the author's personal skill inventory; each machine is routed against its own installed `SKILL.md` files.
It is designed for ordinary-language triggering: users should not need to remember or `@` a specific skill name.

For non-coders, the intended usage is simple: say what you want in everyday words. The router should translate "查资料", "写公众号", "做图", "做个网站", "修报错", "看不懂项目", "上传 GitHub", "整理 PDF", or "做商业验证" into the right skill route.

It also encourages always-visible routing:

```text
Skill Route: <primary skill> + <supporting skills> + <verification skill>
Route Level: none | light | workflow | heavy
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

## Easiest Trigger Pattern

For non-coders, use this one sentence shape:

```text
帮我 + 你想完成的目标 + 你想要的结果
```

Examples:

- `帮我查一下菲律宾 HVAC 市场，做竞品分析并找来源`
- `帮我把这篇公众号改得真人感一点，画重点并排版`
- `帮我做一张公众号封面图和插图`
- `这个项目跑不起来，帮我修报错`
- `我看不懂这个代码项目，先帮我做项目梳理和代码地图`
- `帮我上传 GitHub 并开源，顺便提交代码`
- `帮我整理这个 PDF 成资料包，存在本地以后方便研究`
- `我们一起做商业验证，构思 MVP，看看怎么试卖`

## No-Skill Gate

The router should be useful without becoming heavy-handed. Before opening any skill, it now classifies the task:

- `none` - answer directly; skill overhead is not worth it.
- `light` - one lightweight skill may help.
- `workflow` - use the selected workflow skill.
- `heavy` - multi-step work may need supporting and verification skills.

Typical `none` tasks include single-sentence rewriting, basic concept explanation, short keyword brainstorming, translation, and lightweight naming. Use a skill when the user asks for source verification, files, code, tools, research, a concrete deliverable, or a multi-step workflow.

For broad business-building prompts such as "商业验证 + MVP + 试卖", prefer `opc-orchestrator` as the coordinator. Use narrower OPC stage skills, such as `opc-mvp-designer`, only when the user is clearly asking for that stage.

## Install

Copy this repository folder into your Codex skills directory:

```powershell
Copy-Item -Recurse . "$env:USERPROFILE\.codex\skills\skill-auto-router"
```

Existing installs under `skill-router-cartographer` still work as a legacy folder name, but new installs should use `skill-auto-router`.

Restart Codex after installing.

Then run the post-install onboarding check. This is important: installing the skill makes it available, but most IDEs/agents will not reliably call it unless project or user-level instructions tell them to route work through installed skills.

```powershell
python .\scripts\onboarding_check.py --project D:\path\to\project --host all --scope both
```

If it reports missing guidance, ask the user before applying any change:

```text
Setup Notice: skill-auto-router is installed, but this project/user profile does not yet ask agents to route work through installed skills.
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

Route a business-building workflow:

```powershell
python .\scripts\route_task.py "我们一起做商业验证，构思 MVP，看看怎么试卖和形成转化闭环"
```

Record feedback after a task:

```powershell
python .\scripts\record_trace.py --task "short task summary" --recommended "skill-a,skill-b" --used "skill-a" --missed "skill-b" --fit partial --severity warning --notice-shown --note "short non-sensitive note"
```

Use `--required` for skills that must be used, and `--optional` for candidates. Do not write placeholder values such as `none` into `--missed`; leave it empty.

Summarize feedback:

```powershell
python .\scripts\summarize_traces.py
```

Create a health report:

```powershell
python .\scripts\skill_health_report.py --project D:\path\to\project --host codex --scope project
```

Run router smoke tests:

```powershell
python .\scripts\router_smoke_tests.py
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

- confidence level based on sample size and trace quality
- invalid or polluted trace rows
- repeated missed skills
- overused skills
- conflict clusters
- missing user-facing notices
- corrections taken
- onboarding state for project/user instructions
- project-instruction update recommendations

The report is a routing diagnostic, not an exact accuracy score. `Recommended Candidates Not Used` means "suggested but not necessarily required"; use `Required But Unused` and `Repeated Misses` for stronger failure signals.

## License

MIT
