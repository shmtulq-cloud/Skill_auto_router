from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import re
from collections import Counter, defaultdict


TOPIC_KEYWORDS: dict[str, list[str]] = {
    "research": ["research", "market", "source", "citation", "competitive", "intelligence", "deep"],
    "product": ["product", "prd", "spec", "spec-in", "capability", "roadmap", "requirements"],
    "design": [
        "design", "visual", "slide", "ppt", "artifact", "figma", "creative", "brand", "prototype",
        "视觉", "生图", "配图", "图片", "插图", "封面", "主视觉", "分镜", "海报",
    ],
    "code": ["code", "repo", "backend", "frontend", "api", "database", "migration", "refactor"],
    "debug": ["debug", "bug", "failing", "error", "tdd", "test", "verification", "review"],
    "automation": ["automation", "workflow", "agent", "mcp", "github", "ops", "schedule"],
    "maintenance": ["codex", "fast", "state", "log", "session", "maintenance", "archive"],
    "content": ["content", "article", "social", "wechat", "writing", "copy", "newsletter", "公众号", "微信", "文章"],
    "data": ["data", "spreadsheet", "csv", "sql", "analytics", "dashboard"],
    "security": ["security", "auth", "secret", "owasp", "vulnerability", "compliance"],
}

STOPWORDS = {
    "the", "and", "for", "with", "when", "use", "this", "that", "from", "into",
    "your", "user", "users", "skill", "skills", "task", "tasks", "work", "working",
    "help", "helps", "using", "build", "create", "make", "need", "needs",
}

CHINESE_PHRASES = [
    "公众号", "微信", "文章", "生图", "配图", "图片", "插图", "画图", "绘图",
    "封面", "主视觉", "标题图", "横版", "竖版", "海报", "视觉", "分镜",
    "小红书", "朋友圈", "草稿箱",
]

SKIP_SCAN_PARTS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


@dataclass
class SkillRecord:
    name: str
    folder: str
    path: str
    description: str
    topics: list[str]
    triggers: list[str]
    keywords: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def default_skills_dir() -> Path:
    return codex_home() / "skills"


def default_out_dir() -> Path:
    return codex_home() / "skill-router"


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    match = re.match(r"(?s)^---\s*\n?(.*?)\n?---", text)
    if not match:
        return {}

    lines = match.group(1).splitlines()
    data: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith((" ", "\t")):
            index += 1
            continue
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {"|", ">"}:
            block: list[str] = []
            index += 1
            while index < len(lines):
                nxt = lines[index]
                if nxt and not nxt.startswith((" ", "\t")) and ":" in nxt:
                    break
                block.append(nxt.strip())
                index += 1
            data[key] = " ".join(x for x in block if x).strip()
            continue
        if value == "":
            block = []
            index += 1
            while index < len(lines):
                nxt = lines[index]
                if nxt and not nxt.startswith((" ", "\t")) and ":" in nxt:
                    break
                block.append(nxt.strip())
                index += 1
            data[key] = "\n".join(x for x in block if x).strip()
            continue
        data[key] = value.strip().strip('"').strip("'")
        index += 1
    return data


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}|[\u4e00-\u9fff]{2,}", lowered)
    tokens.extend(phrase for phrase in CHINESE_PHRASES if phrase in text)
    return [t for t in tokens if t not in STOPWORDS]


def classify(name: str, description: str) -> list[str]:
    haystack = f"{name} {description}".lower()
    topics = [topic for topic, words in TOPIC_KEYWORDS.items() if any(word in haystack for word in words)]
    return topics or ["general"]


def extract_triggers(text: str) -> list[str]:
    triggers: list[str] = []
    for pattern in [
        r"Triggers on:\s*([^.\n]+)",
        r"Use when\s+([^.\n]+)",
        r"Use this skill when\s+([^.\n]+)",
    ]:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            triggers.append(match.group(1).strip())
    for quoted in re.findall(r"['\"]([^'\"]{3,80})['\"]", text):
        if len(triggers) >= 12:
            break
        triggers.append(quoted.strip())
    deduped: list[str] = []
    seen: set[str] = set()
    for item in triggers:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped[:12]


