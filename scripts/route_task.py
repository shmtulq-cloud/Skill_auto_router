from __future__ import annotations

import argparse
from pathlib import Path
import json

from host_profiles import known_hosts, profiles_for, skill_roots_for
from skill_router_common import (
    ROUTER_CANONICAL_ID,
    SKILL_ALIASES,
    default_out_dir,
    default_skills_dir,
    load_map,
    normalize_skill_item,
    scan_skills,
    tokenize,
    write_map,
)


VERIFICATION_HINTS = {
    "verification-loop",
    "verification-before-completion",
    "systematic-debugging",
    "tdd-workflow",
    "security-review",
}

CURATED_BOOSTS = [
    (ROUTER_CANONICAL_ID, ["skill", "auto", "router"], 64, "curated: public project name"),
    (ROUTER_CANONICAL_ID, ["skill_auto_router"], 64, "curated: repository slug"),
    (ROUTER_CANONICAL_ID, ["skills_auto_router"], 60, "curated: router alias"),
    (ROUTER_CANONICAL_ID, ["skill_auto_router"], 60, "curated: router alias"),
    (ROUTER_CANONICAL_ID, ["skill-auto-router"], 60, "curated: router alias"),
    (ROUTER_CANONICAL_ID, ["skills-auto-router"], 60, "curated: router alias"),
    (ROUTER_CANONICAL_ID, ["skill", "router"], 42, "curated: skill routing"),
    (ROUTER_CANONICAL_ID, ["auto", "router"], 42, "curated: auto skill router"),
    (ROUTER_CANONICAL_ID, ["健康报告"], 40, "curated: router health report"),
    (ROUTER_CANONICAL_ID, ["健康状态"], 40, "curated: router health status"),
    (ROUTER_CANONICAL_ID, ["路由健康"], 40, "curated: router health"),
    (ROUTER_CANONICAL_ID, ["技能路由"], 40, "curated: skill routing"),
    ("market-research", ["market", "research"], 28, "curated: market research"),
    ("deep-research", ["research"], 18, "curated: deep/cited research"),
    ("deep-research", ["cited"], 12, "curated: citations requested"),
    ("research-ops", ["source"], 16, "curated: evidence/source discipline"),
    ("research-ops", ["cited"], 14, "curated: evidence/source discipline"),
    ("spec-driven-vibe-coding", ["spec"], 24, "curated: spec-driven work"),
    ("spec-driven-vibe-coding", ["spec-in"], 30, "curated: spec-in work"),
    ("product-lens", ["product"], 12, "curated: product framing"),
    ("product-capability", ["product"], 12, "curated: product capability"),
    ("creative-director", ["design"], 14, "curated: visual direction"),
    ("design-brief", ["design"], 12, "curated: design brief"),
    ("artifacts-builder", ["visual"], 10, "curated: artifact building"),
    ("wechat-director", ["公众号"], 36, "curated: WeChat visual direction"),
    ("wechat-director", ["配图"], 34, "curated: WeChat article illustrations"),
    ("wechat-director", ["生图"], 28, "curated: image generation for WeChat visuals"),
    ("wechat-director", ["插图"], 24, "curated: article illustrations"),
    ("wechat-director", ["封面"], 18, "curated: article cover visual"),
    ("imagegen", ["生图"], 24, "curated: bitmap image generation"),
    ("imagegen", ["图片"], 18, "curated: bitmap image generation"),
    ("imagegen", ["插图"], 14, "curated: illustration generation"),
    ("poster-hero", ["封面"], 18, "curated: cover/poster image"),
    ("market-research", ["市场调研"], 52, "curated: market research in Chinese"),
    ("market-research", ["行业调研"], 48, "curated: industry research in Chinese"),
    ("market-research", ["竞品分析"], 50, "curated: competitive analysis in Chinese"),
    ("market-research", ["行业分析"], 42, "curated: industry analysis in Chinese"),
    ("market-research", ["市场规模"], 42, "curated: market sizing"),
    ("market-research", ["客户画像"], 32, "curated: customer profile research"),
    ("market-research", ["用户画像"], 32, "curated: user profile research"),
    ("market-research", ["卖点分析"], 28, "curated: selling-point analysis"),
    ("deep-research", ["查资料"], 34, "curated: ordinary-language research"),
    ("deep-research", ["查一下"], 26, "curated: ordinary-language research"),
    ("deep-research", ["研究一下"], 32, "curated: ordinary-language research"),
    ("deep-research", ["找资料"], 32, "curated: source search"),
    ("research-ops", ["找来源"], 34, "curated: source discipline"),
    ("research-ops", ["引用来源"], 36, "curated: citation discipline"),
    ("research-ops", ["核实"], 30, "curated: fact checking"),
    ("anything-to-local-data", ["网页转资料"], 58, "curated: capture web content locally"),
    ("anything-to-local-data", ["本地资料"], 48, "curated: local data package"),
    ("anything-to-local-data", ["资料包"], 46, "curated: local data package"),
    ("anything-to-local-data", ["抓取网页"], 54, "curated: scrape webpage into local data"),
    ("anything-to-local-data", ["抓取公众号"], 58, "curated: capture WeChat article locally"),
    ("anything-to-local-data", ["保存网页"], 50, "curated: save webpage locally"),
    ("anything-to-local-data", ["文档提取"], 42, "curated: document extraction"),
    ("anything-to-local-data", ["pdf", "资料包"], 74, "curated: turn PDF into local data package"),
    ("anything-to-local-data", ["pdf", "本地"], 58, "curated: keep PDF data local"),
    ("anything-to-local-data", ["整理pdf"], 62, "curated: organize PDF into local data"),
    ("article-writing", ["写文章"], 42, "curated: article writing"),
    ("article-writing", ["改文章"], 38, "curated: article editing"),
    ("article-writing", ["润色"], 34, "curated: prose polishing"),
    ("copywriting", ["标题"], 24, "curated: headline/copywriting"),
    ("copywriting", ["爆款标题"], 38, "curated: headline/copywriting"),
    ("content-engine", ["公众号草稿"], 36, "curated: content workflow"),
    ("writing-shape", ["真人感"], 32, "curated: human-feeling article shaping"),
    ("writing-shape", ["重点标注"], 30, "curated: highlight key passages"),
    ("wechat-director", ["写公众号"], 38, "curated: WeChat article workflow"),
    ("wechat-director", ["公众号草稿"], 42, "curated: WeChat draft workflow"),
    ("imagegen", ["做图"], 34, "curated: ordinary-language image generation"),
    ("imagegen", ["画图"], 30, "curated: ordinary-language image generation"),
    ("poster-hero", ["封面图"], 36, "curated: cover image"),
    ("poster-hero", ["标题图"], 34, "curated: title image"),
    ("pptx", ["做PPT"], 42, "curated: presentation creation"),
    ("pptx", ["幻灯片"], 36, "curated: slides creation"),
    ("pptx-generator", ["演示文稿"], 36, "curated: presentation generation"),
    ("data-report", ["图表"], 28, "curated: chart/report"),
    ("data-report", ["可视化"], 34, "curated: visualization/report"),
    ("frontend-design", ["网页设计"], 42, "curated: web UI design"),
    ("frontend-design", ["界面"], 26, "curated: UI design"),
    ("frontend-design", ["ui"], 26, "curated: UI design"),
    ("prototype", ["原型"], 32, "curated: prototype"),
    ("frontend-dev", ["做个网站"], 46, "curated: build a website"),
    ("frontend-dev", ["做个工具"], 34, "curated: build a frontend tool"),
    ("frontend-dev", ["写代码"], 24, "curated: code implementation"),
    ("systematic-debugging", ["修报错"], 50, "curated: debugging for beginners"),
    ("systematic-debugging", ["跑不起来"], 50, "curated: app does not run"),
    ("systematic-debugging", ["报错"], 36, "curated: error debugging"),
    ("tdd-workflow", ["测试"], 24, "curated: testing"),
    ("verification-loop", ["验收"], 36, "curated: acceptance verification"),
    ("deployment-patterns", ["部署"], 36, "curated: deployment"),
    ("deploy-pipeline", ["上线"], 34, "curated: release/deploy"),
    ("codebase-onboarding", ["看不懂项目"], 54, "curated: codebase onboarding"),
    ("codebase-onboarding", ["项目梳理"], 50, "curated: project orientation"),
    ("code-tour", ["代码讲解"], 42, "curated: code walkthrough"),
    ("knowledge-ops", ["代码知识图谱"], 54, "curated: code knowledge graph"),
    ("knowledge-ops", ["知识图谱"], 32, "curated: knowledge graph"),
    ("repo-scan", ["代码地图"], 52, "curated: repo map"),
    ("chinese-code-review", ["代码审查"], 44, "curated: code review"),
    ("chinese-code-review", ["代码审核"], 44, "curated: code review"),
    ("plankton-code-quality", ["代码质量"], 36, "curated: code quality review"),
    ("github-ops", ["上传github"], 50, "curated: GitHub operations"),
    ("github-ops", ["github"], 22, "curated: GitHub operations"),
    ("git-workflow", ["提交代码"], 42, "curated: git commit workflow"),
    ("git-workflow", ["推送"], 34, "curated: git push workflow"),
    ("git-workflow", ["分支"], 30, "curated: branch workflow"),
    ("git-workflow", ["commit"], 28, "curated: commit workflow"),
    ("github-ops", ["pr"], 30, "curated: pull request workflow"),
    ("github-ops", ["issue"], 30, "curated: issue workflow"),
    ("opensource-pipeline", ["开源"], 38, "curated: open-source publishing"),
    ("opensource-pipeline", ["github", "开源"], 60, "curated: publish repository as open source"),
    ("data-report", ["数据分析"], 42, "curated: data analysis report"),
    ("spreadsheet-formula-helper", ["excel"], 36, "curated: spreadsheet work"),
    ("spreadsheet-formula-helper", ["表格"], 30, "curated: spreadsheet work"),
    ("pdf", ["pdf"], 30, "curated: PDF work"),
    ("automation-audit-ops", ["自动化"], 30, "curated: automation workflow"),
    ("automation-audit-ops", ["定时"], 28, "curated: scheduled automation"),
    ("automation-audit-ops", ["提醒"], 28, "curated: reminders/automation"),
    ("canary-watch", ["监控"], 28, "curated: monitoring"),
    ("mcp-builder", ["mcp"], 34, "curated: MCP builder"),
    ("mcp-server-patterns", ["插件"], 22, "curated: plugin/MCP patterns"),
    ("mcp-builder", ["配置"], 18, "curated: configuration help"),
    ("security-review", ["token"], 30, "curated: token/security review"),
    ("security-review", ["密钥"], 34, "curated: secret/security review"),
    ("security-review", ["权限"], 30, "curated: permission/security review"),
    ("security-review", ["隐私"], 34, "curated: privacy/security review"),
    ("opc-orchestrator", ["一人企业"], 40, "curated: one-person company methodology"),
    ("opc-orchestrator", ["一人公司"], 40, "curated: one-person company methodology"),
    ("opc-orchestrator", ["个人商业化"], 34, "curated: personal business workflow"),
    ("opc-orchestrator", ["个人业务"], 30, "curated: personal business workflow"),
    ("opc-orchestrator", ["建盘"], 44, "curated: OPC build-up workflow"),
    ("opc-orchestrator", ["资源盘点", "利基定位"], 36, "curated: OPC stage sequence"),
    ("opc-orchestrator", ["价值主张", "商业模式"], 30, "curated: OPC strategy sequence"),
    ("opc-orchestrator", ["mvp", "转化闭环"], 30, "curated: OPC validation sequence"),
    ("opc-orchestrator", ["一步步"], 24, "curated: guided workflow"),
    ("opc-orchestrator", ["商业验证"], 52, "curated: OPC business validation workflow"),
    ("opc-orchestrator", ["商业验证", "mvp"], 78, "curated: broad OPC validation workflow with MVP"),
    ("opc-orchestrator", ["商业验证", "试卖"], 54, "curated: broad OPC validation workflow with selling test"),
    ("opc-orchestrator", ["我们一起", "mvp"], 36, "curated: guided OPC workflow request"),
    ("opc-orchestrator", ["业务验证"], 48, "curated: OPC business validation workflow"),
    ("opc-orchestrator", ["商业假设"], 44, "curated: OPC business hypothesis workflow"),
    ("opc-orchestrator", ["商业实验"], 42, "curated: OPC business experiment workflow"),
    ("opc-orchestrator", ["产品化"], 38, "curated: productizing personal business"),
    ("opc-orchestrator", ["商业闭环"], 42, "curated: OPC business loop workflow"),
    ("opc-orchestrator", ["副业"], 30, "curated: side business workflow"),
    ("opc-resource-audit", ["资源盘点"], 62, "curated: OPC resource audit stage"),
    ("opc-niche-positioning", ["利基定位"], 62, "curated: OPC niche positioning stage"),
    ("opc-niche-positioning", ["市场验证"], 34, "curated: validate market and niche"),
    ("opc-niche-positioning", ["需求验证"], 34, "curated: validate demand and niche"),
    ("opc-value-proposition", ["价值主张"], 62, "curated: OPC value proposition stage"),
    ("opc-business-model-design", ["商业模式"], 62, "curated: OPC business model stage"),
    ("opc-business-model-design", ["精益画布"], 58, "curated: OPC lean canvas stage"),
    ("opc-business-model-design", ["收费验证"], 36, "curated: pricing and business-model validation"),
    ("opc-mvp-designer", ["mvp"], 62, "curated: OPC MVP stage"),
    ("opc-mvp-designer", ["最小验证"], 58, "curated: OPC MVP experiment stage"),
    ("opc-mvp-designer", ["mvp验证"], 70, "curated: OPC MVP validation stage"),
    ("opc-mvp-designer", ["构思mvp"], 70, "curated: OPC MVP design stage"),
    ("opc-mvp-designer", ["设计mvp"], 70, "curated: OPC MVP design stage"),
    ("opc-mvp-designer", ["mvp设计"], 70, "curated: OPC MVP design stage"),
    ("opc-mvp-designer", ["验证假设"], 58, "curated: OPC experiment hypothesis stage"),
    ("opc-mvp-designer", ["产品验证"], 50, "curated: OPC product validation stage"),
    ("opc-mvp-designer", ["最小可行实验"], 64, "curated: OPC smallest viable experiment"),
    ("opc-mvp-designer", ["试卖"], 42, "curated: OPC selling-as-validation"),
    ("opc-mvp-designer", ["预售"], 42, "curated: OPC presale-as-validation"),
    ("opc-conversion-loop", ["转化闭环"], 62, "curated: OPC conversion loop stage"),
    ("opc-conversion-loop", ["转化路径"], 66, "curated: OPC conversion path stage"),
    ("opc-conversion-loop", ["成交路径"], 62, "curated: OPC purchase path stage"),
    ("opc-conversion-loop", ["获客成交"], 62, "curated: OPC acquisition to purchase stage"),
    ("opc-conversion-loop", ["获客"], 38, "curated: OPC acquisition stage"),
    ("opc-conversion-loop", ["线索承接"], 58, "curated: OPC lead capture stage"),
    ("opc-conversion-loop", ["承接成交"], 58, "curated: OPC lead-to-purchase stage"),
    ("opc-asset-ops", ["资产沉淀"], 70, "curated: OPC asset operations stage"),
    ("opc-dashboard-review", ["经营复盘"], 76, "curated: OPC dashboard review stage"),
    ("opc-dashboard-review", ["运营复盘"], 70, "curated: OPC operating review stage"),
    ("opc-dashboard-review", ["运营卡住"], 66, "curated: OPC operating bottleneck review"),
    ("verification-loop", ["verify"], 16, "curated: verification"),
    ("verification-loop", ["complete"], 10, "curated: completion check"),
    ("verification-loop", ["report"], 8, "curated: report verification"),
    ("verification-loop", ["spec"], 8, "curated: spec verification"),
    ("systematic-debugging", ["bug"], 22, "curated: debugging"),
    ("tdd-workflow", ["test"], 16, "curated: testing/TDD"),
    ("keep-codex-fast", ["codex", "slow"], 30, "curated: Codex maintenance"),
    ("follow-builders", ["digest"], 24, "curated: builder digest"),
    ("follow-builders", ["track"], 12, "curated: information tracking"),
]

