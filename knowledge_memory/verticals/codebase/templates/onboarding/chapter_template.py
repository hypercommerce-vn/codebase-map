# HC-AI | ticket: MEM-M3-02
"""Chapter template engine for onboarding report.

Uses Python string.Template for lightweight templating.
Jinja2 can be swapped in later without changing the interface.

Design ref: kmp-M3-design.html Screen B (8-chapter report).
"""

from __future__ import annotations

from string import Template
from typing import Any

# HC-AI | ticket: MEM-M3-02
# 8 chapter templates — each uses ${variable} substitution

_CHAPTER_TEMPLATES: dict[int, str] = {
    1: """## 1. Project Overview

This project has **${total_nodes} functions** across **${domains} domains**.

**Architecture:** ${architecture_summary}
**Primary patterns:** ${top_patterns}

${mermaid_placeholder}
""",
    2: """## 2. Naming Conventions

${naming_patterns}

**Key rules for new code:**
- Follow snake_case for all functions and variables
- Use PascalCase for class names only
- CRUD methods: use get_/create_/update_/delete_ prefixes
""",
    3: """## 3. Architecture Layers

${layer_patterns}

**Layer hierarchy (top to bottom):**
1. **Route** — HTTP endpoints, request/response
2. **Service** — Business logic, orchestration
3. **Model** — Data structures, ORM
4. **Util** — Shared helpers, no business logic
""",
    4: """## 4. Error Handling Patterns

${error_patterns}

**Guidelines:**
- Always use specific exception types (never bare `except:`)
- Log errors with context: `logger.error("msg", extra={...})`
- Retry transient failures with exponential backoff
""",
    5: """## 5. Testing Patterns

${test_patterns}

**Testing conventions:**
- Test files: `test_<module>.py` in `tests/` directory
- Use pytest fixtures for shared setup
- Aim for ${coverage_target}% coverage minimum
""",
    6: """## 6. Dependency Injection

${di_patterns}

**Preferred approach:**
- Constructor injection for service dependencies
- Factory functions for complex object creation
- Avoid service locator pattern (use explicit injection)
""",
    7: """## 7. Code Ownership

${ownership_patterns}

**Onboarding focus:**
- Review high-risk single-owner domains first
- Pair with domain experts for first contributions
- Check git blame before modifying unfamiliar code
""",
    8: """## 8. Domain Glossary

${glossary_table}

> These terms are extracted from function names, module paths,
> and code comments. Learn them to navigate the codebase faster.
""",
}


def render_chapter(
    chapter_num: int,
    context: dict[str, Any],
) -> str:
    """Render a chapter template with given context.

    Args:
        chapter_num: Chapter number (1-8).
        context: Template variables (keys match ${var} in template).

    Returns:
        Rendered Markdown string.
    """
    template_str = _CHAPTER_TEMPLATES.get(chapter_num, "")
    if not template_str:
        return f"## {chapter_num}. (No template available)\n"

    # Safe substitute — missing keys become empty string
    tmpl = Template(template_str)
    # Build safe defaults
    safe_context = {k: str(v) for k, v in context.items()}
    return tmpl.safe_substitute(safe_context)


def get_chapter_titles() -> dict[int, str]:
    """Return chapter number → title mapping."""
    return {
        1: "Project Overview",
        2: "Naming Conventions",
        3: "Architecture Layers",
        4: "Error Handling Patterns",
        5: "Testing Patterns",
        6: "Dependency Injection",
        7: "Code Ownership",
        8: "Domain Glossary",
    }
