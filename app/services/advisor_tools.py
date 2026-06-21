"""Heuristic tool routing and scoped workbench outputs for the advisor."""

from __future__ import annotations

from typing import Any


ROUTE_CATALOG: dict[str, dict[str, str]] = {
    "compare_teams": {
        "label": "Compare Teams",
        "summary": "Build side-by-side team cards and compare the scoped squads.",
    },
    "leadership_spine": {
        "label": "Leadership Spine",
        "summary": "Derive the veteran/core leaders across the scoped squads.",
    },
    "defensive_review": {
        "label": "Defensive Review",
        "summary": "Inspect goalkeeper reliability, defensive anchors, and back-line risk.",
    },
    "attacking_core": {
        "label": "Attacking Core",
        "summary": "Inspect scorers, creators, attacking depth, and dependency points.",
    },
    "build_watchlist": {
        "label": "Build Watchlist",
        "summary": "Surface the most interesting or high-leverage players to watch.",
    },
    "team_overview": {
        "label": "Team Overview",
        "summary": "Explain how one scoped team is structured and what to focus on first.",
    },
    "general_scoped_analysis": {
        "label": "General Scoped Analysis",
        "summary": "Answer a scoped question from the available team and player context.",
    },
}


def _route_question(question: str, context: dict) -> tuple[str, str]:
    lowered = question.lower()
    team_count = context["team_count"]

    if any(token in lowered for token in ["watchlist", "breakout", "pay attention", "worth watching"]):
        return "build_watchlist", "The question asks for a shortlist of players to watch."

    if any(token in lowered for token in ["leadership", "captain", "spine", "leaders"]):
        return "leadership_spine", "The question focuses on captaincy, veteran anchors, or squad leadership."

    if any(token in lowered for token in ["defence", "defense", "goalkeeper", "keeper", "back line", "backline"]):
        return "defensive_review", "The question focuses on goalkeeper strength, defenders, or defensive stability."

    if any(token in lowered for token in ["attack", "attacking", "forward", "forwards", "striker", "winger", "scorer", "goal production"]):
        return "attacking_core", "The question focuses on scorers, creators, or attacking structure."

    if team_count >= 2 and any(token in lowered for token in ["compare", "versus", "vs ", "vs.", "better than"]):
        return "compare_teams", "The question asks for a side-by-side judgment between scoped teams."

    if team_count == 1 and any(token in lowered for token in ["understand", "overview", "quickly", "first", "what should i know"]):
        return "team_overview", "The question asks for a first-pass understanding of one scoped team."

    return "general_scoped_analysis", "The question is scoped, but it does not cleanly match a narrower preset route."


def _detect_focus_tags(question: str) -> list[str]:
    lowered = question.lower()
    focus_map = {
        "defence": ["defence", "defense", "back line", "goalkeeper", "keeper"],
        "midfield": ["midfield", "engine room"],
        "attack": ["attack", "forward", "finisher", "striker", "winger"],
        "leadership": ["leadership", "captain", "spine", "leaders"],
        "balance": ["balance", "balanced", "shape", "structure"],
        "depth": ["depth", "bench", "rotation"],
    }
    tags = []
    for tag, keywords in focus_map.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)
    return tags


def _summarize_scoped_players(team_bundle: dict, limit: int = 6) -> list[dict]:
    return [
        {
            "player_id": player["player_id"],
            "full_name": player["full_name"],
            "position_group": player["position_group"],
            "caps": player["caps"],
            "goals": player["goals"],
            "club_name": player["club_name"],
            "is_captain": player["is_captain"],
            "player_report_summary": player["player_report_summary"],
            "player_report_role_tags": player["player_report_role_tags"],
        }
        for player in team_bundle["scoped_players"][:limit]
    ]


def _build_team_cards(context: dict) -> list[dict]:
    cards = []
    for team in context["teams"]:
        report = team["team_report"] or {}
        cards.append(
            {
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "group_name": team["group_name"],
                "squad_size": team["squad_size"],
                "total_caps": team["total_caps"],
                "total_goals": team["total_goals"],
                "average_caps": team["average_caps"],
                "position_counts": team["position_counts"],
                "captains": team["captains"],
                "top_caps": team["top_caps"],
                "top_goals": team["top_goals"],
                "team_report_summary": report.get("summary"),
                "team_report_strengths": report.get("strengths"),
                "team_report_risks": report.get("risks"),
                "watch_players": report.get("watch_players"),
                "scoped_players": _summarize_scoped_players(team),
            }
        )
    return cards


