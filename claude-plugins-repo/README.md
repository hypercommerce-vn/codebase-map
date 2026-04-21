# Claude Plugins by Hyper Commerce

Curated plugins for Claude Code and Cowork, maintained by
[Hyper Commerce](https://hypercommerce.vn).

## Available plugins

| Plugin | Version | Description |
|--------|:-------:|-------------|
| [codebase-map](plugins/codebase-map/) | 2.5.0 | Function dependency graph for Python/TypeScript · MCP auto-invoke · 5 tools · Skill + 3 slash commands |
| [codebase-map-ai-agent](plugins/codebase-map-ai-agent/) | 0.1.0 | **Archetype pack (AI Agent Knowledge)** — bilingual EN/VI · maps Claude/LangChain/AutoGen/CrewAI agent structure · 3 slash commands (`/agent-overview`, `/agent-impact`, `/agent-refactor-plan`) |
| [codebase-map-saas](plugins/codebase-map-saas/) | 0.1.0 | **Archetype pack (SaaS B2B Onboarding)** — bilingual EN/VI · onboards engineers to CRM/CDP/eCommerce multi-tenant SaaS · 3 slash commands (`/saas-onboard`, `/saas-apis`, `/saas-tier-logic`) |

## Install a plugin

### Via Claude Code CLI

Add the marketplace once, then install plugins by name:

```
/plugin marketplace add hypercommerce-vn/claude-plugins
/plugin install codebase-map@hypercommerce-vn
/plugin install codebase-map-ai-agent@hypercommerce-vn
/plugin install codebase-map-saas@hypercommerce-vn
```

### Via Cowork (research preview)

In a Cowork session:

```
/plugin install codebase-map
/plugin install codebase-map-ai-agent
/plugin install codebase-map-saas
```

### Manual install

Clone this repo and follow the plugin's README for step-by-step install.

## Plugin roadmap

- **Q2 2026** — codebase-map (Python + TypeScript support · MCP server)
- **Q2 2026** — codebase-map-js (adds JavaScript parser · planned for CBM v2.4)
- **Q2 2026** — codebase-map-java (adds Java parser · planned for CBM v2.4)

## For plugin authors

See [CONTRIBUTING.md](CONTRIBUTING.md) for submission guidelines.

## License

MIT — see [LICENSE](LICENSE).

## About

Maintained by [Hyper Commerce](https://hypercommerce.vn).
Contact: hypercdp@gmail.com

---

*For CBM-specific issues: https://github.com/hypercommerce-vn/codebase-map/issues*
