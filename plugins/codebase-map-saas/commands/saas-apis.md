---
name: saas-apis
description: >
  Full API catalog for this SaaS — filter by HTTP method or domain, output ready for docs.
  Catalog API đầy đủ của SaaS — lọc theo HTTP method hoặc domain, output sẵn để đưa vào doc.
---

Produce the full API catalog for this SaaS codebase, optionally filtered by HTTP method or domain.

`$ARGUMENTS` parsing rules:
- Empty → full catalog, no filter.
- Single word matching a domain (e.g. `customer`, `billing`, `order`) → filter by domain.
- Single word matching a method (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) → filter by method.
- Anything else → treat as a path prefix filter.

## Steps

1. **Graph presence check.** If `docs/function-map/graph.json` is missing, tell the user to run `/cbm-onboard` first. Stop.

2. **Classify the argument.** Decide which filter to use:

   | `$ARGUMENTS` | Call |
   |--------------|------|
   | empty | `cbm_api_catalog(format="text")` |
   | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` (case-insensitive) | `cbm_api_catalog(method=<upper>, format="text")` |
   | domain keyword (`customer`, `billing`, `order`, `tenant`, `auth`) | `cbm_api_catalog(domain=<kw>, format="text")` |
   | path-like string (starts with `/`) | `cbm_api_catalog(path=<value>, format="text")` |

3. **Run the MCP call.** Example filtered call:

   ```
   cbm_api_catalog(method="POST", format="text")
   ```

4. **Reshape to a Markdown table.** Parse the text output and produce:

   ```markdown
   # API Catalog <filter>

   | Method | Path | Handler | Domain |
   |--------|------|---------|--------|
   | GET | /api/customers | list_customers | customer |
   | POST | /api/customers | create_customer | customer |
   | … | … | … | … |

   **Total:** N endpoints · <filter summary>
   ```

   Group rows by domain in display order: `auth` → `tenant` → core domain (`customer`, `order`, etc.) → integrations (`webhook`, `stripe`, etc.).

5. **If catalog is empty**, the repo has no HTTP layer. Tell the user:

   > "No HTTP endpoints detected — this may be a library, worker, or CLI-only service. Use `/saas-onboard` for a broader overview."

   Stop.

6. **Highlight suspicious patterns.** After the table, add a short "Observations" section if any of:

   - Any `DELETE` route with no auth-required decorator nearby (call `cbm_query` on the handler to check).
   - Two routes with the same path + method — duplicate registration.
   - A `/admin/*` path group visible to unauthenticated handlers.

   If no observations, skip this section.

## Rules

- **Never guess method/domain.** If `$ARGUMENTS` is ambiguous, ask the user to clarify before calling MCP.
- **Do not dump JSON.** MCP `cbm_api_catalog` supports `format="json"` — use `format="text"` for human output, then reshape.
- **Include webhook and integration endpoints.** They are public callables even if not "REST" proper.

## Keep it tight

One Markdown table + optional 3-line observations block. No prose paragraphs — this output is meant to paste into API docs or a team wiki.
