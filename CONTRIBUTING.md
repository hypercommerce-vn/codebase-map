# Contributing to codebase-map

Thanks for your interest in contributing! `codebase-map` is an open-source dependency-graph tool maintained by [Hyper Commerce Vietnam](https://github.com/hypercommerce-vn). This guide covers everything you need to ship your first change.

## Ways to Contribute

- **Report bugs** or regressions (use the bug template).
- **Propose features** or improvements (use the feature template).
- **Send pull requests** — fixes, parser improvements, new exporters, docs, tests, CI, examples.
- **Triage issues** — reproduce bug reports, add missing info, confirm duplicates.
- **Improve documentation** — README, CLAUDE.md links, inline docstrings, translations.
- **Share usage patterns** — real-world config examples or integration recipes in `docs/`.

No contribution is too small. Fixing a typo in a docstring is very welcome.

## Code of Conduct

A dedicated `CODE_OF_CONDUCT.md` is *forthcoming*. Until it lands, we follow the spirit of the [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/): be respectful, assume good intent, and keep discussions focused on the work. Harassment of any kind is not tolerated.

For private concerns, email the maintainers at **hypercdp@gmail.com**.

## Development Setup

### 1. Fork and clone

```bash
git clone git@github.com:<your-username>/codebase-map.git
cd codebase-map
git remote add upstream git@github.com:hypercommerce-vn/codebase-map.git
```

### 2. Create a virtualenv and install with dev extras

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Python **3.10+** is required (see `pyproject.toml`). Runtime dependencies are minimal (`pyyaml`); dev extras add `pytest`, `pytest-cov`, `black`, `isort`, and `flake8`.

### 3. Verify the toolchain

```bash
codebase-map --version          # should print 2.2.0 (or current)
pytest tests/ -q                 # 158 tests, all green
```

### 4. Run lint locally

```bash
black --check codebase_map/ tests/
isort --check codebase_map/ tests/
flake8 codebase_map/ tests/      # uses setup.cfg
```

If any of these fail, the CI will fail too. Run without `--check` to auto-fix formatting.

## Branches and Commits

### Branch naming

Use a prefix that matches the nature of the change:

| Prefix      | Use for                                           |
|-------------|---------------------------------------------------|
| `feat/`     | New functionality                                 |
| `fix/`      | Bug fixes                                         |
| `docs/`     | Documentation only                                |
| `chore/`    | Tooling, CI, dependency bumps                     |
| `refactor/` | Internal restructuring, no behavior change        |
| `security/` | Security-related fixes (coordinate privately first — see `SECURITY.md`) |

Example: `feat/parser-golang-support`, `fix/html-exporter-xss-escape`.

### Conventional Commits (required)

Every commit message must follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(parser): add Go language support
fix(exporter): escape special chars in node labels
chore(ci): bump actions/checkout to v4
docs(readme): document snapshot-diff output formats
```

Common scopes in this repo: `parser`, `graph`, `cli`, `exporter`, `config`, `ci`, `docs`, `tests`.

Keep each PR focused on **one logical change**. Smaller PRs review faster and land faster.

## Pull Request Workflow

1. Sync your fork with upstream `main`:
   ```bash
   git fetch upstream
   git checkout main && git merge upstream/main
   git checkout -b feat/my-change
   ```
2. Make your changes, add tests, update docs.
3. Ensure lint and tests pass locally (see above).
4. Push your branch and open a PR against `hypercommerce-vn/codebase-map:main`.
5. Fill out the PR template completely — it saves reviewer time.
6. CI runs automatically (`.github/workflows/ci.yml`). Both **lint** and **pytest** must be green.
7. At least **one maintainer approval** is required before merge.
8. For feature-sized changes we run a 3-tier `/review-gate` (Tester → CTO → Designer) internally; external contributors do not need to drive this, but expect review feedback from multiple angles.
9. **No direct pushes to `main`.** All changes land via PR.

Maintainers will squash-merge most PRs using the Conventional Commit message from the PR title.

## Testing Guidelines

- Unit tests live under `tests/codebase_map/` mirroring the package layout.
- **Every bug fix must come with a regression test** that fails before the fix and passes after.
- New parsers must meet the **99% accuracy** bar on representative fixtures (a CTO-level KPI — see `agents/cto/SKILL.md`).
- Use fixtures in `tests/` rather than relying on the live HC codebase.
- Prefer small, deterministic assertions over golden-file dumps where possible.

Run the full suite:
```bash
pytest tests/ -q
```

Run a subset while iterating:
```bash
pytest tests/codebase_map/parsers -q -k python
```

### Marking AI-assisted changes

If a block of code was drafted with AI assistance (Claude, Copilot, etc.), leave a short marker comment at the top of the block:

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP
```

This is a maintenance hint, not a quality signal — human review still applies.

## Architecture Principles (Short Form)

CBM is intentionally small and stateless. Keep contributions aligned with these axes:

- **Parser → Graph → Exporter separation.** No cross-layer imports. A parser produces nodes/edges; the graph builder assembles them; exporters only read the finished graph.
- **`BaseParser` is the contract.** New languages implement the interface in `codebase_map/parsers/base.py` — they never touch graph internals directly.
- **Config-driven.** Users describe their project through a YAML file; the tool itself stays project-agnostic.
- **Stateless commands.** Every CLI command takes a `graph.json` as input. No hidden database, no mutable global state.

Deeper context lives in `CLAUDE.md` (§4 "Architecture Principles") and the spec at `specs/spec.md`.

## Reporting Bugs and Requesting Features

- **Bugs:** open an issue using the **Bug report** template. Include CBM version, OS, Python version, minimal config, and reproduction steps.
- **Features:** open an issue using the **Feature request** template. Describe the problem first, proposed solution second.
- **Security:** do **not** file a public issue. See [`SECURITY.md`](SECURITY.md) for the private disclosure channel.

## Getting Help

- **General questions / ideas:** [GitHub Discussions](https://github.com/hypercommerce-vn/codebase-map/discussions) (if enabled) or an issue with the `question` label.
- **Private matters:** email **hypercdp@gmail.com**.
- **Real-time Vietnamese-language support:** the maintainer team is based in Vietnam; English and Vietnamese are both welcome in issues and PRs.

---

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE) that covers the project.

Happy mapping!
