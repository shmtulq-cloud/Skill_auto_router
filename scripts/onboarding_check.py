from __future__ import annotations

import argparse
import json
from pathlib import Path

from host_profiles import find_instruction, known_hosts, profile_for, profiles_for
from project_instruction_router import BEGIN


def is_configured(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return BEGIN in text or "skill-auto-router" in text or "skill-router-cartographer" in text


def check_target(host: str, label: str, root: Path) -> dict[str, object]:
    profile = profile_for(host)
    instruction = find_instruction(root, profile, label)
    configured = is_configured(instruction)
    return {
        "host": profile.id,
        "host_name": profile.display_name,
        "label": label,
        "root": str(root),
        "instruction": str(instruction),
        "configured": configured,
        "note": profile.note,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether skill-router onboarding guidance is present.")
    parser.add_argument("--project", default=".", help="Project folder to check.")
    parser.add_argument("--host", default="codex", choices=known_hosts() + ["all"], help="Host or IDE profile to check.")
    parser.add_argument(
        "--scope",
        default="project",
        choices=["project", "global", "both"],
        help="Check project instructions, global Codex instructions, or both.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project).expanduser().resolve()
    targets: list[dict[str, object]] = []
    for profile in profiles_for(args.host):
        if args.scope in {"project", "both"}:
            targets.append(check_target(profile.id, "project", project_root))
        if args.scope in {"global", "both"}:
            targets.append(check_target(profile.id, "global", project_root))

    needs_setup = [target for target in targets if not bool(target["configured"])]
    payload = {"targets": targets, "needs_setup": needs_setup}

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    for target in targets:
        status = "configured" if target["configured"] else "missing"
        prefix = f"{target['host']}_{target['label']}"
        print(f"{prefix}_status={status}")
        print(f"{prefix}_instruction={target['instruction']}")

    if needs_setup:
        print("setup_notice=Skill router is installed, but routing guidance is missing from one or more instruction files.")
        print(
            "why=Without one short instruction in project or user-level agent instructions, "
            "many IDEs/agents will not proactively invoke this skill before work begins."
        )
        print(
            "ask_user=Do you want me to add a concise skill-routing instruction block? "
            "Recommended: project instructions first. Choose project, global, both, or skip."
        )
        print(
            "project_scope_reason=Project instructions are safer for teams and repos because they affect only this workspace."
        )
        print(
            "global_scope_reason=User/global instructions make skill routing active across future projects on this machine, "
            "but should be used only when the user wants that default everywhere."
        )
        print("safety=Never apply instruction changes silently; project_instruction_router.py writes a backup when updating an existing file.")
        print("recommended_next_step=Ask the user, then apply the exact command for the chosen scope.")
        for target in needs_setup:
            if target["label"] == "project":
                print(
                    f"{target['host']}_project_apply_command="
                    f"python scripts/project_instruction_router.py --host {target['host']} --project \"{target['root']}\" --apply"
                )
            if target["label"] == "global":
                print(
                    f"{target['host']}_global_apply_command="
                    f"python scripts/project_instruction_router.py --host {target['host']} --scope global --project \"{target['root']}\" --apply"
                )
    else:
        print("setup_notice=Skill routing guidance is already configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