QUERY_EXPANSIONS = [
    (
        ["代码索引"],
        ["source", "asset", "audit", "file", "module", "repository", "codebase", "index", "map"],
    ),
    (
        ["知识图谱"],
        ["knowledge", "graph", "memory", "mcp", "relations", "relationship", "retrieval", "semantic"],
    ),
    (
        ["全量阅读"],
        ["scan", "audit", "summary", "map", "overview", "onboarding", "recall", "memory"],
    ),
    (
        ["全量扫描"],
        ["scan", "audit", "summary", "map", "overview", "onboarding", "recall", "memory"],
    ),
    (
        ["模块关系"],
        ["module", "architecture", "dependency", "relationship", "map", "graph"],
    ),
    (
        ["依赖图"],
        ["dependency", "graph", "architecture", "module", "map"],
    ),
    (
        ["调用图"],
        ["call", "graph", "dependency", "architecture", "module", "map"],
    ),
    (
        ["接手项目"],
        ["onboarding", "unfamiliar", "codebase", "architecture", "entry", "conventions"],
    ),
    (
        ["理解代码"],
        ["onboarding", "codebase", "architecture", "entry", "map", "walkthrough"],
    ),
    (
        ["项目记忆"],
        ["memory", "notes", "save", "recall", "knowledge", "project", "context"],
    ),
    (
        ["架构记忆"],
        ["architecture", "memory", "notes", "knowledge", "context", "decision"],
    ),
    (
        ["踩坑记录"],
        ["notes", "gotchas", "recall", "remember", "save", "knowledge"],
    ),
    (
        ["增量审查"],
        ["review", "diff", "changes", "incremental", "verification", "security", "tests"],
    ),
    (
        ["增量审核"],
        ["review", "diff", "changes", "incremental", "verification", "security", "tests"],
    ),
]


