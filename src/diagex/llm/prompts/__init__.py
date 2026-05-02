"""System prompt builders for each extractor.

Each module in this package exposes `build_system_prompt(...)` returning a list
of content blocks (not a bare string) so the transport layer can stamp
`cache_control` on the stable prefix. See spec §6.2 (prompt caching).
"""

from __future__ import annotations

from diagex.llm.prompts.phase1_query import build_system_prompt

__all__ = ["build_system_prompt"]