def _position_leaders(team_bundle: dict) -> list[dict]:
    buckets: dict[str, dict] = {}
    for player in team_bundle["scoped_players"]:
        position = player["position_group"] or "UNK"
        current = buckets.get(position)
        rank_key = (
            player["is_captain"],
            player["caps"],
            player["goals"],
        )
        if current is None or rank_key > (
            current["is_captain"],
            current["caps"],
            current["goals"],
        ):
            buckets[position] = {
                "player_id": player["player_id"],
                "full_name": player["full_name"],
                "position_group": position,
                "caps": player["caps"],
                "goals": player["goals"],
                "is_captain": player["is_captain"],
            }
    ordered = []
    for position in ("GK", "DF", "MF", "FW", "UNK"):
        if position in buckets:
            ordered.append(buckets[position])
    return ordered


def _build_leadership_cards(context: dict) -> list[dict]:
    cards = []
    for team in context["teams"]:
        sorted_players = sorted(
            team["scoped_players"],
            key=lambda player: (
                player["is_captain"],
                player["caps"],
                player["goals"],
                player["full_name"],
            ),
            reverse=True,
        )
        cards.append(
            {
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "captains": team["captains"],
                "top_caps": team["top_caps"],
                "leadership_spine": _position_leaders(team),
                "leadership_watch": _summarize_scoped_players(
                    {"scoped_players": sorted_players},
                    limit=5,
                ),
            }
        )
    return cards


def _build_defensive_cards(context: dict) -> list[dict]:
    cards = []
    for team in context["teams"]:
        goalkeepers = sorted(
            [
                player
                for player in team["scoped_players"]
                if player["position_group"] == "GK"
            ],
            key=lambda player: (
                player["caps"],
                player["goals"],
                player["full_name"],
            ),
            reverse=True,
        )
        defenders = sorted(
            [
                player
                for player in team["scoped_players"]
                if player["position_group"] == "DF"
            ],
            key=lambda player: (
                player["is_captain"],
                player["caps"],
                player["goals"],
                player["full_name"],
            ),
            reverse=True,
        )
        report = team["team_report"] or {}
        goalkeeper_caps = [player["caps"] for player in goalkeepers]
        risk_signals = []
        if goalkeeper_caps and max(goalkeeper_caps) < 10:
            risk_signals.append("goalkeeper_experience_low")
        if sum(1 for player in defenders if player["caps"] >= 40) < 2:
            risk_signals.append("few_high-cap_defenders")
        if report.get("risks"):
            risk_signals.append("team_report_flags_risk")

        cards.append(
            {
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "captains": team["captains"],
                "goalkeepers": _summarize_scoped_players({"scoped_players": goalkeepers}, limit=3),
                "defensive_anchors": _summarize_scoped_players({"scoped_players": defenders}, limit=4),
                "top_caps": team["top_caps"],
                "team_report_strengths": report.get("strengths"),
                "team_report_risks": report.get("risks"),
                "risk_signals": risk_signals,
            }
        )
    return cards


def _build_attacking_cards(context: dict) -> list[dict]:
    cards = []
    for team in context["teams"]:
        attackers = sorted(
            [
                player
                for player in team["scoped_players"]
                if player["position_group"] in {"FW", "MF"}
            ],
            key=lambda player: (
                player["goals"],
                player["caps"],
                player["full_name"],
            ),
            reverse=True,
        )
        forwards = [player for player in attackers if player["position_group"] == "FW"]
        midfielders = [player for player in attackers if player["position_group"] == "MF"]
        report = team["team_report"] or {}
        top_goal_rows = team["top_goals"]
        top_two_goals = sum(item["goals"] for item in top_goal_rows[:2])
        top_five_goals = sum(item["goals"] for item in top_goal_rows[:5])
        dependency_signal = "balanced"
        if top_five_goals > 0 and top_two_goals / top_five_goals >= 0.65:
            dependency_signal = "top_heavy"

        cards.append(
            {
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "top_goal_rows": top_goal_rows,
                "forward_core": _summarize_scoped_players({"scoped_players": forwards}, limit=4),
                "midfield_attack_support": _summarize_scoped_players({"scoped_players": midfielders}, limit=4),
                "position_counts": team["position_counts"],
                "team_report_strengths": report.get("strengths"),
                "team_report_watch_players": report.get("watch_players"),
                "dependency_signal": dependency_signal,
            }
        )
    return cards


