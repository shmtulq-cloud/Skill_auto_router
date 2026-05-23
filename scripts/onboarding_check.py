from __future__ import annotations

import argparse
import json
from pathlib import Path

from project_instruction_router import BEGIN, find_instruction
from skill_router_common import codex_home


def is_configured(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return BEGIN in text or "skill-router-cartographer" in text


def check_target(label: str, root: Path) -> dict[str, object]:
    instruction = find_instruction(root)
    configured = is_configured(instruction)
    return {
        "label": label,
        "root": str(root),
        "instruction": str(instruction),
        "configured": configured,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether skill-router onboarding guidance is present.")
    parser.add_argument("--project", default=".", help="Project folder to check.")
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
    if args.scope in {"project", "both"}:
        targets.append(check_target("project", project_root))
    if args.scope in {"global", "both"}:
        targets.append(check_target("global", codex_home()))

    needs_setup = [target for target in targets if not bool(target["configured"])]
    payload = {"targets": targets, "needs_setup": needs_setup}

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    for target in targets:
        status = "configured" if target["configured"] else "missing"
        print(f"{target['label']}_status={status}")
        print(f"{target['label']}_instruction={target['instruction']}")

    if needs_setup:
        print("setup_notice=Skill router is installed, but routing guidance is missing from one or more instruction files.")
        print("recommended_next_step=Ask the user before applying project_instruction_router.py --apply.")
        for target in needs_setup:
            if target["label"] == "project":
                print(f"project_apply_command=python scripts/project_instruction_router.py --project \"{target['root']}\" --apply")
            if target["label"] == "global":
                print(f"global_apply_command=python scripts/project_instruction_router.py --project \"{target['root']}\" --apply")
    else:
        print("setup_notice=Skill routing guidance is already configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
