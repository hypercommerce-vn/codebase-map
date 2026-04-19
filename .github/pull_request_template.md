<!--
Thanks for sending a pull request! Please fill in every section that applies.
Empty or boilerplate PR descriptions slow reviews down — a few extra sentences
here save multiple review rounds later.
-->

## Summary

<!--
What does this PR do, and why?
Link the issue it resolves: "Closes #123" or "Refs #123".
-->

Closes #

## Type of change

<!-- Check all that apply. -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that changes existing behavior)
- [ ] Documentation / examples
- [ ] Refactor / internal cleanup (no user-visible change)
- [ ] Chore / CI / tooling
- [ ] Security fix (please coordinate privately first — see `SECURITY.md`)

## Changes

<!--
Bullet list of the key changes. Reviewers should be able to read this and
know what to expect before opening the diff.
-->

-
-
-

## Testing steps

<!--
How can a reviewer verify this PR locally? Include commands, fixtures,
or config snippets. If this change is covered purely by automated tests,
it is okay to say "Run `pytest tests/ -q`".
-->

1.
2.

## Screenshots / output (if UI or CLI output changed)

<!-- Attach before/after screenshots for HTML export changes, or paste CLI output diffs. -->

## Checklist

- [ ] Tests added or updated for this change
- [ ] `pytest tests/ -q` passes locally
- [ ] `black --check codebase_map/ tests/` passes
- [ ] `isort --check codebase_map/ tests/` passes
- [ ] `flake8 codebase_map/ tests/` passes
- [ ] Documentation updated (README, docstrings, `docs/`) if user-facing
- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat(parser): ...`)
- [ ] Breaking changes are called out explicitly below
- [ ] PR targets `main` and was **not** pushed directly to `main`
- [ ] AI-assisted code blocks include the `# HC-AI | ticket: FDD-TOOL-CODEMAP` marker (if applicable)

## Breaking changes

<!--
If you checked "Breaking change" above, describe:
- What breaks?
- Migration path for existing users.
- Deprecation plan (if any).
Otherwise delete this section.
-->

## Additional notes for reviewers

<!-- Anything else the reviewer should know: follow-up work, open questions, trade-offs considered. -->
