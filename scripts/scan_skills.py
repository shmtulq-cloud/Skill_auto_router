from __future__ import annotations

import argparse
from pathlib import Path

from host_profiles import known_hosts, profiles_for, skill_roots_for
from skill_router_common import default_out_dir, default_skills_dir, scan_skills, write_map


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan local Codex-compatible skills and build a route map.")
    parser.add_argument("--host", default="codex", choices=known_hosts() + ["all"])
    parser.add_argument("--project", default=".", help="Project folder used to resolve project-local skill roots.")
    parser.add_argument("--skills-dir", action="append", help="Explicit skill directory. Can be passed more than once.")
    parser.add_argument("--out-dir", default=str(default_out_dir()))
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    if args.skills_dir:
        skill_dirs = [Path(item).expanduser().resolve() for item in args.skills_dir]
    else:
        skill_dirs = []
        for profile in profiles_for(args.host):
            skill_dirs.extend(skill_roots_for(profile, project))
        if not skill_dirs:
            skill_dirs = [default_skills_dir()]
    deduped_dirs = []
    seen_dirs: set[str] = set()
    for skills_dir in skill_dirs:
        key = str(skills_dir.expanduser().resolve() if skills_dir.exists() else skills_dir.expanduser())
        if key in seen_dirs:
            continue
        seen_dirs.add(key)
        deduped_dirs.append(skills_dir)
    skill_dirs = deduped_dirs

    records = []
    seen_records: set[tuple[str, str]] = set()
    for skills_dir in skill_dirs:
        for record in scan_skills(skills_dir):
            key = (record.name.lower(), record.description.strip().lower())
            if key in seen_records:
                continue
            seen_records.add(key)
            records.append(record)

    write_map(records, out_dir)
    print(f"skills={len(records)}")
    for skills_dir in skill_dirs:
        print(f"skills_dir={skills_dir.expanduser().resolve()}")
    print(f"out={out_dir}")
    print(f"roadmap={out_dir / 'skill-roadmap.md'}")
    print(f"overlaps={out_dir / 'overlaps.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
