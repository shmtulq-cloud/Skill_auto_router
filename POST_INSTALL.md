# Post-Install Onboarding

After installing `skill-auto-router`, run the onboarding check from the installed skill folder:

```powershell
python .\scripts\onboarding_check.py --project D:\path\to\project --host all --scope both
```

If guidance is missing, ask the user before applying anything:

```text
Setup Notice: skill-auto-router is installed, but this project/user profile does not yet ask agents to route work through installed skills.
Why: without a short instruction block, the skill may be installed but rarely triggered.
Recommended: add it to the project instruction file first so it only affects this workspace. Add it globally only if you want skill routing across all projects on this machine.
Apply project-level guidance, global guidance, both, or skip?
```

Apply only after the user chooses a scope:

```powershell
python .\scripts\project_instruction_router.py --host codex --project D:\path\to\project --apply
python .\scripts\project_instruction_router.py --host codex --scope global --project D:\path\to\project --apply
```

Use `--host claude-code`, `--host kiro`, `--host antigravity`, `--host opencode`, `--host openclaw`, `--host hermes`, or `--host universal` for other IDEs/agents.

Default recommendation: project-level first, global only when the user wants this behavior across all projects on the machine.
