#!/usr/bin/env bash
# HC-AI | ticket: FDD-TOOL-CODEMAP
# Pre-uninstall hook — cleanup codebase-map from pipx.

set -euo pipefail

echo "[codebase-map plugin] Removing codebase-map CLI..."

if command -v pipx > /dev/null 2>&1 && pipx list 2>/dev/null | grep -q 'codebase-map'; then
    pipx uninstall codebase-map || true
    echo "[codebase-map plugin] ✅ Uninstalled codebase-map."
else
    echo "[codebase-map plugin] codebase-map not installed via pipx — skipping."
fi

echo "[codebase-map plugin] Cleanup done."
