from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class HostProfile:
    id: str
    display_name: str
    aliases: tuple[str, ...]
    project_instructions: tuple[str, ...]
    preferred_project_instruction: str
    global_instructions: tuple[str, ...]
    preferred_global_instruction: str
    skill_roots: tuple[str, ...]
    steering_frontmatter: str = ""
    note: str = ""


def home() -> Path:
    return Path.home()


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", home() / ".codex"))


PROFILES: dict[str, HostProfile] = {
    "universal": HostProfile(
        id="universal",
        display_name="Universal AGENTS.md",
        aliases=("agents", "agents.md", "portable"),
        project_instructions=("AGENTS.md",),
        preferred_project_instruction="AGENTS.md",
        global_instructions=("~/AGENTS.md",),
        preferred_global_instruction="~/AGENTS.md",
        skill_roots=(
            "~/.codex/skills",
            "~/.claude/skills",
            "~/.agent/skills",
            "~/.agents/skills",
        ),
        note="Portable baseline for tools that read AGENTS.md.",
    ),
    "codex": HostProfile(
        id="codex",
        display_name="OpenAI Codex",
        aliases=("openai-codex", "codex-cli"),
        project_instructions=("AGENTS.md", ".codex/instructions.md"),
        preferred_project_instruction="AGENTS.md",
        global_instructions=("~/.codex/AGENTS.md",),
        preferred_global_instruction="~/.codex/AGENTS.md",
        skill_roots=("~/.codex/skills",),
        note="Codex uses project AGENTS.md and user-level Codex instructions.",
    ),
    "claude-code": HostProfile(
        id="claude-code",
        display_name="Claude Code",
        aliases=("claude", "claude_code", "cc"),
        project_instructions=("CLAUDE.md", ".claude/CLAUDE.md", "AGENTS.md"),
        preferred_project_instruction="CLAUDE.md",
        global_instructions=("~/.claude/CLAUDE.md",),
        preferred_global_instruction="~/.claude/CLAUDE.md",
        skill_roots=("~/.claude/skills", ".claude/skills"),
        note="Claude Code project memory is CLAUDE.md or .claude/CLAUDE.md.",
    ),
    "kiro": HostProfile(
        id="kiro",
        display_name="Kiro",
        aliases=("kiro-ide", "kiro-web"),
        project_instructions=(".kiro/steering/skill-routing.md", "AGENTS.md"),
        preferred_project_instruction=".kiro/steering/skill-routing.md",
        global_instructions=("~/.kiro/steering/AGENTS.md", "~/.kiro/steering/skill-routing.md"),
        preferred_global_instruction="~/.kiro/steering/AGENTS.md",
        skill_roots=("~/.kiro/skills", ".kiro/skills", "~/.agent/skills"),
        steering_frontmatter="---\ninclusion: always\n---\n\n",
        note="Kiro steering files live under .kiro/steering; AGENTS.md is also supported.",
    ),
    "antigravity": HostProfile(
        id="antigravity",
        display_name="Google Antigravity",
        aliases=("google-antigravity", "ag"),
        project_instructions=("AGENTS.md", "GEMINI.md", ".agents/rules/skill-routing.md", ".agent/rules/skill-routing.md"),
        preferred_project_instruction="AGENTS.md",
        global_instructions=("~/.gemini/GEMINI.md",),
        preferred_global_instruction="~/.gemini/GEMINI.md",
        skill_roots=("~/.gemini/antigravity/skills", "~/.gemini/skills", ".agents/skills", ".agent/skills"),
        note="Prefer AGENTS.md for cross-tool portability; Antigravity also supports GEMINI.md, .agents/rules, and .agents/skills.",
    ),
    "opencode": HostProfile(
        id="opencode",
        display_name="OpenCode",
        aliases=("open-code", "open_code"),
        project_instructions=("AGENTS.md", "CLAUDE.md", ".opencode/AGENTS.md"),
        preferred_project_instruction="AGENTS.md",
        global_instructions=("~/.config/opencode/AGENTS.md", "~/.claude/CLAUDE.md"),
        preferred_global_instruction="~/.config/opencode/AGENTS.md",
        skill_roots=(
            "~/.config/opencode/skills",
            "~/.claude/skills",
            "~/.agents/skills",
            ".opencode/skills",
            ".claude/skills",
            ".agents/skills",
        ),
        note="OpenCode reads project AGENTS.md, then Claude Code fallbacks such as CLAUDE.md and ~/.claude/skills unless disabled.",
    ),
    "openclaw": HostProfile(
        id="openclaw",
        display_name="OpenClaw",
        aliases=("xiaolongxia", "little-lobster"),
        project_instructions=("AGENTS.md", ".openclaw/AGENTS.md"),
        preferred_project_instruction="AGENTS.md",
        global_instructions=("~/.openclaw/AGENTS.md",),
        preferred_global_instruction="~/.openclaw/AGENTS.md",
        skill_roots=("~/.openclaw/skills", "~/.agents/skills", ".openclaw/skills"),
        note="Keep persona files such as SOUL.md focused on identity; put routing rules in AGENTS.md.",
    ),
    "hermes": HostProfile(
        id="hermes",
        display_name="Hermes Agent",
        aliases=("aimashi", "hermes-agent"),
        project_instructions=("AGENTS.md", "HERMES.md", ".hermes/AGENTS.md"),
        preferred_project_instruction="AGENTS.md",
        global_instructions=("~/.hermes/AGENTS.md", "~/.hermes/HERMES.md"),
        preferred_global_instruction="~/.hermes/AGENTS.md",
        skill_roots=("~/.hermes/skills", "~/.agents/skills", ".hermes/skills"),
        note="Hermes can use skills_list and skill_view; AGENTS.md keeps routing portable.",
    ),
}


