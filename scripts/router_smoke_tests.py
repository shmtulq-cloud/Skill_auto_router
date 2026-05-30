from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SAMPLE_SKILLS = [
    {
        "name": "market-research",
        "folder": "market-research",
        "path": "market-research",
        "description": "Conduct market research and competitive analysis with source attribution.",
        "topics": ["research"],
        "triggers": [],
        "keywords": ["market", "research", "competitive"],
    },
    {
        "name": "research-ops",
        "folder": "research-ops",
        "path": "research-ops",
        "description": "Evidence-first research and source discipline.",
        "topics": ["research"],
        "triggers": [],
        "keywords": ["source", "citation", "research"],
    },
    {
        "name": "deep-research",
        "folder": "deep-research",
        "path": "deep-research",
        "description": "Deep cited research.",
        "topics": ["research"],
        "triggers": [],
        "keywords": ["research", "cited"],
    },
    {
        "name": "systematic-debugging",
        "folder": "systematic-debugging",
        "path": "systematic-debugging",
        "description": "Debug failing apps and errors systematically.",
        "topics": ["debug"],
        "triggers": [],
        "keywords": ["debug", "error", "bug"],
    },
    {
        "name": "opensource-pipeline",
        "folder": "opensource-pipeline",
        "path": "opensource-pipeline",
        "description": "Prepare and publish open-source repositories.",
        "topics": ["automation"],
        "triggers": [],
        "keywords": ["open-source", "github"],
    },
    {
        "name": "github-ops",
        "folder": "github-ops",
        "path": "github-ops",
        "description": "GitHub operations, issues, PRs, and repository management.",
        "topics": ["automation"],
        "triggers": [],
        "keywords": ["github", "issue", "pr"],
    },
    {
        "name": "opc-orchestrator",
        "folder": "opc-orchestrator",
        "path": "opc-orchestrator",
        "description": "Orchestrate the full one-person company workflow across OPC skills.",
        "topics": ["automation"],
        "triggers": [],
        "keywords": ["business", "workflow"],
    },
    {
        "name": "opc-mvp-designer",
        "folder": "opc-mvp-designer",
        "path": "opc-mvp-designer",
        "description": "Define MVP options and smallest viable experiments.",
        "topics": ["product"],
        "triggers": [],
        "keywords": ["mvp", "experiment"],
    },
    {
        "name": "skill-auto-router",
        "folder": "skill-auto-router",
        "path": "skill-auto-router",
        "description": "Route tasks to installed skills and update the route when the work changes phase.",
        "topics": ["automation"],
        "triggers": [],
        "keywords": ["skill", "router", "route", "reroute", "checkpoint"],
    },
]


CASES = [
    {
        "task": "把这句话改得更自然：我们通过更好的客户沟通来创造长期商业价值。",
        "route_level": "none",
        "primary": None,
    },
    {
        "task": "不用上网，帮我想 5 个适合检索办公室绿植养护的中文关键词组合。",
        "route_level": "none",
        "primary": None,
    },
    {
        "task": "解释一下 PR 是什么",
        "route_level": "none",
        "primary": None,
    },
    {
        "task": "帮我查一下菲律宾HVAC市场，做竞品分析并找来源",
        "route_level": "heavy",
        "primary": "market-research",
    },
    {
        "task": "这个项目跑不起来，帮我修报错",
        "route_level": "heavy",
        "primary": "systematic-debugging",
    },
    {
        "task": "帮我上传 GitHub 并开源，顺便提交代码",
        "route_level": "heavy",
        "primary": "opensource-pipeline",
    },
    {
        "task": "我们一起做商业验证，构思 MVP，看看怎么试卖",
        "route_level": "heavy",
        "primary": "opc-orchestrator",
    },
    {
        "task": "帮我设计 MVP 的最小可行实验",
        "route_level": "heavy",
        "primary": "opc-mvp-designer",
    },
    {
        "task": "任务做到一半发现要重新路由，追加技能并做中途检查",
        "route_level": "heavy",
        "primary": "skill-auto-router",
    },
]


def run_case(route_script: Path, map_path: Path, task: str) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(route_script), task, "--map", str(map_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return json.loads(result.stdout)


def main() -> int:
    route_script = Path(__file__).with_name("route_task.py")
    with tempfile.TemporaryDirectory() as tmp:
        map_path = Path(tmp) / "skill-map.json"
        map_path.write_text(json.dumps({"count": len(SAMPLE_SKILLS), "skills": SAMPLE_SKILLS}, ensure_ascii=False), encoding="utf-8")
        failures = []
        for case in CASES:
            payload = run_case(route_script, map_path, case["task"])
            expected_level = case["route_level"]
            expected_primary = case["primary"]
            if payload["route_level"] != expected_level or payload["primary"] != expected_primary:
                failures.append(
                    {
                        "task": case["task"],
                        "expected": {"route_level": expected_level, "primary": expected_primary},
                        "actual": {"route_level": payload["route_level"], "primary": payload["primary"]},
                    }
                )

    if failures:
        print(json.dumps({"ok": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "cases": len(CASES)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
