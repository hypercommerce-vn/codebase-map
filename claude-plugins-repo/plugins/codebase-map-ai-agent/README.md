# Codebase Map — AI Agent Knowledge Pack

Archetype plugin for developers building Claude agents, LangChain/AutoGen
workflows, CrewAI crews, or any multi-agent orchestration codebase.

Gói archetype dành cho dev xây Claude agents, workflow LangChain/AutoGen,
crew CrewAI, hoặc bất kỳ codebase orchestration multi-agent nào.

---

## English

### What ships in this pack

| Component | Purpose |
|-----------|---------|
| Skill `codebase-map-ai-agent` | Auto-triggers on "agent structure", "agent tools", "what does this agent do", "multi-agent dependencies", "agent entry point" |
| `/agent-overview` | Map agent classes, tool registry, entry points, orchestration layer — 5-bullet summary |
| `/agent-impact <name>` | Blast radius for an agent class or tool method, bucketed by agent role |
| `/agent-refactor-plan` | Staged refactor plan (3 stages, sorted by blast radius) |

This pack **reuses the main plugin's 5 MCP tools** — no new backend, no new
Python. The value is in the agent-specific framing of prompts, output
bucketing, and rollout advice (tool signature migration pattern).

### Prerequisite

This pack depends on the main `codebase-map` plugin (for the MCP server) or
a manual install of `codebase-map[mcp]>=2.4.0`. The post-install hook
installs it automatically via pipx.

### Install

In Claude Code:

```
/plugin marketplace add hypercommerce-vn/claude-plugins
/plugin install codebase-map-ai-agent@hypercommerce-vn
```

### First use

```bash
cd /path/to/your/agent-repo
codebase-map generate -c codebase-map.yaml
```

Then in Claude Code:

```
/agent-overview
```

Claude returns a 5-bullet map of the agent codebase. Next, pick a method and
check its blast radius:

```
/agent-impact ResearchAgent.search
```

Or plan a full refactor:

```
/agent-refactor-plan
```

### When to use vs main plugin

| Question | Use |
|----------|-----|
| "What does this agent do?" | `/agent-overview` |
| "How is this repo organized?" (non-agent) | `/cbm-onboard` (main plugin) |
| "If I change this tool, what breaks?" | `/agent-impact` (agent-aware bucketing) |
| "If I change this function, what breaks?" (non-agent) | `/cbm-impact` (main plugin) |

### Frameworks recognized

- Anthropic Agent SDK · LangChain · AutoGen · CrewAI · custom `tools=[...]` patterns

### Links

- Main repo: https://github.com/hypercommerce-vn/codebase-map
- Issues: https://github.com/hypercommerce-vn/codebase-map/issues
- License: MIT

---

## Tiếng Việt

### Nội dung pack

| Thành phần | Mục đích |
|------------|----------|
| Skill `codebase-map-ai-agent` | Tự động kích hoạt khi gặp "cấu trúc agent", "công cụ agent", "agent này làm gì", "phụ thuộc multi-agent", "điểm vào agent" |
| `/agent-overview` | Map agent class, tool registry, entry point, lớp orchestration — tóm tắt 5 gạch đầu dòng |
| `/agent-impact <tên>` | Tác động khi đổi một agent class hay tool method, phân loại theo vai trò |
| `/agent-refactor-plan` | Kế hoạch refactor theo giai đoạn (3 stage, xếp theo blast radius) |

Pack này **tái sử dụng 5 MCP tool của plugin chính** — không có backend mới,
không có Python mới. Giá trị nằm ở cách khung câu hỏi riêng cho agent, cách
phân loại output, và lời khuyên rollout (pattern migration tool signature).

### Điều kiện tiên quyết

Pack này phụ thuộc plugin `codebase-map` chính (lấy MCP server) hoặc
install thủ công `codebase-map[mcp]>=2.4.0`. Post-install hook tự cài qua pipx.

### Cài đặt

Trong Claude Code:

```
/plugin marketplace add hypercommerce-vn/claude-plugins
/plugin install codebase-map-ai-agent@hypercommerce-vn
```

### Dùng lần đầu

```bash
cd /path/to/your/agent-repo
codebase-map generate -c codebase-map.yaml
```

Sau đó trong Claude Code:

```
/agent-overview
```

Claude trả về map 5 gạch đầu dòng của codebase agent. Tiếp theo, chọn một
method và kiểm tra blast radius:

```
/agent-impact ResearchAgent.search
```

Hoặc lập kế hoạch refactor đầy đủ:

```
/agent-refactor-plan
```

### Khi nào dùng pack này vs plugin chính

| Câu hỏi | Dùng |
|---------|------|
| "Agent này làm gì?" | `/agent-overview` |
| "Repo này tổ chức ra sao?" (không phải agent) | `/cbm-onboard` (plugin chính) |
| "Nếu đổi tool này, cái gì vỡ?" | `/agent-impact` (phân loại theo agent) |
| "Nếu đổi function này, cái gì vỡ?" (không phải agent) | `/cbm-impact` (plugin chính) |

### Framework được nhận diện

- Anthropic Agent SDK · LangChain · AutoGen · CrewAI · pattern `tools=[...]` tự định nghĩa

### Liên kết

- Repo chính: https://github.com/hypercommerce-vn/codebase-map
- Issues: https://github.com/hypercommerce-vn/codebase-map/issues
- License: MIT
