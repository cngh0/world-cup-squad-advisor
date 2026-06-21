"""View-model builders for the World Cup Squad Advisor web pages."""

from __future__ import annotations

from collections import Counter

from app.database.repository import SquadAdvisorRepository
from app.services.advisor_presets import list_advisor_presets
from app.services.advisor_service import (
    get_advisor_session_detail,
    list_advisor_session_summaries,
)
from app.services.player_queries import (
    get_player_profile_data,
    list_player_summary_rows,
)
from app.services.team_queries import (
    get_team_comparison_data,
    get_team_overview_data,
    list_team_summary_rows,
)


def _team_option_rows(team_summaries: list[dict]) -> list[dict]:
    return [
        {
            "id": summary["team_id"],
            "name": summary["team_name"],
            "group_name": summary["group_name"],
        }
        for summary in team_summaries
    ]


def _build_cited_rows(
    repo: SquadAdvisorRepository,
    cited_team_ids: list[str],
    cited_player_ids: list[str],
) -> tuple[list[dict], list[dict]]:
    cited_teams = []
    for team_id in cited_team_ids:
        team = repo.get_team_by_id(team_id)
        if team is not None:
            cited_teams.append(
                {
                    "team_id": team.id,
                    "team_name": team.name,
                }
            )

    cited_players = []
    for player_id in cited_player_ids:
        player_context = repo.get_player_context(player_id)
        if player_context is None:
            continue
        player, membership, team, player_report = player_context
        cited_players.append(
            {
                "player_id": player.id,
                "full_name": player.full_name,
                "team_name": team.name,
            }
        )

    return cited_teams, cited_players


def build_dashboard_page_data() -> dict:
    repo = SquadAdvisorRepository()
    try:
        team_summaries = list_team_summary_rows(repo=repo)
        recent_team_reports = repo.get_recent_team_reports(limit=6)
        recent_player_reports = repo.get_recent_player_reports(limit=6)
        group_counts = Counter(summary["group_name"] for summary in team_summaries)
        most_capped = sorted(
            team_summaries,
            key=lambda item: (item["total_caps"], item["team_name"]),
            reverse=True,
        )[:6]
        most_goals = sorted(
            team_summaries,
            key=lambda item: (item["total_goals"], item["team_name"]),
            reverse=True,
        )[:6]

        return {
            "page_title": "World Cup Squad Workbench",
            "subtitle": "Inspect squads, compare teams, and trace normalized tournament data.",
            "stats": [
                {"label": "Teams", "value": repo.get_team_count(), "hint": "normalized squads"},
                {"label": "Players", "value": repo.get_player_count(), "hint": "current player rows"},
                {
                    "label": "Squad Rows",
                    "value": sum(summary["squad_size"] for summary in team_summaries),
                    "hint": "team-player memberships",
                },
                {
                    "label": "Raw Documents",
                    "value": repo.get_raw_document_count(),
                    "hint": "saved evidence pages",
                },
                {
                    "label": "Team Reports",
                    "value": repo.get_team_report_count(),
                    "hint": "AI-enriched squad reports",
                },
                {
                    "label": "Player Reports",
                    "value": repo.get_player_report_count(),
                    "hint": "AI-enriched player reports",
                },
                {
                    "label": "Advisor Sessions",
                    "value": repo.get_advisor_session_count(),
                    "hint": "saved multi-turn question threads",
                },
            ],
            "group_rows": [
                {"group_name": group_name, "teams": count}
                for group_name, count in sorted(group_counts.items())
            ],
            "most_capped": most_capped,
            "most_goals": most_goals,
            "recent_team_reports": [
                {
                    "team_id": team.id,
                    "team_name": team.name,
                    "summary": report.summary,
                    "prompt_version": report.prompt_version,
                }
                for report, team in recent_team_reports
            ],
            "recent_player_reports": [
                {
                    "player_id": player.id,
                    "full_name": player.full_name,
                    "team_name": team.name,
                    "summary": report.summary,
                    "prompt_version": report.prompt_version,
                }
                for report, player, membership, team in recent_player_reports
            ],
            "recent_advisor_sessions": list_advisor_session_summaries(limit=5),
        }
    finally:
        repo.close()


