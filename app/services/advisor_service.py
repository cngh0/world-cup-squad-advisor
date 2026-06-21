"""Build advisor context from stored data and answer scoped questions."""

from __future__ import annotations

import json
from uuid import uuid4

from app.agent.advisor_agent import AdvisorAgent
from app.database.models import AdvisorMessage, AdvisorSession
from app.database.repository import SquadAdvisorRepository
from app.services.advisor_tools import build_advisor_execution_bundle
from app.services.team_queries import get_team_overview_data, list_team_summary_rows


DEFAULT_SESSION_LIST_LIMIT = 12
PROMPT_HISTORY_LIMIT = 6


def _json_dumps(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_load_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def _build_session_title(question: str) -> str:
    cleaned = " ".join(question.split())
    if len(cleaned) <= 72:
        return cleaned
    return f"{cleaned[:69].rstrip()}..."


def _format_timestamp(value) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _format_message_for_history(message: AdvisorMessage) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "generated": message.generated,
    }


def _serialize_advisor_message(message: AdvisorMessage) -> dict:
    return {
        "message_id": message.id,
        "role": message.role,
        "content": message.content,
        "generated": message.generated,
        "task_type": message.task_type,
        "task_label": message.task_label,
        "tool_trace": _json_load_list(message.tool_trace),
        "scope_mode": message.scope_mode,
        "scope_team_ids": _json_load_list(message.scope_team_ids),
        "scope_team_count": message.scope_team_count,
        "scope_player_count": message.scope_player_count,
        "key_points": _json_load_list(message.key_points),
        "cited_team_ids": _json_load_list(message.cited_team_ids),
        "cited_player_ids": _json_load_list(message.cited_player_ids),
        "follow_up_suggestions": _json_load_list(message.follow_up_suggestions),
        "prompt_version": message.prompt_version,
        "model_name": message.model_name,
        "created_at": message.created_at,
        "created_at_label": _format_timestamp(message.created_at),
    }


def _build_team_scope_bundle(
    repo: SquadAdvisorRepository,
    team_id: str,
    max_players: int = 8,
) -> dict:
    overview = get_team_overview_data(team_id=team_id, repo=repo)
    team_report = repo.get_team_report(team_id)
    player_rows = repo.search_player_rows(team_id=team_id, limit=30)
    player_rows = sorted(
        player_rows,
        key=lambda row: (
            row[3] is not None,
            row[1].caps or 0,
            row[1].goals or 0,
            row[0].full_name,
        ),
        reverse=True,
    )

    scoped_players = []
    for player, membership, team, player_report in player_rows[:max_players]:
        scoped_players.append(
            {
                "player_id": player.id,
                "full_name": player.full_name,
                "shirt_number": membership.shirt_number,
                "position_group": membership.position_group,
                "caps": membership.caps or 0,
                "goals": membership.goals or 0,
                "club_name": player.club_name,
                "is_captain": membership.is_captain,
                "player_report_summary": player_report.summary if player_report is not None else None,
                "player_report_role_tags": player_report.role_tags if player_report is not None else None,
            }
        )

    return {
        "team_id": overview["team_id"],
        "team_name": overview["team_name"],
        "group_name": overview["group_name"],
        "squad_size": overview["squad_size"],
        "total_caps": overview["total_caps"],
        "total_goals": overview["total_goals"],
        "average_caps": round(overview["average_caps"], 1),
        "position_counts": overview["position_counts"],
        "captains": overview["captains"],
        "top_caps": overview["top_caps"][:3],
        "top_goals": overview["top_goals"][:3],
        "team_report": (
            {
                "summary": team_report.summary,
                "style_of_play": team_report.style_of_play,
                "strengths": team_report.strengths,
                "risks": team_report.risks,
                "watch_players": team_report.watch_players,
            }
            if team_report is not None
            else None
        ),
        "scoped_players": scoped_players,
    }


