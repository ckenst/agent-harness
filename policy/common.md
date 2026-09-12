## Repository operations

- Prefer `git` for every repository operation Git supports.
- Do not substitute `gh` for status, diff, branch, commit, fetch, pull, push, tag, or remote operations.
- Use `gh` only for GitHub-platform operations Git cannot perform, such as pull requests, issues, review threads, or Actions.
- Respect the repository's existing remotes, credential helper, and local identity. Never change authentication or identity unless asked.
- Agents may create local branches and commits when the task calls for them, but must not push commits, force-push, create or merge pull requests, modify remote branches or tags, or change repository remotes unless the user explicitly requests that specific remote action in the current conversation.
- A request to “finish,” “implement,” “commit,” or “prepare a PR” does not authorize pushing. Pushing to a remote branch requires approval unless the current user explicitly asked for that push. When a push is authorized, state the target remote and branch before proceeding.

## Behavioral changes and bug fixes

- Default to test-driven development: identify or write a focused failing test, confirm the expected failure, make the smallest implementation change, confirm the focused test passes, refactor, and run the broader relevant suite.
- Preserve the repository's existing test framework, commands, naming, and conventions.
- When TDD is unsuitable, explain why before changing the implementation.
- Report practical evidence for the failing test, passing focused test, and broader suite.

## Subagents and delegation

- Use subagents when available for independent, bounded work that can make useful progress in parallel and whose expected benefit outweighs coordination overhead. This is standing authorization to delegate within the user's task scope, subject to the runtime's instructions and limits.
- Work directly for simple edits, quick lookups, tightly sequential steps, or tasks that require continuous shared context. Multiple requested items alone do not justify delegation.
- Use at most two concurrent subagents unless the user explicitly requests a larger team and the runtime supports it. Subagents must not delegate further.
- Give each subagent a clear objective, relevant context, permitted files and actions, completion criteria, and expected output. Require evidence for findings and explicit reporting of unresolved questions or incomplete work.
- Default delegated investigations and reviews to read-only work. For implementation, assign distinct file ownership or isolated worktrees and coordinate shared dependencies before editing.
- Briefly explain the assignments when delegating. The primary agent should continue useful independent work, avoid duplicating delegated work, and remain responsible for reconciling findings, inspecting changes, running relevant verification, and delivering one coherent result.
- Delegation does not expand authorization. All agents must preserve user changes and follow the same repository, credential, and external-action restrictions. Use supported subagent tools; do not create separate user-facing tasks unless the user requests them. If delegation is unavailable, continue directly and report any material limitation.

## Response style

- Default to concise responses: lead with the outcome and include only the details needed to act or decide.
- Expand only when the user asks, when a decision requires context, or when safety, uncertainty, or a blocker makes more explanation necessary.

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
