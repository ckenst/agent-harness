#!/usr/bin/env python3
"""Portable, dependency-free installer for the personal agent harness."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

MANAGED_MARKER = "Managed: agent-harness/v1"
STATE_VERSION = 1
AGENT_ORDER = ("codex", "claude", "copilot")
INSTRUCTION_TARGETS = {
    "codex": Path(".codex/AGENTS.md"),
    "claude": Path(".claude/CLAUDE.md"),
    "copilot": Path(".copilot/copilot-instructions.md"),
}


@dataclasses.dataclass
class Options:
    profile: str
    home: Path
    with_agents: List[str]
    without_agents: List[str]
    dry_run: bool
    json: bool = False


@dataclasses.dataclass
class Plan:
    profile: str
    agents: Tuple[str, ...]
    skills: Tuple[str, ...]
    files: Dict[Path, bytes]


@dataclasses.dataclass
class Result:
    changed: int = 0
    unchanged: int = 0
    backed_up: int = 0
    removed: int = 0
    skipped: List[Path] = dataclasses.field(default_factory=list)
    actions: List[str] = dataclasses.field(default_factory=list)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_json(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _split_agent_values(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    for value in values:
        result.extend(item.strip().lower() for item in value.split(",") if item.strip())
    unknown = sorted(set(result) - set(AGENT_ORDER))
    if unknown:
        raise ValueError("unknown agent(s): " + ", ".join(unknown))
    return result


def _selected_agents(profile: Mapping[str, object], options: Options) -> Tuple[str, ...]:
    selected = set(str(value) for value in profile["default_agents"])
    selected.update(_split_agent_values(options.with_agents))
    selected.difference_update(_split_agent_values(options.without_agents))
    return tuple(agent for agent in AGENT_ORDER if agent in selected)


def _markdown_header(source: str, profile: str) -> str:
    return (
        f"<!-- Generated file. Source: agent-harness/{source}. "
        f"Profile: {profile}. {MANAGED_MARKER}. -->\n\n"
    )


def _decorate_skill(content: bytes, source: str, profile: str, filename: str) -> bytes:
    text = content.decode("utf-8")
    comment = (
        f"Generated file. Source: agent-harness/{source}. "
        f"Profile: {profile}. {MANAGED_MARKER}."
    )
    if filename == "SKILL.md" and text.startswith("---\n"):
        closing = text.find("\n---\n", 4)
        if closing == -1:
            raise ValueError(f"invalid skill frontmatter in {source}")
        position = closing + len("\n---\n")
        return (text[:position] + f"\n<!-- {comment} -->\n" + text[position:]).encode("utf-8")
    if filename.endswith((".yaml", ".yml")):
        return (f"# {comment}\n" + text).encode("utf-8")
    if filename.endswith(".md"):
        return (f"<!-- {comment} -->\n\n" + text).encode("utf-8")
    if text.startswith("#!"):
        first, separator, rest = text.partition("\n")
        return (first + separator + f"# {comment}\n" + rest).encode("utf-8")
    return content


def _instruction_content(root: Path, profile_data: Mapping[str, object], profile_name: str) -> bytes:
    policy_names = [str(item) for item in profile_data["policies"]]
    sources = " + ".join(f"policy/{name}" for name in policy_names)
    body = "\n\n".join(
        (root / "policy" / name).read_text(encoding="utf-8").strip()
        for name in policy_names
    )
    return (_markdown_header(sources, profile_name) + "# Personal Agent Instructions\n\n" + body + "\n").encode("utf-8")


def build_plan(root: Path, options: Options) -> Plan:
    profile_path = root / "profiles" / f"{options.profile}.json"
    if not profile_path.is_file():
        raise ValueError(f"unknown profile: {options.profile}")
    profile_data = _read_json(profile_path)
    agents = _selected_agents(profile_data, options)
    if not agents:
        raise ValueError("at least one agent must be selected")
    files: Dict[Path, bytes] = {}
    instructions = _instruction_content(root, profile_data, options.profile)
    for agent in agents:
        files[options.home / INSTRUCTION_TARGETS[agent]] = instructions
    skill_names: List[str] = []
    skill_targets: List[Path] = []
    if "codex" in agents or "copilot" in agents:
        skill_targets.append(options.home / ".agents" / "skills")
    if "claude" in agents:
        skill_targets.append(options.home / ".claude" / "skills")
    for group_value in profile_data["skill_groups"]:
        group = str(group_value)
        group_root = root / "skills" / group
        if not group_root.is_dir():
            continue
        for skill_root in sorted(path for path in group_root.iterdir() if path.is_dir()):
            if not (skill_root / "SKILL.md").is_file():
                continue
            skill_names.append(skill_root.name)
            for source_file in sorted(path for path in skill_root.rglob("*") if path.is_file()):
                relative = source_file.relative_to(skill_root)
                source_name = f"skills/{group}/{skill_root.name}/{relative.as_posix()}"
                content = _decorate_skill(source_file.read_bytes(), source_name, options.profile, source_file.name)
                for target_root in skill_targets:
                    files[target_root / skill_root.name / relative] = content
    return Plan(options.profile, agents, tuple(sorted(set(skill_names))), files)


def _is_managed(content: bytes) -> bool:
    return MANAGED_MARKER.encode("utf-8") in content[:4096]


def _backup_path(path: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    return path.with_name(f"{path.name}.agent-harness-backup-{stamp}")


def _write_file(path: Path, content: bytes, result: Result, dry_run: bool, replace_unmanaged: bool) -> None:
    if path.exists():
        if not path.is_file():
            result.skipped.append(path)
            result.actions.append(f"skip non-file {path}")
            return
        current = path.read_bytes()
        if current == content:
            result.unchanged += 1
            return
        if not _is_managed(current):
            if not replace_unmanaged:
                result.skipped.append(path)
                result.actions.append(f"skip unmanaged {path}")
                return
            backup = _backup_path(path)
            result.backed_up += 1
            result.actions.append(f"backup {path} -> {backup}")
            if not dry_run:
                shutil.copy2(str(path), str(backup))
    result.changed += 1
    result.actions.append(f"write {path}")
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _state_path(home: Path) -> Path:
    return home / ".agent-harness" / "manifest.json"


def _relative_to_home(path: Path, home: Path) -> str:
    return path.relative_to(home).as_posix()


def _load_state(home: Path) -> Mapping[str, object]:
    path = _state_path(home)
    if not path.is_file():
        return {"version": STATE_VERSION, "files": []}
    try:
        value = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {"version": STATE_VERSION, "files": []}
    if value.get("managed") != MANAGED_MARKER:
        return {"version": STATE_VERSION, "files": []}
    return value


def _remove_empty_parents(path: Path, stop: Path) -> None:
    parent = path.parent
    while parent != stop and parent.is_dir():
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def install(root: Path, options: Options) -> Result:
    plan = build_plan(root, options)
    result = Result()
    old_state = _load_state(options.home)
    old_entries = {
        str(entry["path"]): entry for entry in old_state.get("files", [])
        if isinstance(entry, dict) and "path" in entry and "sha256" in entry
    }
    new_relative = {_relative_to_home(path, options.home) for path in plan.files}
    for relative, entry in old_entries.items():
        if relative in new_relative:
            continue
        stale = options.home / relative
        if stale.is_file():
            stale_content = stale.read_bytes()
            if _sha256(stale_content) == entry["sha256"] and _is_managed(stale_content):
                result.removed += 1
                result.actions.append(f"remove stale {stale}")
                if not options.dry_run:
                    stale.unlink()
                    _remove_empty_parents(stale, options.home)
                continue
        if stale.exists():
            result.skipped.append(stale)
    for path, content in sorted(plan.files.items(), key=lambda item: str(item[0])):
        _write_file(path, content, result, options.dry_run, replace_unmanaged=True)
    manifest = {
        "managed": MANAGED_MARKER,
        "version": STATE_VERSION,
        "profile": plan.profile,
        "agents": list(plan.agents),
        "skills": list(plan.skills),
        "files": [
            {"path": _relative_to_home(path, options.home), "sha256": _sha256(content)}
            for path, content in sorted(plan.files.items(), key=lambda item: str(item[0]))
        ],
    }
    manifest_content = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    state_path = _state_path(options.home)
    if not options.dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        if not state_path.exists() or state_path.read_bytes() != manifest_content:
            state_path.write_bytes(manifest_content)
    return result


def verify(root: Path, options: Options, which: Callable[[str], Optional[str]] = shutil.which) -> Dict[str, object]:
    plan = build_plan(root, options)
    files: List[Dict[str, str]] = []
    ok = True
    for path, expected in sorted(plan.files.items(), key=lambda item: str(item[0])):
        if not path.is_file():
            status = "missing"
            ok = False
        elif path.read_bytes() == expected:
            status = "installed"
        elif _is_managed(path.read_bytes()):
            status = "managed-modified"
            ok = False
        else:
            status = "unmanaged"
            ok = False
        files.append({"path": "~/" + _relative_to_home(path, options.home), "status": status})
    return {
        "ok": ok,
        "platform": platform.system() or os.name,
        "profile": plan.profile,
        "agents": list(plan.agents),
        "skills": list(plan.skills),
        "files": files,
        "tools": {
            "vibium": "available" if which("vibium") else "missing",
            "mailinator-cli": "available" if which("mailinator-cli") else "missing",
        },
    }


def uninstall(root: Path, options: Options) -> Result:
    del root
    result = Result()
    state = _load_state(options.home)
    remaining: List[Mapping[str, str]] = []
    for entry in state.get("files", []):
        if not isinstance(entry, dict) or "path" not in entry or "sha256" not in entry:
            continue
        path = options.home / str(entry["path"])
        if not path.exists():
            continue
        content = path.read_bytes() if path.is_file() else b""
        if path.is_file() and _is_managed(content) and _sha256(content) == entry["sha256"]:
            result.removed += 1
            result.actions.append(f"remove {path}")
            if not options.dry_run:
                path.unlink()
                _remove_empty_parents(path, options.home)
        else:
            result.skipped.append(path)
            remaining.append(entry)
    state_path = _state_path(options.home)
    if not options.dry_run and state_path.exists():
        if remaining:
            updated = dict(state)
            updated["files"] = remaining
            state_path.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            state_path.unlink()
            _remove_empty_parents(state_path, options.home)
    return result


def _without_generated_header(text: str) -> str:
    if text.startswith("<!-- Generated file."):
        _, separator, remainder = text.partition("-->\n\n")
        if separator:
            return remainder
    return text


def bootstrap(root: Path, repository: Path, dry_run: bool, force: bool) -> Result:
    repository = repository.expanduser()
    if not repository.is_dir():
        raise ValueError(f"repository directory does not exist: {repository}")
    result = Result()
    template_agents = (root / "repo-template" / "AGENTS.md").read_text(encoding="utf-8")
    agents_path = repository / "AGENTS.md"
    if agents_path.is_file() and not _is_managed(agents_path.read_bytes()) and not force:
        canonical = agents_path.read_text(encoding="utf-8")
    else:
        canonical = template_agents
    outputs = {
        agents_path: (_markdown_header("repo-template/AGENTS.md", "repository") + _without_generated_header(template_agents)).encode("utf-8"),
        repository / "CLAUDE.md": (
            _markdown_header("repo-template/CLAUDE.md", "repository")
            + (root / "repo-template" / "CLAUDE.md").read_text(encoding="utf-8")
        ).encode("utf-8"),
        repository / ".github" / "copilot-instructions.md": (
            _markdown_header("repo-template/AGENTS.md", "repository")
            + "# GitHub Copilot Repository Instructions\n\n"
            + "The following content is materialized from the canonical `AGENTS.md`.\n\n"
            + _without_generated_header(canonical).strip() + "\n"
        ).encode("utf-8"),
    }
    for path, content in outputs.items():
        _write_file(path, content, result, dry_run, replace_unmanaged=force)
    return result


def _options_from_args(args: argparse.Namespace) -> Options:
    return Options(args.profile, Path(args.home).expanduser().resolve(), args.with_agents, args.without_agents, args.dry_run, getattr(args, "json", False))


def _add_common(parser: argparse.ArgumentParser, include_json: bool = False) -> None:
    parser.add_argument("--profile", choices=("work", "home"), default="home")
    parser.add_argument("--home", default=str(Path.home()), help=argparse.SUPPRESS)
    parser.add_argument("--with", dest="with_agents", action="append", default=[], metavar="AGENT")
    parser.add_argument("--without", dest="without_agents", action="append", default=[], metavar="AGENT")
    parser.add_argument("--dry-run", action="store_true")
    if include_json:
        parser.add_argument("--json", action="store_true")


def _print_result(result: Result) -> None:
    for action in result.actions:
        print(action)
    print(f"changed={result.changed} unchanged={result.unchanged} backed_up={result.backed_up} removed={result.removed} skipped={len(result.skipped)}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    install_parser = subparsers.add_parser("install", help="install or upgrade a profile")
    _add_common(install_parser)
    verify_parser = subparsers.add_parser("verify", help="report installed files, skills, and tools")
    _add_common(verify_parser, include_json=True)
    uninstall_parser = subparsers.add_parser("uninstall", help="remove unchanged managed files")
    _add_common(uninstall_parser)
    bootstrap_parser = subparsers.add_parser("bootstrap", help="add guidance to another repository")
    bootstrap_parser.add_argument("--repo", required=True)
    bootstrap_parser.add_argument("--force", action="store_true")
    bootstrap_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            _print_result(install(root, _options_from_args(args)))
        elif args.command == "verify":
            report = verify(root, _options_from_args(args))
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"platform={report['platform']} profile={report['profile']} ok={str(report['ok']).lower()}")
                print("agents=" + ",".join(report["agents"]))
                print("skills=" + ",".join(report["skills"]))
                for item in report["files"]:
                    print(f"{item['status']}: {item['path']}")
                for name, status in report["tools"].items():
                    print(f"tool {name}: {status}")
            return 0 if report["ok"] else 1
        elif args.command == "uninstall":
            _print_result(uninstall(root, _options_from_args(args)))
        else:
            _print_result(bootstrap(root, Path(args.repo), args.dry_run, args.force))
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
