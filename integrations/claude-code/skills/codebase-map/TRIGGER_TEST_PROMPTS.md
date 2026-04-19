# Trigger Test Prompts

Ten sample user prompts that should trigger this skill. PM/CTO will dry-run
these in Claude Code during review gate. Target: 8/10 trigger rate.

## Prompts

1. "What breaks if I change the `CustomerService.create` method?"
2. "Show me all callers of `process_payment`."
3. "Generate a dependency graph for this project."
4. "Onboard me to this repo — what are the main components?"
5. "What's the blast radius if I delete this function?"
6. "List all API endpoints in this project."
7. "Compare this branch to main — what functions changed?"
8. "Is it safe to rename `User.email` to `User.email_address`?"
9. "Run before/after diff for my refactor PR."
10. "Which tests should I add for this change?"

## Non-trigger prompts (should NOT invoke skill)

1. "Read the README file."
2. "What does this one function do?" (without asking about callers/impact)
3. "Run the tests."
4. "Fix this lint error."
5. "Deploy to production."
