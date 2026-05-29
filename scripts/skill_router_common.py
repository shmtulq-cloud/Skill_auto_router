from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import re
from collections import Counter, defaultdict


ROUTER_CANONICAL_ID = "skill-auto-router"
ROUTER_DISPLAY_NAME = "Skill Auto Router"
ROUTER_REPO_SLUG = "Skill_auto_router"
ROUTER_LEGACY_ID = "skill-router-cartographer"
TRACE_SCHEMA_VERSION = 2


TOPIC_KEYWORDS: dict[str, list[str]] = {
    "research": ["research", "market", "source", "citation", "competitive", "intelligence", "deep"],
    "product": ["product", "prd", "spec", "spec-in", "capability", "roadmap", "requirements"],
    "design": [
        "design", "visual", "slide", "ppt", "artifact", "figma", "creative", "brand", "prototype",
        "视觉", "生图", "配图", "图片", "插图", "封面", "主视觉", "分镜", "海报",
    ],
    "code": [
        "code", "repo", "backend", "frontend", "api", "database", "migration", "refactor",
        "代码", "代码库", "仓库", "模块", "架构", "索引", "代码索引", "知识图谱", "依赖图", "调用图",
    ],
    "debug": ["debug", "bug", "failing", "error", "tdd", "test", "verification", "review", "审查", "审核", "增量"],
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
    "技能路由", "路由器", "路由健康", "健康报告", "健康状态", "安装状态",
    "代码", "代码库", "代码审核", "代码审查", "代码索引", "知识图谱", "架构图",
    "模块关系", "调用图", "依赖图", "增量审查", "增量审核", "全量阅读", "全量扫描",
    "接手项目", "理解代码", "项目记忆", "架构记忆", "踩坑记录",
    "一人企业", "一人公司", "个人商业化", "个人业务", "副业", "轻资产",
    "建盘", "资源盘点", "利基定位", "价值主张", "商业模式", "精益画布",
    "商业模式画布", "最小验证", "转化闭环", "资产沉淀", "经营复盘",
    "运营复盘", "运营卡住", "用户池", "内容池", "产品池",
    "商业验证", "业务验证", "商业假设", "验证假设", "需求验证", "市场验证",
    "产品验证", "MVP验证", "构思MVP", "设计MVP", "MVP设计", "最小可行实验",
    "mvp验证", "构思mvp", "设计mvp", "mvp设计",
    "试卖", "预售", "收费验证", "转化路径", "成交路径", "获客成交",
    "获客", "线索承接", "承接成交", "产品化", "商业闭环", "商业实验",
    "查资料", "研究一下", "找资料", "找来源", "引用来源", "核实", "事实核查",
    "市场调研", "行业调研", "竞品分析", "行业分析", "市场规模", "客户画像",
    "用户画像", "卖点分析", "定价调研", "菲律宾市场", "报告", "调研报告",
    "写文章", "写公众号", "改文章", "润色", "排版", "标题", "成稿",
    "公众号草稿", "真人感", "爆款标题", "小标题", "重点标注",
    "做图", "封面图", "标题图", "做PPT", "幻灯片", "演示文稿", "图表",
    "网页设计", "界面", "UI", "交互", "原型", "设计稿", "视觉稿",
    "做个网站", "做个工具", "写代码", "修报错", "跑不起来", "报错",
    "安装依赖", "部署", "上线", "测试", "验收", "代码质量", "重构",
    "看不懂项目", "项目梳理", "代码地图", "代码知识图谱", "代码讲解",
    "找问题", "代码问题", "安全审查", "上传GitHub", "提交代码", "推送",
    "开源", "分支", "PR", "issue", "commit", "整理表格", "数据分析",
    "可视化", "Excel", "表格", "PDF", "整理PDF", "整理pdf", "网页转资料", "本地资料", "资料包",
    "抓取网页", "抓取公众号", "保存网页", "文档提取", "自动化", "定时",
    "提醒", "监控", "MCP", "插件", "hook", "配置", "token", "密钥",
    "权限", "隐私", "备份",
]

