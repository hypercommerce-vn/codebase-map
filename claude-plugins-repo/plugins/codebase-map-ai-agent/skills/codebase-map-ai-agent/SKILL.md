---
name: codebase-map-ai-agent
description: >
  AI Agent Knowledge — understand the structure, tools, and workflows of any
  Claude agent / LangChain / AutoGen / multi-agent codebase. Maps entry points,
  tool registry, orchestration layers, and blast radius before agent refactors.
  Gói AI Agent Knowledge — hiểu cấu trúc, công cụ, và luồng hoạt động của bất kỳ
  codebase Claude agent / LangChain / AutoGen / multi-agent nào. Map entry points,
  tool registry, orchestration layers, và tác động trước khi refactor agent.
  Triggers: "agent structure", "cấu trúc agent", "agent tools", "công cụ agent",
  "agent workflow", "luồng agent", "refactor agent flow", "what does this agent do",
  "multi-agent dependencies", "agent entry point", "tool registry", "agent orchestration".
---

# Codebase Map — AI Agent Knowledge Pack

## Purpose / Mục đích

**EN:** Agent codebases have a specific shape — one or more entry points (a
`run()`, a FastAPI route, a CLI), a **tool registry** (functions decorated with
`@tool` or registered into an `Agent(...).tools = [...]` list), and
orchestration glue that routes LLM responses to tool calls. This skill reuses
the `codebase-map` MCP tools to map that shape fast.

**VI:** Các codebase agent có một cấu trúc đặc trưng — một hoặc nhiều entry
point (một `run()`, một FastAPI route, một CLI), một **tool registry** (các
hàm được decorator bằng `@tool` hoặc đăng ký vào danh sách
`Agent(...).tools = [...]`), và lớp orchestration điều hướng response từ LLM
đến tool call. Skill này tái sử dụng các MCP tool của `codebase-map` để map
cấu trúc đó nhanh chóng.

## Prerequisite / Điều kiện tiên quyết

**EN:** Requires `codebase-map >= 2.4.0` with MCP extras. A `graph.json` file
must exist at `docs/function-map/graph.json` (run `codebase-map generate`
first, or use `/cbm-onboard` from the main plugin).

**VI:** Cần `codebase-map >= 2.4.0` với MCP extras. File `graph.json` phải
tồn tại tại `docs/function-map/graph.json` (chạy `codebase-map generate`
trước, hoặc dùng `/cbm-onboard` từ plugin chính).

```bash
codebase-map --version  # should be 2.4.0+
ls docs/function-map/graph.json 2>/dev/null || echo "RUN /cbm-onboard FIRST"
```

## Frameworks this pack recognizes / Các framework pack này nhận diện

**EN:** The skill looks for agent-shaped patterns. Common matches:

**VI:** Skill tìm các pattern có dạng agent. Các kiểu phổ biến:

| Framework | Tool registration pattern | Entry point signal |
|-----------|---------------------------|--------------------|
| Anthropic Agent SDK | `ClaudeAgentOptions(tools=[...])` | `query()`, `stream()` |
| LangChain | `@tool` decorator, `Tool(...)` | `AgentExecutor.run()` |
| AutoGen | `register_for_llm()` | `initiate_chat()` |
| CrewAI | `@task`, `Agent(tools=[...])` | `Crew.kickoff()` |
| Custom | Function passed to LLM API with `tools=[...]` | `main()`, route handler |

## Workflow — Three questions this skill answers / Ba câu hỏi skill này trả lời

### 1. "What does this agent do?" / "Agent này làm gì?"

**EN:** Use `/agent-overview` (slash command in this pack). It calls
`cbm_search` for `"agent"` and `"tool"`, then `cbm_query` on each top match
to expose signatures + domains.

**VI:** Dùng `/agent-overview`. Nó gọi `cbm_search` cho `"agent"` và `"tool"`,
sau đó `cbm_query` trên từng match hàng đầu để hiện signature + domain.

### 2. "If I change X, what breaks?" / "Nếu đổi X, cái gì vỡ?"

**EN:** Use `/agent-impact <name>`. Wraps `cbm_impact` with agent-specific
output: groups callers by `tool`, `orchestrator`, `route`, `test` buckets so
you see tool contracts at risk vs downstream workflows.

