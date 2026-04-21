# Contributing to `hypercommerce-vn/claude-plugins`

Thanks for your interest in submitting a plugin. This marketplace curates
plugins for Claude Code and Cowork. Submissions go through a lightweight
review focused on quality, security, and clarity.

## Submission flow

1. **Fork** this repository.
2. **Add your plugin** under `plugins/<your-plugin-name>/` with this layout:
   ```
   plugins/<your-plugin-name>/
   ├── manifest.json           # required — plugin metadata
   ├── README.md               # required — install + usage docs
   ├── skills/                 # optional — Claude skills
   ├── commands/               # optional — slash commands
   ├── mcp/                    # optional — MCP server config
   └── hooks/                  # optional — install/uninstall scripts
   ```
3. **Register** the plugin by adding an entry to
   `.claude-plugin/marketplace.json` under the `plugins` array.
4. **Open a PR** against `main` with a clear description of what the
   plugin does, who it's for, and how you tested it.

## Naming conventions

- Plugin directory name: `kebab-case`, matches the `name` field in
  `manifest.json` and the marketplace entry.
- Commands: prefix with a short namespace, e.g. `/cbm-impact`, not
  `/impact`, to avoid collisions.

## Required quality bar

- **Works offline** — post-install hook fails loudly, not silently.
- **Idempotent install** — re-running `/plugin install` does not break
  a working install.
- **Clean uninstall** — `pre-uninstall.sh` removes what the plugin
  created; user data (caches, config) is left alone.
- **Documented** — README covers install, first-use, troubleshooting,
  and uninstall.

## Testing before PR

At minimum:

1. Install locally via `/plugin install file://$(pwd)` (or equivalent).
2. Run each documented command at least once on a real repo.
3. Uninstall cleanly, reinstall, verify no drift.

## CI

This repo runs schema validation on `.claude-plugin/marketplace.json`
and a smoke-test install for each plugin in `plugins/`. PRs that fail
CI will not be merged — fix the build first.

## Review process

- **Tier 1 (automated):** JSON schema + smoke-install.
- **Tier 2 (maintainer review):** Hyper Commerce maintainer checks
  naming, docs, security posture, and fit with the marketplace theme.
- **Turnaround:** target 5 business days; complex plugins may take
  longer.

## Security

Do not submit plugins that:

- Request secrets in plaintext (use environment variables).
- Auto-exfiltrate data to third-party services without explicit user
  consent in the hook script.
- Run as root or require sudo in the post-install hook.

Security concerns:
[SECURITY.md](https://github.com/hypercommerce-vn/codebase-map/blob/main/SECURITY.md).

## Questions

Open an issue or email hypercdp@gmail.com.
