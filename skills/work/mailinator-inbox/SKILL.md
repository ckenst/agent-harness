---
name: mailinator-inbox
description: Use Mailinator CLI for inbox inspection, message retrieval, verification links, OTPs, magic links, and email-based automated test flows. Use when a task mentions Mailinator, test inboxes, waiting for email, extracting a code or link, or validating delivered email.
---

# Mailinator Inbox

## Prepare safely

1. Read repository guidance and locate existing Mailinator scripts or configuration.
2. Resolve the repository's documented command first, then `mailinator-cli` on `PATH`.
3. Run the resolved command's `--help` before assuming options. If unavailable, report that state; do not substitute another email service or invent an installation command.
4. Use `MAILINATOR_API_KEY` or the CLI's supported credential store for private access. Never place a token in a command argument, source file, transcript, generated file, or test fixture.
5. Never print environment contents or credential-store contents. Redact tokens from error output.

## Work with messages

- Use public inboxes only for non-sensitive experiments. Use a private domain for OTPs, password resets, magic links, private test users, or other sensitive flows.
- Generate a unique inbox name for parallel or repeated automated runs when the project does not provide one.
- Prefer structured JSON or full-message output when the installed CLI supports it; inspect help output to confirm the exact syntax.
- Select messages using sender, recipient, subject, timestamp, or a run-specific correlation value rather than assuming the first list entry is correct.
- Extract only the code, link, or assertion data the workflow needs. Avoid echoing entire sensitive messages.

## Poll with limits

Poll using the repository's existing helper when available. Otherwise use a loop with an explicit maximum attempt count, delay, and overall deadline. Re-query the inbox each attempt, reject messages older than the test start time, and finish immediately on a match. On timeout, report bounded diagnostic metadata without tokens or sensitive bodies.

## Installation guidance

When installation is requested, inspect current local or official Mailinator CLI documentation first. Present the documented platform-appropriate option and request approval before changing the machine. Never install automatically while performing an inbox task.