PLACEHOLDER_LIST_VALUES = {
    "",
    "-",
    "none",
    "n/a",
    "na",
    "nil",
    "null",
    "not applicable",
    "no",
    "无",
    "没有",
    "无遗漏",
    "无需",
}

STATUS_SUFFIXES = {
    "pending",
    "planned",
    "todo",
    "blocked",
    "later",
    "deferred",
    "maybe",
}

SKILL_ALIASES = {
    "skills_auto_router": ROUTER_CANONICAL_ID,
    "skill_auto_router": ROUTER_CANONICAL_ID,
    "skills-auto-router": ROUTER_CANONICAL_ID,
    "skill-auto-router": ROUTER_CANONICAL_ID,
    "auto skill router": ROUTER_CANONICAL_ID,
    "skill auto router": ROUTER_CANONICAL_ID,
    "skill-router-cartographer": ROUTER_CANONICAL_ID,
    "skill router cartographer": ROUTER_CANONICAL_ID,
    "skill-router": ROUTER_CANONICAL_ID,
    "skill router": ROUTER_CANONICAL_ID,
}

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


def router_identity() -> dict[str, object]:
    return {
        "canonical_skill_id": ROUTER_CANONICAL_ID,
        "display_name": ROUTER_DISPLAY_NAME,
        "repo_slug": ROUTER_REPO_SLUG,
        "legacy_skill_id": ROUTER_LEGACY_ID,
        "aliases": sorted(SKILL_ALIASES),
    }


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


def raw_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",")]
    if isinstance(value, list):
        return [str(item).strip() for item in value]
    return [str(value).strip()]


def normalize_skill_item(value: object, known_names: set[str] | None = None) -> tuple[str | None, str | None]:
    """Return a clean skill name plus an optional data-quality note."""

    text = str(value).strip().strip("`").strip('"').strip("'")
    text = re.sub(r"\s+", " ", text)
    key = text.lower()
    if key == ROUTER_CANONICAL_ID:
        return key, None
    if key in PLACEHOLDER_LIST_VALUES:
        return None, f"placeholder:{text or '<empty>'}"
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key], f"alias:{text}->{SKILL_ALIASES[key]}"

    known_names = known_names or set()
    if known_names and key in known_names:
        return key, None

    parts = key.split()
    if len(parts) > 1:
        if parts[-1] in STATUS_SUFFIXES:
            base = " ".join(parts[:-1])
            if not known_names or base in known_names or "-" in base:
                normalized_base = SKILL_ALIASES.get(base, base)
                return normalized_base, f"status-suffix:{text}->{normalized_base} ({parts[-1]})"
        first = parts[0]
        if known_names and first in known_names:
            normalized_first = SKILL_ALIASES.get(first, first)
            return normalized_first, f"extra-words:{text}->{normalized_first}"
        if "-" in first or "_" in first:
            candidate = first.replace("_", "-")
            normalized_candidate = SKILL_ALIASES.get(candidate, candidate)
            return normalized_candidate, f"extra-words:{text}->{normalized_candidate}"
        return None, f"non-canonical:{text}"

    if not key:
        return None, "placeholder:<empty>"
    return key, None


def clean_skill_list(value: object, known_names: set[str] | None = None) -> tuple[list[str], list[str]]:
    cleaned: list[str] = []
    notes: list[str] = []
    seen: set[str] = set()
    for item in raw_list(value):
        name, note = normalize_skill_item(item, known_names)
        if note:
            notes.append(note)
        if name and name not in seen:
            seen.add(name)
            cleaned.append(name)
    return cleaned, notes


def load_trace_events(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if not path.exists():
        return [], []
    events: list[dict[str, object]] = []
    invalid: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            invalid.append({"line": line_number, "error": exc.msg})
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            invalid.append({"line": line_number, "error": "JSON value is not an object"})
    return events, invalid


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


def load_known_skill_names(out_dir: Path) -> set[str]:
    map_path = out_dir.expanduser().resolve() / "skill-map.json"
    names = {ROUTER_CANONICAL_ID, ROUTER_LEGACY_ID}
    if not map_path.exists():
        return names
    try:
        names.update(record.name.lower() for record in load_map(map_path))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return names
    return names
