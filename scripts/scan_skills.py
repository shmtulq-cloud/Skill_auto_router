from __future__ import annotations

import argparse
from pathlib import Path

from skill_router_common import default_out_dir, default_skills_dir, scan_skills, write_map


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan local Codex-compatible skills and build a route map.")
    parser.add_argument("--skills-dir", default=str(default_skills_dir()))
    parser.add_argument("--out-dir", default=str(default_out_dir()))
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    records = scan_skills(skills_dir)
    write_map(records, out_dir)
    print(f"skills={len(records)}")
    print(f"skills_dir={skills_dir}")
    print(f"out={out_dir}")
    print(f"roadmap={out_dir / 'skill-roadmap.md'}")
    print(f"overlaps={out_dir / 'overlaps.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
