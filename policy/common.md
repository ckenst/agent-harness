## Repository operations

- Prefer `git` for every repository operation Git supports.
- Do not substitute `gh` for status, diff, branch, commit, fetch, pull, push, tag, or remote operations.
- Use `gh` only for GitHub-platform operations Git cannot perform, such as pull requests, issues, review threads, or Actions.
- Respect the repository's existing remotes, credential helper, and local identity. Never change authentication or identity unless asked.

## Behavioral changes and bug fixes

- Default to test-driven development: identify or write a focused failing test, confirm the expected failure, make the smallest implementation change, confirm the focused test passes, refactor, and run the broader relevant suite.
- Preserve the repository's existing test framework, commands, naming, and conventions.
- When TDD is unsuitable, explain why before changing the implementation.
- Report practical evidence for the failing test, passing focused test, and broader suite.

## Safety

- Preserve user changes and avoid destructive operations.
- Never expose credentials, tokens, sessions, caches, trusted-project lists, Git identities, or machine-specific configuration.