def build_teams_page_data(group: str | None = None) -> dict:
    repo = SquadAdvisorRepository()
    try:
        team_summaries = list_team_summary_rows(repo=repo)
        groups = sorted({summary["group_name"] for summary in team_summaries if summary["group_name"]})
        if group:
            team_summaries = [summary for summary in team_summaries if summary["group_name"] == group]

        return {
            "page_title": "Teams",
            "subtitle": "Browse normalized squads and jump into a team detail page.",
            "groups": groups,
            "selected_group": group or "",
            "teams": team_summaries,
        }
    finally:
        repo.close()


def build_team_detail_page_data(team_id: str) -> dict:
    repo = SquadAdvisorRepository()
    try:
        overview = get_team_overview_data(team_id=team_id, repo=repo)
        team_report = repo.get_team_report(team_id)
        report_data = None
        if team_report is not None:
            report_data = {
                "summary": team_report.summary,
                "style_of_play": team_report.style_of_play,
                "strengths": team_report.strengths,
                "risks": team_report.risks,
                "watch_players": team_report.watch_players,
                "evidence_note": team_report.evidence_note,
                "prompt_version": team_report.prompt_version,
                "model_name": team_report.model_name,
            }
        return {
            "page_title": overview["team_name"],
            "subtitle": "Normalized squad detail from the stored Wikipedia evidence page.",
            "team": overview,
            "team_report": report_data,
        }
    finally:
        repo.close()


def build_compare_page_data(
    left_team_id: str | None = None,
    right_team_id: str | None = None,
) -> dict:
    repo = SquadAdvisorRepository()
    try:
        team_summaries = list_team_summary_rows(repo=repo)
        comparison = None
        if left_team_id and right_team_id:
            comparison = get_team_comparison_data(
                left_team_id=left_team_id,
                right_team_id=right_team_id,
                repo=repo,
            )

        return {
            "page_title": "Compare Teams",
            "subtitle": "Compare two squads using the normalized tournament tables.",
            "teams": _team_option_rows(team_summaries),
            "selected_left_team_id": left_team_id or "",
            "selected_right_team_id": right_team_id or "",
            "comparison": comparison,
        }
    finally:
        repo.close()


def build_players_page_data(
    q: str | None = None,
    team_id: str | None = None,
    position_group: str | None = None,
) -> dict:
    repo = SquadAdvisorRepository()
    try:
        player_rows = list_player_summary_rows(
            name_query=q,
            team_id=team_id,
            position_group=position_group,
            repo=repo,
        )
        team_summaries = list_team_summary_rows(repo=repo)
        return {
            "page_title": "Players",
            "subtitle": "Search normalized squad members and open player-level AI notes.",
            "players": player_rows,
            "teams": _team_option_rows(team_summaries),
            "positions": ["GK", "DF", "MF", "FW"],
            "selected_query": q or "",
            "selected_team_id": team_id or "",
            "selected_position_group": position_group or "",
        }
    finally:
        repo.close()


def build_player_detail_page_data(player_id: str) -> dict:
    profile = get_player_profile_data(player_id=player_id)
    return {
        "page_title": profile["full_name"],
        "subtitle": "Normalized player detail with AI-enriched player notes and team context.",
        "player": profile,
    }


def build_advisor_page_data(
    session_id: str | None = None,
) -> dict:
    repo = SquadAdvisorRepository()
    try:
        team_summaries = list_team_summary_rows(repo=repo)
        session_summaries = list_advisor_session_summaries(limit=12)
        current_session = get_advisor_session_detail(session_id) if session_id else None
        latest_assistant_message = None
        cited_teams = []
        cited_players = []
        selected_team_ids = []

        if current_session is not None:
            selected_team_ids = current_session["selected_team_ids"]
            assistant_messages = [
                message
                for message in current_session["messages"]
                if message["role"] == "assistant"
            ]
            if assistant_messages:
                latest_assistant_message = assistant_messages[-1]
                cited_teams, cited_players = _build_cited_rows(
                    repo=repo,
                    cited_team_ids=latest_assistant_message["cited_team_ids"],
                    cited_player_ids=latest_assistant_message["cited_player_ids"],
                )

        return {
            "page_title": "Advisor",
            "subtitle": "Ask scoped questions over stored squad data, save the thread, and continue the conversation later.",
            "teams": _team_option_rows(team_summaries),
            "presets": list_advisor_presets(),
            "selected_team_ids": selected_team_ids,
            "sessions": session_summaries,
            "current_session": current_session,
            "active_session_id": current_session["session_id"] if current_session else "",
            "latest_assistant_message": latest_assistant_message,
            "cited_teams": cited_teams,
            "cited_players": cited_players,
        }
    finally:
        repo.close()
