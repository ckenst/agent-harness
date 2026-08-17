## Repository operations

- Prefer `git` for every repository operation Git supports.
- Do not substitute `gh` for status, diff, branch, commit, fetch, pull, push, tag, or remote operations.
- Use `gh` only for GitHub-platform operations Git cannot perform, such as pull requests, issues, review threads, or Actions.
- Respect the repository's existing remotes, credential helper, and local identity. Never change authentication or identity unless asked.
- Agents may create local branches and commits when the task calls for them, but must not push commits, force-push, create or merge pull requests, modify remote branches or tags, or change repository remotes unless the user explicitly requests that specific remote action in the current conversation.
- A request to “finish,” “implement,” “commit,” or “prepare a PR” does not authorize pushing. Before a remote Git action, state the target remote and branch and obtain explicit approval unless the user has already named both.

## Behavioral changes and bug fixes

- Default to test-driven development: identify or write a focused failing test, confirm the expected failure, make the smallest implementation change, confirm the focused test passes, refactor, and run the broader relevant suite.
- Preserve the repository's existing test framework, commands, naming, and conventions.
- When TDD is unsuitable, explain why before changing the implementation.
- Report practical evidence for the failing test, passing focused test, and broader suite.

## Safety

- Preserve user changes and avoid destructive operations.
- Never expose credentials, tokens, sessions, caches, trusted-project lists, Git identities, or machine-specific configuration.

## Credentials and local configuration

- Never hard-code or commit credentials, API keys, tokens, or other secrets.
- Prefer the credential store supported by the tool or platform. Otherwise, inject secrets through environment variables.
- For local development, follow the repository's existing `.env` convention. Before creating or modifying a secret-bearing `.env` file, ensure it is excluded from Git.
- Keep `.env.example` files secret-free; include only variable names and safe placeholder values.
- Treat existing `.env` files as sensitive. Read only values needed for the task and never print, log, or reproduce their contents.
- Avoid passing secrets directly in command arguments when a safer environment-variable or credential-store mechanism exists.
