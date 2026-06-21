"""Reusable query helpers for player list and detail views."""

from __future__ import annotations

from typing import Any

from app.database.repository import SquadAdvisorRepository


def _safe_int(value: int | None) -> int:
    return value or 0


def list_player_summary_rows(
    name_query: str | None = None,
    team_id: str | None = None,
    position_group: str | None = None,
    limit: int = 200,
    repo: SquadAdvisorRepository | None = None,
) -> list[dict[str, Any]]:
    owns_repo = repo is None
    repo = repo or SquadAdvisorRepository()
    try:
        rows = repo.search_player_rows(
            name_query=name_query,
            team_id=team_id,
            position_group=position_group,
            limit=limit,
        )
        return [
            {
                "player_id": player.id,
                "full_name": player.full_name,
                "team_id": team.id,
                "team_name": team.name,
                "group_name": team.group_name,
                "shirt_number": membership.shirt_number,
                "position_group": membership.position_group,
                "caps": membership.caps or 0,
                "goals": membership.goals or 0,
                "club_name": player.club_name,
                "birth_date": player.birth_date,
                "is_captain": membership.is_captain,
                "has_report": report is not None,
            }
            for player, membership, team, report in rows
        ]
    finally:
        if owns_repo:
            repo.close()


def get_player_profile_data(
    player_id: str,
    repo: SquadAdvisorRepository | None = None,
) -> dict[str, Any]:
    owns_repo = repo is None
    repo = repo or SquadAdvisorRepository()
    try:
        row = repo.get_player_context(player_id)
        if row is None:
            raise SystemExit(f"Player not found: {player_id}")

        player, membership, team, report = row
        squad = repo.get_team_squad(team.id)

        caps_sorted = sorted(
            squad,
            key=lambda item: (_safe_int(item[0].caps), item[1].full_name),
            reverse=True,
        )
        goals_sorted = sorted(
            squad,
            key=lambda item: (_safe_int(item[0].goals), item[1].full_name),
            reverse=True,
        )

        caps_rank = next(
            (index for index, (_, squad_player) in enumerate(caps_sorted, start=1) if squad_player.id == player.id),
            None,
        )
        goals_rank = next(
            (index for index, (_, squad_player) in enumerate(goals_sorted, start=1) if squad_player.id == player.id),
            None,
        )

        same_position_peers = []
        for peer_membership, peer_player in squad:
            if peer_player.id == player.id:
                continue
            if peer_membership.position_group != membership.position_group:
                continue
            same_position_peers.append(
                {
                    "player_id": peer_player.id,
                    "full_name": peer_player.full_name,
                    "caps": peer_membership.caps or 0,
                    "goals": peer_membership.goals or 0,
                    "club_name": peer_player.club_name,
                }
            )

        return {
            "player_id": player.id,
            "full_name": player.full_name,
            "normalized_name": player.normalized_name,
            "birth_date": player.birth_date,
            "nationality": player.nationality,
            "club_name": player.club_name,
            "club_country": player.club_country,
            "preferred_position": player.preferred_position,
            "profile_source_url": player.profile_source_url,
            "team_id": team.id,
            "team_name": team.name,
            "group_name": team.group_name,
            "shirt_number": membership.shirt_number,
            "position_group": membership.position_group,
            "caps": membership.caps or 0,
            "goals": membership.goals or 0,
            "is_captain": membership.is_captain,
            "source_document_id": membership.source_document_id,
            "caps_rank_in_team": caps_rank,
            "goals_rank_in_team": goals_rank,
            "same_position_peer_count": len(same_position_peers),
            "same_position_peers": same_position_peers[:6],
            "team_top_caps": [
                {
                    "player_id": squad_player.id,
                    "full_name": squad_player.full_name,
                    "caps": squad_membership.caps or 0,
                }
                for squad_membership, squad_player in caps_sorted[:5]
            ],
            "team_top_goals": [
                {
                    "player_id": squad_player.id,
                    "full_name": squad_player.full_name,
                    "goals": squad_membership.goals or 0,
                }
                for squad_membership, squad_player in goals_sorted[:5]
            ],
            "player_report": (
                {
                    "summary": report.summary,
                    "strengths": report.strengths,
                    "concerns": report.concerns,
                    "role_tags": report.role_tags,
                    "evidence_note": report.evidence_note,
                    "prompt_version": report.prompt_version,
                    "model_name": report.model_name,
                }
                if report is not None
                else None
            ),
        }
    finally:
        if owns_repo:
            repo.close()