def build_advisor_context(
    team_ids: list[str] | None = None,
    max_teams: int = 4,
    max_players_per_team: int = 8,
    repo: SquadAdvisorRepository | None = None,
) -> dict:
    owns_repo = repo is None
    repo = repo or SquadAdvisorRepository()
    try:
        team_summaries = list_team_summary_rows(repo=repo)
        summary_map = {summary["team_id"]: summary for summary in team_summaries}

        if team_ids:
            scoped_team_ids = [team_id for team_id in team_ids if team_id in summary_map]
        else:
            ranked = sorted(
                team_summaries,
                key=lambda row: (
                    repo.get_team_report(row["team_id"]) is not None,
                    row["total_caps"],
                    row["total_goals"],
                ),
                reverse=True,
            )
            scoped_team_ids = [row["team_id"] for row in ranked[:max_teams]]

        teams = [
            _build_team_scope_bundle(repo, team_id=team_id, max_players=max_players_per_team)
            for team_id in scoped_team_ids
        ]

        available_team_ids = [summary["team_id"] for summary in team_summaries]
        available_player_ids = []
        for team_bundle in teams:
            for player in team_bundle["scoped_players"]:
                available_player_ids.append(player["player_id"])

        return {
            "scope_mode": "selected_teams" if team_ids else "auto_top_teams",
            "selected_team_ids": scoped_team_ids,
            "team_count": len(teams),
            "player_count": len(available_player_ids),
            "available_team_ids": available_team_ids,
            "available_player_ids": available_player_ids,
            "teams": teams,
        }
    finally:
        if owns_repo:
            repo.close()


def list_advisor_session_summaries(limit: int = DEFAULT_SESSION_LIST_LIMIT) -> list[dict]:
    repo = SquadAdvisorRepository()
    try:
        sessions = repo.list_advisor_sessions(limit=limit)
        summaries = []
        for session in sessions:
            summaries.append(
                {
                    "session_id": session.id,
                    "title": session.title,
                    "selected_team_ids": _json_load_list(session.selected_team_ids),
                    "message_count": repo.get_advisor_message_count(session.id),
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "created_at_label": _format_timestamp(session.created_at),
                    "updated_at_label": _format_timestamp(session.updated_at),
                }
            )
        return summaries
    finally:
        repo.close()


def get_advisor_session_detail(session_id: str) -> dict | None:
    repo = SquadAdvisorRepository()
    try:
        session = repo.get_advisor_session_by_id(session_id)
        if session is None:
            return None

        messages = repo.list_advisor_messages(session_id=session_id)
        return {
            "session_id": session.id,
            "title": session.title,
            "selected_team_ids": _json_load_list(session.selected_team_ids),
            "message_count": len(messages),
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "created_at_label": _format_timestamp(session.created_at),
            "updated_at_label": _format_timestamp(session.updated_at),
            "messages": [_serialize_advisor_message(message) for message in messages],
        }
    finally:
        repo.close()