ALIASES: dict[str, str] = {}
for profile_id, profile in PROFILES.items():
    ALIASES[profile_id] = profile_id
    for alias in profile.aliases:
        ALIASES[alias] = profile_id


def normalize_host(host: str | None) -> str:
    if not host:
        return "codex"
    key = host.strip().lower()
    if key == "all":
        return "all"
    if key not in ALIASES:
        raise ValueError(f"Unknown host: {host}")
    return ALIASES[key]


def profile_for(host: str | None) -> HostProfile:
    host_id = normalize_host(host)
    if host_id == "all":
        raise ValueError("Use profiles_for('all') when checking every host.")
    return PROFILES[host_id]


def profiles_for(host: str | None) -> list[HostProfile]:
    host_id = normalize_host(host)
    if host_id == "all":
        return [PROFILES[key] for key in sorted(PROFILES)]
    return [PROFILES[host_id]]


def resolve_path(root: Path, candidate: str) -> Path:
    expanded = Path(candidate).expanduser()
    if expanded.is_absolute():
        return expanded
    return root / expanded


def instruction_candidates(root: Path, profile: HostProfile, scope: str) -> list[Path]:
    if scope == "global":
        return [resolve_path(home(), item) for item in profile.global_instructions]
    return [resolve_path(root, item) for item in profile.project_instructions]


def preferred_instruction(root: Path, profile: HostProfile, scope: str) -> Path:
    if scope == "global":
        return resolve_path(home(), profile.preferred_global_instruction)
    return resolve_path(root, profile.preferred_project_instruction)


def find_instruction(root: Path, profile: HostProfile, scope: str = "project") -> Path:
    for candidate in instruction_candidates(root, profile, scope):
        if candidate.exists():
            return candidate
    return preferred_instruction(root, profile, scope)


def skill_roots_for(profile: HostProfile, project: Path | None = None) -> list[Path]:
    root = project or Path.cwd()
    paths = [resolve_path(root, item) for item in profile.skill_roots]
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path.resolve() if path.exists() else path)
        if key not in seen:
            seen.add(key)
            deduped.append(path)
    return deduped


def known_hosts() -> list[str]:
    return sorted(PROFILES)
