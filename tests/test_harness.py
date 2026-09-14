import contextlib
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from installer import harness


ROOT = Path(__file__).resolve().parents[1]


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()

    def options(self, profile="work", **overrides):
        values = {
            "profile": profile,
            "home": self.home,
            "with_agents": [],
            "without_agents": [],
            "dry_run": False,
            "json": False,
        }
        values.update(overrides)
        return harness.Options(**values)

    def test_profile_selection_and_path_resolution(self):
        work = harness.build_plan(ROOT, self.options("work"))
        home = harness.build_plan(ROOT, self.options("home"))

        self.assertEqual(work.agents, ("codex", "claude"))
        self.assertEqual(home.agents, ("codex",))
        self.assertIn(self.home / ".codex" / "AGENTS.md", work.files)
        self.assertIn(self.home / ".claude" / "CLAUDE.md", work.files)
        self.assertNotIn(self.home / ".copilot" / "copilot-instructions.md", work.files)

    def test_mailinator_skill_is_common_to_home_and_work_profiles(self):
        for profile in ("home", "work"):
            plan = harness.build_plan(ROOT, self.options(profile))
            skill = self.home / ".agents" / "skills" / "mailinator-inbox" / "SKILL.md"

            with self.subTest(profile=profile):
                self.assertIn(skill, plan.files)

    def test_generated_content_has_profile_source_and_valid_skill_frontmatter(self):
        plan = harness.build_plan(ROOT, self.options("work"))
        instructions = plan.files[self.home / ".codex" / "AGENTS.md"].decode()
        skill = (
            plan.files[self.home / ".agents" / "skills" / "tdd" / "SKILL.md"]
            .decode()
            .replace("\r\n", "\n")
        )

        self.assertIn("Profile: work", instructions)
        self.assertIn("Source: agent-harness/policy/common.md", instructions)
        self.assertTrue(skill.startswith("---\nname: tdd\n"))
        self.assertIn("Managed: agent-harness/v1", skill)

    def test_skill_frontmatter_supports_crlf_line_endings(self):
        skill = harness._decorate_skill(
            b"---\r\nname: example\r\n---\r\n\r\n# Example\r\n",
            "skills/common/example/SKILL.md",
            "home",
            "SKILL.md",
        ).decode()

        self.assertTrue(skill.startswith("---\r\nname: example\r\n---\r\n"))
        self.assertIn("\r\n<!-- Generated file.", skill)
        self.assertIn("Managed: agent-harness/v1. -->\r\n\r\n# Example\r\n", skill)

    def test_common_policy_requires_safe_local_env_files(self):
        plan = harness.build_plan(ROOT, self.options("home"))
        instructions = plan.files[self.home / ".codex" / "AGENTS.md"].decode()

        self.assertIn("credential store supported by the tool or platform", instructions)
        self.assertIn("ensure it is excluded from Git", instructions)
        self.assertIn("Treat existing `.env` files as sensitive", instructions)
        self.assertIn("Keep `.env.example` files secret-free", instructions)

    def test_common_policy_defaults_to_concise_responses(self):
        plan = harness.build_plan(ROOT, self.options("home"))
        instructions = plan.files[self.home / ".codex" / "AGENTS.md"].decode()

        self.assertIn("Default to concise responses", instructions)
        self.assertIn("Expand only when the user asks", instructions)

    def test_common_policy_requires_explicit_authorization_for_remote_git_actions(self):
        plan = harness.build_plan(ROOT, self.options("home"))
        instructions = plan.files[self.home / ".codex" / "AGENTS.md"].decode()

        self.assertIn("must not push commits", instructions)
        self.assertIn("explicitly requests that specific remote action", instructions)
        self.assertIn("A request to \u201cfinish,\u201d \u201cimplement,\u201d \u201ccommit,\u201d or \u201cprepare a PR\u201d does not authorize pushing", instructions)

    def test_common_policy_prefers_discovered_domain_native_external_service_tools(self):
        plan = harness.build_plan(ROOT, self.options("home"))
        instructions = plan.files[self.home / ".codex" / "AGENTS.md"].decode()

        expected_distinctions = (
            "Skills determine how work should be performed",
            "Plugins, connectors, and tools determine what actions are available",
            "Choose the domain-native execution tool before selecting a generic mechanism",
        )
        expected_in_order = (
            "Identify the target service and desired operation",
            "Load any mandatory skills",
            "Search both explicitly listed and deferred or lazy-loaded tools",
            "Connected service plugin, app, or MCP tool",
            "Repository-supported CLI",
            "Authenticated UI automation",
            "Raw API using an existing credential store",
            "Manual instructions",
            "Absence from the initial tool list does not prove",
        )
        positions = [instructions.index(text) for text in expected_in_order]

        for distinction in expected_distinctions:
            self.assertIn(distinction, instructions)
        self.assertEqual(positions, sorted(positions))
        self.assertLess(
            instructions.index("domain-native execution tool"),
            instructions.index("Authenticated UI automation"),
        )
        self.assertIn("tool_search", instructions)
        self.assertIn("ALL_TOOLS", instructions)

    def test_skill_metadata_prompts_invoke_the_named_skill(self):
        for metadata_path in ROOT.glob("skills/*/*/agents/openai.yaml"):
            skill_name = metadata_path.parents[1].name
            metadata = metadata_path.read_text(encoding="utf-8")
            with self.subTest(skill=skill_name):
                self.assertIn(f'default_prompt: "Use ${skill_name} ', metadata)

    def test_home_can_enable_optional_agents(self):
        plan = harness.build_plan(
            ROOT, self.options("home", with_agents=["claude,copilot"])
        )
        self.assertEqual(plan.agents, ("codex", "claude", "copilot"))
        self.assertIn(self.home / ".copilot" / "copilot-instructions.md", plan.files)

    def test_install_is_idempotent(self):
        options = self.options("work")
        first = harness.install(ROOT, options)
        backups_after_first = list(self.home.rglob("*.agent-harness-backup-*"))
        second = harness.install(ROOT, options)

        self.assertGreater(first.changed, 0)
        self.assertEqual(second.changed, 0)
        self.assertEqual(second.backed_up, 0)
        self.assertEqual(backups_after_first, list(self.home.rglob("*.agent-harness-backup-*")))

    def test_dry_run_does_not_write(self):
        result = harness.install(ROOT, self.options("work", dry_run=True))
        self.assertGreater(result.changed, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_release_receipt_and_independent_drift_detection(self):
        source = Path(self.temp.name) / "source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        (source / "VERSION").write_text("0.2.0\n")
        options = self.options()
        harness.install(source, options)
        receipt_path = self.home / ".agent-harness/manifest.json"
        receipt = receipt_path.read_bytes()
        report = harness.verify(source, options)
        self.assertEqual(report["deployment"]["status"], "current")
        self.assertEqual(report["deployment"]["installed"]["release"], "0.2.0")
        self.assertIsNotNone(report["deployment"]["installed"]["installed_at"])
        harness.install(source, options)
        self.assertEqual(receipt_path.read_bytes(), receipt)
        policy = source / "policy/common.md"
        policy.write_text(policy.read_text(encoding="utf-8") + "\nNew policy\n", encoding="utf-8")
        report = harness.verify(source, options)
        self.assertEqual(report["deployment"]["status"], "update-available")
        self.assertEqual(report["deployment"]["local_changes"], [])
        target = self.home / ".codex/AGENTS.md"
        target.write_text(target.read_text(encoding="utf-8") + "\nLocal edit\n", encoding="utf-8")
        report = harness.verify(source, options)
        self.assertEqual(report["deployment"]["local_changes"], ["~/.codex/AGENTS.md"])
        harness.install(source, options)
        self.assertTrue(harness.verify(source, options)["ok"])
        (source / "VERSION").write_text("0.3.0\n")
        self.assertEqual(harness.verify(source, options)["deployment"]["status"], "update-available")

    def test_git_identity_and_missing_git(self):
        plan = harness.build_plan(ROOT, self.options())
        responses = [mock.Mock(stdout=str(ROOT)), mock.Mock(stdout="a" * 40), mock.Mock(stdout=" M policy/common.md")]
        with mock.patch.object(harness.subprocess, "run", side_effect=responses):
            identity = harness._release_identity(ROOT, plan, self.home)
        self.assertEqual(identity["commit"], "a" * 40)
        self.assertTrue(identity["dirty"])
        with mock.patch.object(harness.subprocess, "run", side_effect=FileNotFoundError):
            exported = harness._release_identity(ROOT, plan, self.home)
        self.assertIsNone(exported["commit"])
        self.assertIsNone(exported["dirty"])
        self.assertEqual(identity["fingerprint"], exported["fingerprint"])

    def test_legacy_receipt_has_unknown_release(self):
        options = self.options()
        harness.install(ROOT, options)
        path = self.home / ".agent-harness/manifest.json"
        state = json.loads(path.read_text())
        state.pop("release", None)
        path.write_text(json.dumps(state))
        report = harness.verify(ROOT, options)
        self.assertIsNone(report["deployment"]["installed"])
        self.assertEqual(report["deployment"]["status"], "unknown")
        self.assertEqual(report["deployment"]["local_changes"], [])

    def test_unmanaged_file_is_backed_up_before_replacement(self):
        destination = self.home / ".codex" / "AGENTS.md"
        destination.parent.mkdir()
        destination.write_text("my existing instructions\n", encoding="utf-8")

        result = harness.install(ROOT, self.options("home"))
        backups = list(destination.parent.glob("AGENTS.md.agent-harness-backup-*"))

        self.assertEqual(result.backed_up, 1)
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "my existing instructions\n")
        self.assertIn("Managed: agent-harness/v1", destination.read_text(encoding="utf-8"))

    def test_verify_reports_files_skills_and_tools(self):
        harness.install(ROOT, self.options("work"))
        report = harness.verify(ROOT, self.options("work"), which=lambda name: f"/bin/{name}" if name == "mailinator-cli" else None)

        self.assertTrue(report["ok"])
        self.assertIn("tdd", report["skills"])
        self.assertEqual(report["tools"]["mailinator-cli"], "available")
        self.assertEqual(report["tools"]["vibium"], "missing")

    def test_bootstrap_skips_unmanaged_files_without_force(self):
        repository = Path(self.temp.name) / "project"
        repository.mkdir()
        existing = repository / "AGENTS.md"
        existing.write_text("team guidance\n", encoding="utf-8")

        result = harness.bootstrap(ROOT, repository, dry_run=False, force=False)

        self.assertEqual(existing.read_text(encoding="utf-8"), "team guidance\n")
        self.assertIn(existing, result.skipped)
        self.assertTrue((repository / "CLAUDE.md").exists())
        self.assertTrue((repository / ".github" / "copilot-instructions.md").exists())

    def test_bootstrap_force_backs_up_and_copilot_contains_canonical_guidance(self):
        repository = Path(self.temp.name) / "project"
        repository.mkdir()
        (repository / "AGENTS.md").write_text("old\n", encoding="utf-8")

        result = harness.bootstrap(ROOT, repository, dry_run=False, force=True)
        agents = (repository / "AGENTS.md").read_text(encoding="utf-8")
        copilot = (repository / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")

        self.assertEqual(result.backed_up, 1)
        self.assertIn("Project-specific guidance", agents)
        self.assertIn("Project-specific guidance", copilot)
        self.assertIn("@AGENTS.md", (repository / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_uninstall_preserves_modified_managed_file(self):
        options = self.options("home")
        harness.install(ROOT, options)
        destination = self.home / ".codex" / "AGENTS.md"
        destination.write_text(destination.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")

        result = harness.uninstall(ROOT, options)

        self.assertTrue(destination.exists())
        self.assertIn(destination, result.skipped)


if __name__ == "__main__":
    unittest.main()
