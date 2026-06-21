"""ID and slug helpers for normalized entities."""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return cleaned


def build_team_id(tournament_id: str, team_name: str) -> str:
    return f"{tournament_id}:{slugify(team_name)}"


def build_player_id(tournament_id: str, team_name: str, player_name: str) -> str:
    return f"{tournament_id}:{slugify(team_name)}:{slugify(player_name)}"


def build_membership_id(tournament_id: str, team_name: str, player_name: str) -> str:
    return build_player_id(tournament_id, team_name, player_name)
