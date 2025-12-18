"""Helpers for loading and inspecting the daily SEDE report digest."""
from typing import Dict, Any, Tuple

from sede_report import get_daily_sede_report


def load_digest() -> Dict[str, Any]:
    """Loads the daily SEDE report digest (shared across API routes)."""
    return get_daily_sede_report()


def count_changes(changes: Dict[str, list] | None, key: str) -> int:
    if not changes:
        return 0
    return len(changes.get(key, []))


def incoming_stats(digest: Dict[str, Any]) -> Tuple[int, int, int]:
    incoming = digest.get("incoming", {})
    stats = incoming.get("stats", {})
    return (
        stats.get("total", 0),
        stats.get("real", 0),
        stats.get("test", 0),
    )
