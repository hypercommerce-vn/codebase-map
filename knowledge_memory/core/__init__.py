"""KMP Core — vertical-agnostic platform services.

The core never imports from ``knowledge_memory.verticals`` (enforced by
import-linter in M0-04). Sub-packages follow architecture.md section 3:

- ``vault``     — storage abstraction (BaseVault)
- ``learners``  — learner runtime + Pattern dataclass
- ``parsers``   — parser abstraction + Evidence dataclass
- ``ai``        — multi-LLM gateway (BYOK)
- ``mcp``       — MCP tool/resource registry
- ``licensing`` — Ed25519 offline license verification
- ``cli``       — shared CLI framework
- ``telemetry`` — privacy-safe local telemetry
- ``config``    — YAML config loader
"""

# HC-AI | ticket: KMP-M0-01