def answer_advisor_question(
    question: str,
    team_ids: list[str] | None = None,
    session_id: str | None = None,
    session_title: str | None = None,
) -> dict:
    cleaned_question = question.strip()
    if not cleaned_question:
        raise SystemExit("Question must not be empty.")

    repo = SquadAdvisorRepository()
    try:
        existing_session = None
        created_session = False
        if session_id:
            existing_session = repo.get_advisor_session_by_id(session_id)

        effective_team_ids = team_ids
        if existing_session is not None and effective_team_ids is None:
            effective_team_ids = _json_load_list(existing_session.selected_team_ids)

        conversation_history = []
        if existing_session is not None:
            history_messages = repo.list_advisor_messages(
                session_id=existing_session.id,
                limit=PROMPT_HISTORY_LIMIT,
            )
            conversation_history = [
                _format_message_for_history(message)
                for message in history_messages
            ]

        context = build_advisor_context(team_ids=effective_team_ids, repo=repo)
        execution_bundle = build_advisor_execution_bundle(
            question=cleaned_question,
            context=context,
        )
        agent = AdvisorAgent()
        result = agent.answer(
            question=cleaned_question,
            agent_context=execution_bundle["agent_context"],
            conversation_history=conversation_history,
        )

        target_session_id = existing_session.id if existing_session is not None else f"advsess-{uuid4().hex[:12]}"
        selected_team_ids_json = _json_dumps(context["selected_team_ids"])
        tool_trace_json = _json_dumps([
            f"{step['label']}: {step['detail']}"
            for step in execution_bundle["tool_trace"]
        ])

        user_message = AdvisorMessage(
            id=f"advmsg-{uuid4().hex[:12]}",
            session_id=target_session_id,
            role="user",
            content=cleaned_question,
            generated=True,
            task_type=execution_bundle["route_id"],
            task_label=execution_bundle["route_label"],
            tool_trace=tool_trace_json,
            scope_mode=context["scope_mode"],
            scope_team_ids=selected_team_ids_json,
            scope_team_count=context["team_count"],
            scope_player_count=context["player_count"],
        )

        if existing_session is None:
            pending_session = AdvisorSession(
                id=target_session_id,
                title=session_title or _build_session_title(cleaned_question),
                selected_team_ids=selected_team_ids_json,
            )
            created_session = True
        else:
            pending_session = None

        if result is None:
            assistant_message = AdvisorMessage(
                id=f"advmsg-{uuid4().hex[:12]}",
                session_id=target_session_id,
                role="assistant",
                content="The advisor could not generate an answer from the current scoped context.",
                generated=False,
                task_type=execution_bundle["route_id"],
                task_label=execution_bundle["route_label"],
                tool_trace=tool_trace_json,
                scope_mode=context["scope_mode"],
                scope_team_ids=selected_team_ids_json,
                scope_team_count=context["team_count"],
                scope_player_count=context["player_count"],
            )
            existing_session = repo.save_advisor_turn(
                advisor_messages=[user_message, assistant_message],
                session_id=existing_session.id if existing_session is not None else None,
                new_session=pending_session,
                selected_team_ids=selected_team_ids_json,
            )
            return {
                "question": cleaned_question,
                "context": context,
                "execution": execution_bundle,
                "generated": False,
                "answer": None,
                "session": {
                    "session_id": existing_session.id,
                    "title": existing_session.title,
                    "created": created_session,
                    "message_count": repo.get_advisor_message_count(existing_session.id),
                },
                "user_message_id": user_message.id,
            }

        valid_team_ids = set(context["available_team_ids"])
        valid_player_ids = set(context["available_player_ids"])

        cited_team_ids = [
            team_id for team_id in result.cited_team_ids if team_id in valid_team_ids
        ]
        cited_player_ids = [
            player_id for player_id in result.cited_player_ids if player_id in valid_player_ids
        ]

        assistant_message = AdvisorMessage(
            id=f"advmsg-{uuid4().hex[:12]}",
            session_id=target_session_id,
            role="assistant",
            content=result.answer,
            generated=True,
            task_type=execution_bundle["route_id"],
            task_label=execution_bundle["route_label"],
            tool_trace=tool_trace_json,
            scope_mode=context["scope_mode"],
            scope_team_ids=selected_team_ids_json,
            scope_team_count=context["team_count"],
            scope_player_count=context["player_count"],
            key_points=_json_dumps(result.key_points),
            cited_team_ids=_json_dumps(cited_team_ids),
            cited_player_ids=_json_dumps(cited_player_ids),
            follow_up_suggestions=_json_dumps(result.follow_up_suggestions),
            prompt_version=agent.prompt_version,
            model_name=agent.model,
        )
        existing_session = repo.save_advisor_turn(
            advisor_messages=[user_message, assistant_message],
            session_id=existing_session.id if existing_session is not None else None,
            new_session=pending_session,
            selected_team_ids=selected_team_ids_json,
        )

        return {
            "question": cleaned_question,
            "context": context,
            "execution": execution_bundle,
            "generated": True,
            "answer": {
                "answer": result.answer,
                "key_points": result.key_points,
                "cited_team_ids": cited_team_ids,
                "cited_player_ids": cited_player_ids,
                "follow_up_suggestions": result.follow_up_suggestions,
                "prompt_version": agent.prompt_version,
                "model_name": agent.model,
            },
            "session": {
                "session_id": existing_session.id,
                "title": existing_session.title,
                "created": created_session,
                "message_count": repo.get_advisor_message_count(existing_session.id),
            },
            "user_message_id": user_message.id,
        }
    finally:
        repo.close()


def run_advisor_turn(
    *,
    question: str | None = None,
    preset_id: str | None = None,
    team_ids: list[str] | None = None,
    session_id: str | None = None,
) -> dict:
    from app.services.advisor_presets import prepare_advisor_turn

    turn = prepare_advisor_turn(
        question=question,
        preset_id=preset_id,
        team_ids=team_ids,
    )
    result = answer_advisor_question(
        question=turn["question"],
        team_ids=turn["team_ids"],
        session_id=session_id,
        session_title=turn["session_title"],
    )
    result["preset"] = turn["preset"]
    return result
