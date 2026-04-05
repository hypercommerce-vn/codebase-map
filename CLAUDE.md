# CLAUDE.md — Codebase Map

## Project
Standalone function dependency graph generator. Works with any Python/TypeScript project via YAML config.

## Rules
- Comment `# HC-AI | ticket: FDD-TOOL-CODEMAP` on all AI-generated code blocks
- Run `black --check . && isort --check . && flake8` before commit
- All commits follow Conventional Commits format
- PR required for all changes (no direct push to main)

## Structure
```
codebase_map/
├── parsers/          # Language-specific AST parsers
├── graph/            # Graph models, builder, query engine
├── exporters/        # JSON + HTML (D3.js) exporters
└── cli.py            # CLI entry point
```

## Usage
```bash
pip install -e .
codebase-map generate -c /path/to/project/codebase-map.yaml
codebase-map query "function_name" -f graph.json
codebase-map impact "ClassName" -f graph.json
```

## Design Refs
- v2.0 mockup: `design-preview/codebase-map-v2-design.html`
- CM-S1 detail: `design-preview/codebase-map-CM-S1-design.html`
- FDD spec: `specs/spec.md`