NO_SKILL_DIRECT_HINTS = [
    "不用上网",
    "不要上网",
    "不需要上网",
    "直接回答",
    "简单解释",
    "解释一下",
    "什么意思",
    "是什么",
    "这句话",
    "这一句",
    "一句话",
    "单句",
    "短句",
    "改得更自然",
    "改自然",
    "润色一下这句话",
    "想5个",
    "想 5 个",
    "给我5个",
    "给我 5 个",
    "列5个",
    "列 5 个",
    "几个关键词",
    "关键词组合",
    "取个名字",
    "起个名字",
]

WORKFLOW_SIGNALS = [
    "项目",
    "代码",
    "代码库",
    "仓库",
    "文件",
    "目录",
    "安装",
    "配置",
    "修复",
    "报错",
    "跑不起来",
    "测试",
    "部署",
    "上线",
    "github",
    "开源",
    "commit",
    "issue",
    "pr",
    "调研",
    "研究",
    "来源",
    "引用",
    "市场",
    "竞品",
    "报告",
    "资料包",
    "pdf",
    "网页",
    "抓取",
    "公众号",
    "文章",
    "排版",
    "封面",
    "插图",
    "图片",
    "生图",
    "ppt",
    "幻灯片",
    "网站",
    "工具",
    "mvp",
    "商业验证",
    "一人企业",
    "一人公司",
    "复盘",
    "自动化",
    "mcp",
]

