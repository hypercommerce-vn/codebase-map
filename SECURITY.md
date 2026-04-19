# Security Policy

Thank you for helping keep **codebase-map** and its users safe. This document describes how to report vulnerabilities and what you can expect from us in return.

## Supported Versions

Security patches are backported to the **latest minor release line** only. Earlier minor lines become end-of-life once the next minor ships.

| Version  | Released   | Status         | Security updates |
|----------|------------|----------------|------------------|
| v2.2.x   | 2026-04-12 | Current        | Yes              |
| v2.1.x   | 2026-04-12 | End of life    | No               |
| v2.0.x   | 2026-04-07 | End of life    | No               |
| < v2.0   | —          | End of life    | No               |

If you are on an older version, please upgrade to the latest v2.2.x before filing a report — the issue may already be fixed.

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for a suspected vulnerability.**

Preferred channel — **GitHub Security Advisories** (private):

> https://github.com/hypercommerce-vn/codebase-map/security/advisories/new

Alternate channel — **email**:

> hypercdp@gmail.com with subject prefix `[SECURITY] codebase-map`

Please include as much of the following as you can:

- Affected version(s) (`codebase-map --version`)
- A clear description of the issue and its impact
- Step-by-step reproduction (minimal repo, config excerpt, command invocation)
- Any logs, stack traces, or proof-of-concept output
- A suggested fix or mitigation, if you have one
- Whether you would like credit in the advisory

If you need to send sensitive attachments, encrypted email is fine — request our PGP key via the same address.

## Our Response Commitment

| Stage                         | Target                                      |
|-------------------------------|---------------------------------------------|
| Acknowledge receipt           | Within **48 hours**                         |
| Initial assessment & triage   | Within **7 days**                           |
| Fix for **critical** severity | Target **< 14 days** from confirmation      |
| Fix for **high** severity     | Target **< 30 days** from confirmation      |
| Fix for **medium** severity   | Target **< 90 days** from confirmation      |
| Fix for **low** severity      | Rolled into the next regular release        |

We will keep you updated on progress and coordinate disclosure timing with you.

## Disclosure Policy

We practice **coordinated disclosure**:

1. We work with you privately to confirm, reproduce, and fix the issue.
2. A patched release is published.
3. A GitHub Security Advisory is published alongside release notes.
4. For high / critical issues we request a CVE via GitHub.
5. We credit the reporter by name or handle unless you prefer to remain anonymous.

We ask that you give us a reasonable window to ship a fix before any public writeup.

## Scope

### In scope
- `codebase_map` Python package — parsers, graph builder, query engine, CLI, exporters
- HTML / JSON exporters (including the bundled `d3.v7.min.js`)
- GitHub Actions workflows shipped in this repository (`.github/workflows/`)
- Example config (`codebase-map.example.yaml`) and documentation in `docs/`
- From v2.3 onwards: the MCP server and any first-party adapters we ship

### Out of scope
- Vulnerabilities in **upstream dependencies** (PyYAML, click, etc.) — please report those to the upstream project. We will update our pin once a fixed release is available.
- Issues that require an attacker who already has write access to a target project's source tree or configuration (CBM reads source as trusted input).
- Private Hyper Commerce infrastructure, non-public forks, or third-party integrations we do not maintain.
- Reports based solely on version numbers without a demonstrated vulnerability.
- Rate limiting, CSRF, or session handling on properties we do not operate.

## Known Design Decisions (Hardening Notes)

We want to be transparent about how CBM handles untrusted input so that you can focus your research:

- **Source code is read, not executed.** The Python parser uses the standard library `ast` module. CBM never `exec()`s, `eval()`s, or `import`s user code.
- **YAML config is loaded via `yaml.safe_load()`** — no `yaml.load()`, no custom constructors, no arbitrary object instantiation.
- **HTML export escapes user-supplied strings** (function names, docstrings, file paths) before interpolation. The bundled `d3.v7.min.js` is served from the same origin as the report — no third-party CDN fetches at runtime.
- **Snapshot files** under `.codebase-map-cache/` are treated as trusted local artifacts produced by CBM itself; a threat model assuming an attacker who can write to that directory is out of scope.
- **Subprocess usage** is limited to `git` invocations when computing PR diffs, always with explicit arguments (no shell string interpolation).

If you find a case where one of these assumptions breaks, that is exactly the kind of report we want to see.

## Hall of Fame

We gratefully acknowledge researchers who have helped improve the security of codebase-map. Contributions will be listed here once we have advisories to publish.

*(Your name could be here — see [Reporting a Vulnerability](#reporting-a-vulnerability).)*

---

*Last updated: 2026-04-18 · Maintained by Hyper Commerce Vietnam ([hypercommerce-vn](https://github.com/hypercommerce-vn))*