def split_frontmatter_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    items: list[str] = []
    for line in raw.splitlines():
        item = line.strip()
        if item.startswith("-"):
            item = item[1:].strip()
        item = item.strip().strip('"').strip("'")
        if item:
            items.append(item)
    return items


def iter_skill_files(skills_dir: Path, max_depth: int = 4) -> list[Path]:
    root = skills_dir.expanduser()
    if not root.exists():
        return []
    files: list[Path] = []
    for skill_md in root.rglob("SKILL.md"):
        rel_parts = skill_md.relative_to(root).parts
        if len(rel_parts) > max_depth + 1:
            continue
        if any(part in SKIP_SCAN_PARTS for part in rel_parts):
            continue
        files.append(skill_md)
    return sorted(files, key=lambda p: str(p).lower())


def scan_skills(skills_dir: Path) -> list[SkillRecord]:
    records: list[SkillRecord] = []
    if not skills_dir.exists():
        return records
    for skill_md in iter_skill_files(skills_dir):
        skill_dir = skill_md.parent
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        name = meta.get("name") or skill_dir.name
        description = meta.get("description") or ""
        keyword_counts = Counter(tokenize(f"{name} {description}"))
        keywords = [word for word, _ in keyword_counts.most_common(20)]
        rel_folder = str(skill_dir.relative_to(skills_dir)).replace("\\", "/")
        triggers = split_frontmatter_list(meta.get("triggers")) + extract_triggers(description)
        records.append(
            SkillRecord(
                name=name,
                folder=rel_folder,
                path=str(skill_dir),
                description=description,
                topics=classify(name, description),
                triggers=triggers[:12],
                keywords=keywords,
            )
        )
    return records


def write_map(records: list[SkillRecord], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"count": len(records), "skills": [r.to_dict() for r in records]}
    (out_dir / "skill-map.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    by_topic: dict[str, list[SkillRecord]] = defaultdict(list)
    by_name: dict[str, list[SkillRecord]] = defaultdict(list)
    for record in records:
        by_name[record.name.lower()].append(record)
        for topic in record.topics:
            by_topic[topic].append(record)

    roadmap = ["# Local Skill Route Map", "", f"Total standard skills: {len(records)}", "", "## Topics", ""]
    for topic in sorted(by_topic):
        roadmap.append(f"### {topic}")
        for record in sorted(by_topic[topic], key=lambda r: r.name.lower())[:50]:
            roadmap.append(f"- `{record.name}` - {record.description}")
        if len(by_topic[topic]) > 50:
            roadmap.append(f"- ... {len(by_topic[topic]) - 50} more")
        roadmap.append("")
    (out_dir / "skill-roadmap.md").write_text("\n".join(roadmap), encoding="utf-8")

    overlaps = ["# Skill Overlaps", ""]
    exact = {name: vals for name, vals in by_name.items() if len(vals) > 1}
    if exact:
        overlaps.append("## Exact frontmatter name overlaps")
        for name, vals in sorted(exact.items()):
            overlaps.append(f"### {name}")
            for record in vals:
                overlaps.append(f"- `{record.folder}`: {record.path}")
            overlaps.append("")
    else:
        overlaps.append("No exact frontmatter-name overlaps found.")
        overlaps.append("")

    overlaps.append("## Large topic clusters")
    for topic, vals in sorted(by_topic.items(), key=lambda item: len(item[1]), reverse=True):
        if len(vals) >= 20:
            overlaps.append(f"- `{topic}`: {len(vals)} skills")
    (out_dir / "overlaps.md").write_text("\n".join(overlaps), encoding="utf-8")


def load_map(path: Path) -> list[SkillRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records: list[SkillRecord] = []
    for item in data.get("skills", []):
        description = item.get("description", "")
        name = item.get("name", item.get("folder", "unknown"))
        item.setdefault("triggers", extract_triggers(description))
        item.setdefault("keywords", [word for word, _ in Counter(tokenize(f"{name} {description}")).most_common(20)])
        item.setdefault("topics", classify(name, description))
        records.append(SkillRecord(**item))
    return records
