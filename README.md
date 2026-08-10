# Personal Agent Harness

This repository is the canonical source for portable personal policies and reusable skills for Codex, Claude Code, and GitHub Copilot. Installers materialize ordinary files, never symlinks, and never copy credentials, sessions, caches, trusted-project lists, Git identity, or machine-specific paths.

## Requirements

- macOS or Windows
- Python 3.9 or newer on `PATH`
- POSIX shell on macOS; PowerShell on Windows

The installer detects the operating system for reporting. Vibium and Mailinator CLI are optional and are only detected; installation never downloads or configures them.

## Profiles and agents

- `work`: Codex and Claude by default; Copilot is optional. Installs `tdd`, `vibium-browser`, and `mailinator-inbox`.
- `home`: Codex by default; Claude and Copilot are optional. Installs `tdd` and `vibium-browser`.

Enable optional agents with `--with claude`, `--with copilot`, or a comma-separated value. Disable a default with `--without claude`.

## Inspect and install

Preview all changes first:

```sh
./installer/install.sh install --profile work --dry-run
```

```powershell
.\installer\install.ps1 install --profile work --dry-run
```

After reviewing the preview, omit `--dry-run`. Existing unmanaged destination files are copied beside themselves with an `.agent-harness-backup-<timestamp>` suffix before replacement. Identical managed files are left untouched. A profile change removes only stale managed files whose hashes still match the prior manifest.

Use `--home PATH` only for testing or an intentionally redirected installation. Automated tests always use temporary fake homes.

## Verify

Report the active profile, selected agents, installed files and skills, platform, and CLI availability:

```sh
./installer/install.sh verify --profile work
./installer/install.sh verify --profile work --json
```

Verification is read-only and exits nonzero when an expected file is missing or differs from the generated source.

## Upgrade

Update this canonical repository with `git`, inspect the diff, run the tests, preview the same install command with `--dry-run`, and then run it without `--dry-run`. Managed files are updated in place; unrelated files are not touched.

## Uninstall and recovery

Preview removal:

```sh
./installer/install.sh uninstall --profile work --dry-run
```

Then omit `--dry-run` to remove files that are still managed and byte-identical to the recorded installation. Locally modified files are preserved and reported as skipped. Backups are never deleted automatically; restore one by copying it back to its original filename after uninstalling or moving the generated file aside.

## Bootstrap another repository

`AGENTS.md` is canonical project guidance. `CLAUDE.md` imports it with `@AGENTS.md`; Copilot receives a materialized compatibility copy.

```sh
./installer/install.sh bootstrap --repo /path/to/repository --dry-run
./installer/install.sh bootstrap --repo /path/to/repository
```

Unmanaged existing guidance is skipped. If replacement is intentional, use `--force`; the installer backs up each unmanaged file first. When an existing `AGENTS.md` is skipped, newly created Copilot guidance is generated from that existing canonical file.

## Add policies, profiles, or skills

- Put shared policy in `policy/common.md` and profile-only policy in `policy/work.md` or `policy/home.md`.
- Update the corresponding JSON profile's ordered `policies`, `skill_groups`, or agent defaults.
- Create skills under `skills/common/<name>` or `skills/work/<name>` with the `skill-creator` workflow. Keep `SKILL.md` frontmatter portable; optional `agents/openai.yaml` metadata is copied harmlessly for agents that ignore it.
- Run skill validation and the full tests before installing.

## Test

```sh
python3 -m unittest discover -s tests -v
```

The suite covers profile selection, path resolution, generated headers, skill frontmatter, idempotency, dry runs, backups, verification, safe bootstrap, and conservative uninstall behavior.

## Official conventions checked

The layout follows current official documentation for Codex `AGENTS.md` and `$HOME/.agents/skills`, Claude Code `CLAUDE.md` imports and personal skills, GitHub Copilot personal/repository instructions, Vibium installation and command discovery, and Mailinator CLI credentials and output modes. Recheck those sources before changing integration paths or installation guidance.