ACTIONABLE_SKILL_HINTS = [
    "查资料",
    "找资料",
    "找来源",
    "引用",
    "核实",
    "调研",
    "竞品分析",
    "市场规模",
    "报告",
    "文件",
    "项目",
    "代码",
    "代码库",
    "修复",
    "修报错",
    "跑不起来",
    "安装",
    "配置",
    "部署",
    "上线",
    "上传",
    "推送",
    "提交",
    "开源",
    "资料包",
    "抓取",
    "保存网页",
    "网页转资料",
    "做图",
    "生图",
    "封面图",
    "做ppt",
    "做个网站",
    "做个工具",
    "商业验证",
    "构思mvp",
    "设计mvp",
    "mvp验证",
    "复盘",
    "自动化",
    "监控",
]

HEAVY_SIGNALS = [
    "全盘",
    "完整",
    "系统",
    "从零",
    "一步步",
    "市场调研",
    "竞品分析",
    "代码地图",
    "知识图谱",
    "开源",
    "做个网站",
    "做个工具",
    "资料包",
    "商业验证",
    "一人企业",
    "spec",
    "spec-in",
    "mvp",
]

FORCE_SKILL_HINTS = [
    "@",
    "用skill",
    "使用skill",
    "调用skill",
    "按skill",
    "使用技能",
    "调用技能",
    "按这个技能",
    "启动",
]


