---
name: vibium-browser
description: Use Vibium for browser automation, UI verification, and browser-based testing. Use when a task needs navigating pages, interacting with elements, capturing screenshots or text, or testing a web flow with Vibium, especially when the repository already contains Vibium configuration.
---

# Vibium Browser

## Resolve the project setup

1. Read repository guidance and search for existing Vibium dependencies, scripts, configuration, and tests.
2. Prefer the repository's documented command or package script.
3. Otherwise check for a project-local Vibium executable, then `vibium` on `PATH`, and then a configured `VIBIUM_BIN_PATH` where supported.
4. Run `vibium --help` or the resolved project's help command before assuming flags or subcommands.
5. If Vibium is unavailable, stop and report it. Do not silently install or substitute Playwright, Selenium, Puppeteer, or another framework.

## Automate

- Reuse existing browser, session, headless, output, and test configuration.
- Follow Vibium's inspect-act-observe loop: navigate, map or find interactive elements, act on stable references, and read back visible state.
- Prefer semantic element discovery and fresh maps over brittle selectors.
- Bound waits and capture enough output to diagnose failures.
- Avoid exposing cookies, session data, credentials, or sensitive page content in logs.

## Installation guidance

When installation is requested, inspect current project documentation and the official Vibium installation page first. Present the documented option appropriate to the environment and ask before changing dependencies or downloading a managed browser. Never invent an installation command.
