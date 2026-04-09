"""Vault Service — local-first storage abstraction for every vertical.

See architecture.md §4.1. ``BaseVault`` is the ABC that vertical vaults
(e.g. ``CodebaseVault``) inherit from.
"""

# HC-AI | ticket: KMP-M0-02

from knowledge_memory.core.vault.base import BaseVault

__all__ = ["BaseVault"]
