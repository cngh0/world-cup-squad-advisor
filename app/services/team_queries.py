"""Reusable query helpers for team and comparison views."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.database.repository import SquadAdvisorRepository
from app.domain.ids import build_team_id


TOURNAMENT_ID = "fifa-world-cup-2026"


def _safe_sum(values: list[int | None]) -> int:
    return sum(value or 0 for value in values)


def get_team_overview_data(
    team_name: str | None = None,
    team_id: str | None = None,
    repo: SquadAdvisorRepository | None = None,
) -> dict[str, Any]:
    owns_repo = repo is None
    repo = repo or SquadAdvisorRepository()
    try:
        resolved_team_id = team_id or build_team_id(TOURNAMENT_ID, team_name or "")
        team = repo.get_team_by_id(resolved_team_id)
        if team is None:
            raise SystemExit(f"Team not found: {team_name or team_id}")

        squad = repo.get_team_squad(team.id)
        if not squad:
            raise SystemExit(f"No squad rows found for: {team.name}")

        memberships = [membership for membership, _ in squad]
        position_counts = Counter(m.position_group or "UNK" for m in memberships)
        total_caps = _safe_sum([m.caps for m in memberships])
        total_goals = _safe_sum([m.goals for m in memberships])
        average_caps = total_caps / len(memberships)
        captains = [player.full_name for membership, player in squad if membership.is_captain]

        top_caps = sorted(
            squad,
            key=lambda item: ((item[0].caps or 0), item[1].full_name),
            reverse=True,
        )[:5]
        top_goals = sorted(
            squad,
            key=lambda item: ((item[0].goals or 0), item[1].full_name),
            reverse=True,
        )[:5]

        squad_rows = []
        source_document_id = None
        for membership, player in squad:
            if source_document_id is None and membership.source_document_id:
                source_document_id = membership.source_document_id
            squad_rows.append(
                {
                    "player_id": player.id,
                    "shirt_number": membership.shirt_number,
                    "position_group": membership.position_group,
                    "full_name": player.full_name,
                    "caps": membership.caps,
                    "goals": membership.goals,
                    "club_name": player.club_name,
                    "birth_date": player.birth_date,
                    "is_captain": membership.is_captain,
                }
            )

        return {
            "team_id": team.id,
            "team_name": team.name,
            "group_name": team.group_name,
            "official_page_url": team.official_page_url,
            "squad_size": len(memberships),
            "position_counts": dict(position_counts),
            "total_caps": total_caps,
            "total_goals": total_goals,
            "average_caps": average_caps,
            "captains": captains,
            "source_document_id": source_document_id,
            "top_caps": [
                {
                    "player_id": player.id,
                    "full_name": player.full_name,
                    "caps": membership.caps or 0,
                    "goals": membership.goals or 0,
                    "club_name": player.club_name,
                }
                for membership, player in top_caps
            ],
            "top_goals": [
                {
                    "player_id": player.id,
                    "full_name": player.full_name,
                    "goals": membership.goals or 0,
                    "caps": membership.caps or 0,
                    "club_name": player.club_name,
                }
                for membership, player in top_goals
            ],
            "squad": squad_rows,
        }
    finally:
        if owns_repo:
            repo.close()


def list_team_summary_rows(repo: SquadAdvisorRepository | None = None) -> list[dict[str, Any]]:
    owns_repo = repo is None
    repo = repo or SquadAdvisorRepository()
    try:
        rows = []
        for team in repo.list_teams():
            overview = get_team_overview_data(team_id=team.id, repo=repo)
            rows.append(overview)
        return rows
    finally:
        if owns_repo:
            repo.close()


def get_team_comparison_data(
    left_team_name: str | None = None,
    right_team_name: str | None = None,
    left_team_id: str | None = None,
    right_team_id: str | None = None,
    repo: SquadAdvisorRepository | None = None,
) -> dict[str, Any]:
    owns_repo = repo is None
    repo = repo or SquadAdvisorRepository()
    try:
        left = get_team_overview_data(team_name=left_team_name, team_id=left_team_id, repo=repo)
        right = get_team_overview_data(team_name=right_team_name, team_id=right_team_id, repo=repo)
        return {
            "left": left,
            "right": right,
        }
    finally:
        if owns_repo:
            repo.close()