def has_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def count_matches(text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term in text)


def route_gate(query_text: str, top_score: int, top_count: int) -> dict[str, object]:
    """Decide whether using a skill is worth the overhead for this task."""

    direct = has_any(query_text, NO_SKILL_DIRECT_HINTS)
    workflow_count = count_matches(query_text, WORKFLOW_SIGNALS)
    heavy_count = count_matches(query_text, HEAVY_SIGNALS)
    force_skill = has_any(query_text, FORCE_SKILL_HINTS)

    if force_skill:
        return {
            "use_skill": True,
            "route_level": "workflow",
            "reason": "user explicitly asked to use or start a skill/workflow",
            "signals": {"direct": direct, "workflow": workflow_count, "heavy": heavy_count, "top_score": top_score},
        }

    if direct and not has_any(query_text, ACTIONABLE_SKILL_HINTS):
        return {
            "use_skill": False,
            "route_level": "none",
            "reason": "light direct-answer task; skill overhead is likely unnecessary",
            "signals": {"direct": direct, "workflow": workflow_count, "heavy": heavy_count, "top_score": top_score},
        }

    if top_count == 0 or (top_score < 12 and workflow_count == 0):
        return {
            "use_skill": False,
            "route_level": "none",
            "reason": "no strong workflow or installed-skill signal",
            "signals": {"direct": direct, "workflow": workflow_count, "heavy": heavy_count, "top_score": top_score},
        }

    if heavy_count >= 1 or workflow_count >= 3 or top_score >= 100:
        level = "heavy"
        reason = "multi-step or high-confidence workflow task"
    elif workflow_count >= 1 or top_score >= 35:
        level = "workflow"
        reason = "task has a clear workflow or deliverable signal"
    else:
        level = "light"
        reason = "a lightweight skill may help, but avoid loading extra skills"

    return {
        "use_skill": True,
        "route_level": level,
        "reason": reason,
        "signals": {"direct": direct, "workflow": workflow_count, "heavy": heavy_count, "top_score": top_score},
    }