**VI:** Dùng `/agent-impact <tên>`. Bọc `cbm_impact` với output riêng cho
agent: nhóm caller theo `tool`, `orchestrator`, `route`, `test` để bạn thấy
được tool contract nào đang gặp rủi ro và workflow downstream nào bị ảnh hưởng.

### 3. "How do I refactor the agent flow safely?" / "Làm sao refactor luồng agent an toàn?"

**EN:** Use `/agent-refactor-plan`. Enumerates top public methods, runs
`cbm_impact` on each, sorts by blast radius, recommends a staged rollout
(low-blast first, high-blast last, with deprecation shim pattern).

**VI:** Dùng `/agent-refactor-plan`. Liệt kê các public method hàng đầu,
chạy `cbm_impact` cho từng cái, sort theo blast radius, đề xuất kế hoạch
staged rollout (low-blast trước, high-blast sau, theo pattern deprecation shim).

## MCP tools used / Các MCP tool được sử dụng

**EN:** This pack does NOT register new MCP tools. It reuses the 5 from the
main `codebase-map` plugin:

**VI:** Pack này KHÔNG đăng ký MCP tool mới. Nó tái sử dụng 5 tool từ plugin
`codebase-map` chính:

- `cbm_search "agent"` / `cbm_search "tool"` — discover agent + tool functions
- `cbm_query "<class>"` — expose a specific agent class signature
- `cbm_impact "<name>"` — blast radius for an agent refactor
- `cbm_snapshot_diff` — compare agent structure before/after a refactor
- `cbm_api_catalog` — list HTTP endpoints the agent exposes (if any)

## Rules / Quy tắc

**EN:**

- **Always run `/agent-overview` first** on a new agent repo. It tells you
  whether the codebase is a single-agent, multi-agent, or tool-heavy shape
  before you query specifics.
- **Tool signatures are contracts.** Before changing a tool function body,
  check its blast radius with `/agent-impact <tool_name>`. Tools are called
  by the LLM via JSON schema — breaking their signature breaks prompts.
- **Orchestration layers deserve extra caution.** A function named `run`,
  `execute`, `orchestrate`, or `dispatch` is usually on the hot path. Refactor
  with a feature flag and a snapshot-diff review.
- **If the repo has no `@tool` decorator matches**, it may be a raw-LLM app
  (not tool-using). Tell the user and offer to use the main `codebase-map`
  skill instead.

**VI:**

- **Luôn chạy `/agent-overview` trước** trên một agent repo mới. Nó cho biết
  codebase là dạng single-agent, multi-agent, hay tool-heavy trước khi query
  chi tiết.
- **Tool signature là contract.** Trước khi thay đổi body của tool function,
  kiểm tra blast radius bằng `/agent-impact <tool_name>`. Tool được LLM gọi
  qua JSON schema — đổi signature là phá prompt.
- **Lớp orchestration cần đặc biệt cẩn thận.** Function tên `run`, `execute`,
  `orchestrate`, hoặc `dispatch` thường nằm trên hot path. Refactor với
  feature flag và snapshot-diff review.
- **Nếu repo không có match `@tool` decorator**, có thể đó là một app
  raw-LLM (không dùng tool). Báo user và đề xuất dùng skill `codebase-map`
  chính.

## When not to use / Khi nào không dùng

**EN:**

- Repo is not an AI agent codebase — use the main `codebase-map` skill.
- Single-file script — `grep` is faster.
- The question is about the LLM API itself (not the agent code wrapping it) —
  this skill maps code, not model behavior.

**VI:**

- Repo không phải codebase AI agent — dùng skill `codebase-map` chính.
- Script đơn file — `grep` nhanh hơn.
- Câu hỏi về chính LLM API (không phải code agent wrap nó) — skill này map
  code, không map behavior model.

## Links / Liên kết

- Main plugin: [`codebase-map`](https://github.com/hypercommerce-vn/codebase-map)
- GTM brief: [Project Archetype GTM Strategy](https://github.com/hypercommerce-vn/codebase-map/tree/main/docs/active/cbm-claude-integration)
- Issues: https://github.com/hypercommerce-vn/codebase-map/issues