def _build_watchlist_cards(context: dict) -> list[dict]:
    candidates = []
    for team in context["teams"]:
        for player in team["scoped_players"]:
            candidates.append(
                {
                    "player_id": player["player_id"],
                    "full_name": player["full_name"],
                    "team_id": team["team_id"],
                    "team_name": team["team_name"],
                    "position_group": player["position_group"],
                    "caps": player["caps"],
                    "goals": player["goals"],
                    "is_captain": player["is_captain"],
                    "club_name": player["club_name"],
                    "player_report_summary": player["player_report_summary"],
                    "player_report_role_tags": player["player_report_role_tags"],
                }
            )

    ranked = sorted(
        candidates,
        key=lambda player: (
            player["is_captain"],
            player["goals"],
            player["caps"],
            player["full_name"],
        ),
        reverse=True,
    )
    return ranked[:10]


def _build_tool_outputs(route_id: str, context: dict, focus_tags: list[str]) -> dict[str, Any]:
    if route_id == "compare_teams":
        return {
            "team_cards": _build_team_cards(context),
            "focus_tags": focus_tags,
        }

    if route_id == "leadership_spine":
        return {
            "leadership_cards": _build_leadership_cards(context),
            "focus_tags": focus_tags,
        }

    if route_id == "defensive_review":
        return {
            "defensive_cards": _build_defensive_cards(context),
            "focus_tags": focus_tags,
        }

    if route_id == "attacking_core":
        return {
            "attacking_cards": _build_attacking_cards(context),
            "focus_tags": focus_tags,
        }

    if route_id == "build_watchlist":
        return {
            "watchlist_candidates": _build_watchlist_cards(context),
            "focus_tags": focus_tags,
        }

    if route_id == "team_overview":
        return {
            "team_cards": _build_team_cards(context),
            "focus_tags": focus_tags,
        }

    return {
        "team_cards": _build_team_cards(context),
        "focus_tags": focus_tags,
    }


def build_advisor_execution_bundle(question: str, context: dict) -> dict[str, Any]:
    route_id, route_reason = _route_question(question, context)
    route = ROUTE_CATALOG[route_id]
    focus_tags = _detect_focus_tags(question)
    tool_outputs = _build_tool_outputs(route_id, context, focus_tags)

    team_names = [team["team_name"] for team in context["teams"]]
    team_label = ", ".join(team_names) if team_names else "auto-scoped teams"

    trace = [
        {
            "tool": "resolve_scope",
            "label": "Resolve Scope",
            "detail": (
                f"{context['team_count']} teams / {context['player_count']} scoped players "
                f"for {team_label}"
            ),
        },
        {
            "tool": "route_question",
            "label": "Route Question",
            "detail": f"{route['label']} - {route_reason}",
        },
        {
            "tool": "derive_focus",
            "label": "Derive Focus",
            "detail": ", ".join(focus_tags) if focus_tags else "No narrow focus tags detected.",
        },
        {
            "tool": "prepare_tool_outputs",
            "label": "Prepare Tool Outputs",
            "detail": route["summary"],
        },
    ]

    return {
        "route_id": route_id,
        "route_label": route["label"],
        "route_summary": route["summary"],
        "route_reason": route_reason,
        "focus_tags": focus_tags,
        "tool_trace": trace,
        "tool_outputs": tool_outputs,
        "agent_context": {
            "task_type": route_id,
            "task_label": route["label"],
            "task_summary": route["summary"],
            "route_reason": route_reason,
            "focus_tags": focus_tags,
            "scope": {
                "scope_mode": context["scope_mode"],
                "selected_team_ids": context["selected_team_ids"],
                "team_count": context["team_count"],
                "player_count": context["player_count"],
            },
            "tool_trace": trace,
            "tool_outputs": tool_outputs,
        },
    }