def expand_query_tokens(query_tokens: set[str], query_text: str) -> set[str]:
    expanded = set(query_tokens)
    for terms, additions in QUERY_EXPANSIONS:
        if all(term in query_tokens or term in query_text for term in terms):
            expanded.update(additions)
    return expanded


def score_skill(
    query_tokens: set[str],
    query_text: str,
    skill,
    raw_query_tokens: set[str] | None = None,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    name = skill.name.lower()
    canonical_name = SKILL_ALIASES.get(name, name)
    description = skill.description.lower()
    keywords = set(skill.keywords)
    raw_query_tokens = raw_query_tokens or query_tokens

    if name in query_text:
        score += 20
        reasons.append("name mentioned")

    overlap = sorted(query_tokens & keywords)
    if overlap:
        score += min(20, len(overlap) * 3)
        reasons.append("keyword overlap: " + ", ".join(overlap[:6]))

    for topic in skill.topics:
        if topic in query_tokens or topic in query_text:
            score += 6
            reasons.append(f"topic: {topic}")

    for trigger in skill.triggers:
        trigger_tokens = set(tokenize(trigger))
        if query_tokens & trigger_tokens:
            score += min(8, len(query_tokens & trigger_tokens) * 2)

    for skill_name, terms, boost, reason in CURATED_BOOSTS:
        if canonical_name == skill_name and all(term in raw_query_tokens or term in query_text for term in terms):
            score += boost
            reasons.append(reason)

    return score, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a task to likely installed skills.")
    parser.add_argument("task", nargs="+")
    parser.add_argument("--map", default=str(default_out_dir() / "skill-map.json"))
    parser.add_argument("--host", default="codex", choices=known_hosts() + ["all"])
    parser.add_argument("--project", default=".", help="Project folder used to resolve project-local skill roots.")
    parser.add_argument("--skills-dir", action="append", help="Explicit skill directory. Can be passed more than once.")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    query_text = " ".join(args.task).lower()
    raw_query_tokens = set(tokenize(query_text))
    query_tokens = expand_query_tokens(raw_query_tokens, query_text)
    map_path = Path(args.map).expanduser().resolve()

    if args.refresh or not map_path.exists():
        project = Path(args.project).expanduser().resolve()
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
        write_map(records, map_path.parent)
    else:
        records = load_map(map_path)

    ranked_by_name = {}
    for skill in records:
        score, reasons = score_skill(query_tokens, query_text, skill, raw_query_tokens)
        if score > 0:
            key = normalize_skill_item(skill.name)[0] or skill.name.lower()
            item = {"skill": skill, "score": score, "reasons": reasons}
            if key not in ranked_by_name or score > ranked_by_name[key]["score"]:
                ranked_by_name[key] = item
    ranked = list(ranked_by_name.values())
    ranked.sort(key=lambda item: (-item["score"], item["skill"].name.lower()))
    gate = route_gate(query_text, ranked[0]["score"] if ranked else 0, len(ranked))
    if not bool(gate["use_skill"]):
        ranked = []
    top = ranked[: args.limit]

    def route_name(name: str) -> str:
        return normalize_skill_item(name)[0] or name

    primary = route_name(top[0]["skill"].name) if top else None
    verification = next((route_name(item["skill"].name) for item in top if route_name(item["skill"].name) in VERIFICATION_HINTS), None)
    if verification is None:
        verification = next((route_name(item["skill"].name) for item in ranked if route_name(item["skill"].name) in VERIFICATION_HINTS), None)

    payload = {
        "task": " ".join(args.task),
        "route_level": gate["route_level"],
        "gate": gate,
        "primary": primary,
        "verification": verification,
        "recommended": [
            {
                "name": route_name(item["skill"].name),
                "source_name": item["skill"].name,
                "folder": item["skill"].folder,
                "score": item["score"],
                "topics": item["skill"].topics,
                "reasons": item["reasons"],
                "description": item["skill"].description,
            }
            for item in top
        ],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"task={payload['task']}")
        print(f"route_level={payload['route_level']}")
        print(f"gate_reason={payload['gate']['reason']}")
        print(f"primary={primary or 'none'}")
        print(f"verification={verification or 'none'}")
        print("recommended:")
        for item in payload["recommended"]:
            print(f"- {item['name']} score={item['score']} reasons={'; '.join(item['reasons'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
