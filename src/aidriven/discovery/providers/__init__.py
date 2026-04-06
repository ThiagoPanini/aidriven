"""Built-in provider registration.

Importing this module creates the default :class:`ProviderRegistry` instance
pre-populated with all built-in providers (VS Code, Cursor, Kiro).
"""

from __future__ import annotations

from aidriven.discovery._providers import ProviderRegistry
from aidriven.discovery.providers._cursor import CursorProvider
from aidriven.discovery.providers._kiro import KiroProvider
from aidriven.discovery.providers._vscode import VSCodeProvider

#: Default registry used by :func:`aidriven.discovery.discover_ides` when no
#: custom registry is provided.
default_registry: ProviderRegistry = ProviderRegistry()
default_registry.register(VSCodeProvider())
default_registry.register(CursorProvider())
default_registry.register(KiroProvider())

__all__ = ["default_registry"]
