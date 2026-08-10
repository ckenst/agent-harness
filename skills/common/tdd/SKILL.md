---
name: tdd
description: Apply test-driven development to behavioral changes and bug fixes. Use when implementing or repairing observable behavior, adding regression coverage, or when a request mentions tests, TDD, red-green-refactor, or test-first development.
---

# Test-Driven Development

## Workflow

1. Inspect repository guidance and existing tests before choosing commands or locations.
2. Discover the narrowest repository-native test command from documentation, package scripts, build files, CI configuration, and nearby tests. Do not introduce a new framework when the repository already has one.
3. Write or identify one focused test that expresses the requested behavior.
4. Run it and confirm it fails for the expected behavioral reason. A syntax, dependency, collection, or environment failure is not a valid red test.
5. Make the smallest implementation change that can satisfy the test.
6. Run the focused test and confirm it passes.
7. Refactor only while the test remains green.
8. Run the broader relevant suite using the repository's established command.

## Evidence

- Report the exact commands and concise outcomes for the red test, green test, and broader suite when practical.
- Preserve useful failure output without dumping unrelated logs.
- If an existing test already demonstrates the defect, use it rather than duplicating coverage.
- If the red phase cannot be run safely or reliably, explain the constraint before implementing and use the closest verifiable alternative.

## Guardrails

- Test public behavior rather than incidental implementation details.
- Keep fixtures and test style consistent with neighboring tests.
- Do not weaken, delete, skip, or broadly rewrite tests merely to obtain green output.
- Do not treat an unrelated pre-existing failure as evidence for the requested behavior.
