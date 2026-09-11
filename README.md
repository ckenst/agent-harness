# Personal Agent Harness

This repository is the canonical source for portable personal policies and reusable skills for Codex, Claude Code, and GitHub Copilot. Installers materialize ordinary files, never symlinks, and never copy credentials, sessions, caches, trusted-project lists, Git identity, or machine-specific paths.

## Requirements

- macOS or Windows
- Python 3.9 or newer on `PATH`
- POSIX shell on macOS; PowerShell on Windows

The installer detects the operating system for reporting. Vibium and Mailinator CLI are optional and are only detected; installation never downloads or configures them.

## Privacy and security

This repository contains reusable policy and skill definitions, not runtime data. Do not commit API keys, credentials, session data, private inbox contents, generated installation state, backups, or machine-specific configuration. Keep secrets in environment variables or the credential store supported by the relevant tool.

The installer writes generated files and a manifest only beneath the selected home directory. Review every install, upgrade, bootstrap, or uninstall with `--dry-run` before allowing it to change files. Treat additions to `policy/work.md` and `skills/work/` as public information and review them for employer-confidential details before committing.

## Profiles and agents

- `work`: Codex and Claude by default; Copilot is optional. Installs `tdd`, `vibium-browser`, and `mailinator-inbox`.
- `home`: Codex by default; Claude and Copilot are optional. Installs `tdd`, `vibium-browser`, and `mailinator-inbox`.

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

## Release and installation tracking

`VERSION` identifies the harness release (starting with `0.1.0`). Bump the minor version for new capabilities, the patch version for fixes or policy refinements, and the major version for incompatible changes.

Run `.\installer\install.ps1 verify --profile work` on Windows or `./installer/install.sh verify --profile work` on macOS to compare the installed release with this checkout. Pass the same profile and optional agent selections used during installation. Add `--json` for structured output, including the full content fingerprint.

The local installation manifest records the release, source Git commit, whether relevant source files had uncommitted changes, a deployment content fingerprint, and the UTC installation time. An unchanged reinstall preserves that timestamp. Git metadata is reported as unknown when Git is unavailable or the source is an exported directory.

Verification reports `current`, `update-available`, or `unknown`, and separately lists installed files changed or missing since installation. `update-available` means the selected deployment differs, not necessarily that its version number is higher. The fingerprint covers generated files and installer code, so changes are detected even without a version bump. A different Git commit alone does not require reinstalling identical content. Old manifests retain their file verification behavior but report an unknown release until the next successful install.

After changing the harness: update `VERSION` as appropriate, run tests, review the install dry run, then install. Committing a change does not install it. The manifest's existing `version` field remains its schema version, separate from the harness release. Deployment receipts stay local and must not be committed.

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

## License

Licensed under the [MIT License](LICENSE).

## Official conventions checked

The layout follows current official documentation for Codex `AGENTS.md` and `$HOME/.agents/skills`, Claude Code `CLAUDE.md` imports and personal skills, GitHub Copilot personal/repository instructions, Vibium installation and command discovery, and Mailinator CLI credentials and output modes. Recheck those sources before changing integration paths or installation guidance.
