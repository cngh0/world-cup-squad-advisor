"""Preset prompts for the World Cup squad advisor."""

from __future__ import annotations

from app.services.advisor_service import build_advisor_context


PRESET_CATALOG = [
    {
        "id": "compare_teams",
        "label": "Compare Teams",
        "description": "Get a structured verdict on two squads across balance, defence, attack, and leadership.",
    },
    {
        "id": "scout_core_players",
        "label": "Scout Core Players",
        "description": "Identify the most important players to study first and explain why they matter.",
    },
    {
        "id": "build_watchlist",
        "label": "Build Watchlist",
        "description": "Create a short list of high-leverage or especially watchable players from the scoped teams.",
    },
    {
        "id": "defensive_review",
        "label": "Defensive Review",
        "description": "Review goalkeeper reliability, defensive anchors, and the main back-line risks.",
    },
    {
        "id": "attacking_core",
        "label": "Attacking Core",
        "description": "Focus on scorers, creators, attacking depth, and where each team's threat really comes from.",
    },
]


def list_advisor_presets() -> list[dict]:
    return [dict(preset) for preset in PRESET_CATALOG]


def get_advisor_preset(preset_id: str) -> dict | None:
    for preset in PRESET_CATALOG:
        if preset["id"] == preset_id:
            return dict(preset)
    return None


def _format_team_names(team_names: list[str]) -> str:
    if not team_names:
        return "the scoped teams"
    if len(team_names) == 1:
        return team_names[0]
    if len(team_names) == 2:
        return f"{team_names[0]} and {team_names[1]}"
    return f"{', '.join(team_names[:-1])}, and {team_names[-1]}"


def _format_compact_team_names(team_names: list[str]) -> str:
    if not team_names:
        return "Auto Scope"
    if len(team_names) == 1:
        return team_names[0]
    if len(team_names) == 2:
        return f"{team_names[0]} vs {team_names[1]}"
    preview = ", ".join(team_names[:2])
    return f"{preview} +{len(team_names) - 2}"


def _build_preset_session_title(preset_id: str, team_names: list[str]) -> str:
    compact_names = _format_compact_team_names(team_names)
    if preset_id == "compare_teams":
        return f"Compare Teams: {compact_names}"
    if preset_id == "scout_core_players":
        return f"Scout Core Players: {compact_names}"
    if preset_id == "build_watchlist":
        return f"Build Watchlist: {compact_names}"
    if preset_id == "defensive_review":
        return f"Defensive Review: {compact_names}"
    if preset_id == "attacking_core":
        return f"Attacking Core: {compact_names}"
    return compact_names


def _resolve_team_scope(
    team_ids: list[str] | None,
    *,
    auto_max_teams: int,
    min_teams: int = 0,
    max_teams: int | None = None,
) -> list[dict]:
    selected_context = build_advisor_context(
        team_ids=team_ids,
        max_teams=max_teams or auto_max_teams,
    )
    teams = list(selected_context["teams"])

    if len(teams) >= min_teams:
        if max_teams is not None:
            return teams[:max_teams]
        return teams

    fallback_context = build_advisor_context(team_ids=None, max_teams=max(auto_max_teams, min_teams))
    seen_ids = {team["team_id"] for team in teams}
    for team in fallback_context["teams"]:
        if team["team_id"] in seen_ids:
            continue
        teams.append(team)
        seen_ids.add(team["team_id"])
        if len(teams) >= min_teams:
            break

    if max_teams is not None:
        teams = teams[:max_teams]
    return teams


def prepare_advisor_turn(
    *,
    question: str | None = None,
    preset_id: str | None = None,
    team_ids: list[str] | None = None,
) -> dict:
    cleaned_question = (question or "").strip()

    if preset_id:
        preset = get_advisor_preset(preset_id)
        if preset is None:
            raise ValueError(f"Unknown advisor preset: {preset_id}")

        if preset_id == "compare_teams":
            teams = _resolve_team_scope(
                team_ids,
                auto_max_teams=2,
                min_teams=2,
                max_teams=2,
            )
            names = [team["team_name"] for team in teams]
            generated_question = (
                f"Compare {_format_team_names(names)} across squad balance, defensive reliability, "
                "midfield leadership, attacking depth, and the most important watch players. "
                "End with a concise verdict on what each team currently looks best at."
            )
        elif preset_id == "scout_core_players":
            teams = _resolve_team_scope(
                team_ids,
                auto_max_teams=2,
                min_teams=1,
                max_teams=3,
            )
            names = [team["team_name"] for team in teams]
            generated_question = (
                f"For {_format_team_names(names)}, identify the core players I should study first. "
                "Name the most important players, explain each player's role, and say what part of the squad "
                "or playing identity they help me understand."
            )
        elif preset_id == "build_watchlist":
            teams = _resolve_team_scope(
                team_ids,
                auto_max_teams=4,
                min_teams=1,
                max_teams=4,
            )
            names = [team["team_name"] for team in teams]
            generated_question = (
                f"Build a watchlist from {_format_team_names(names)}. Prioritize the most interesting "
                "or high-leverage players to watch, explain why each belongs on the list, and note what I "
                "should pay attention to when watching them."
            )
        elif preset_id == "defensive_review":
            teams = _resolve_team_scope(
                team_ids,
                auto_max_teams=2,
                min_teams=1,
                max_teams=3,
            )
            names = [team["team_name"] for team in teams]
            generated_question = (
                f"Review {_format_team_names(names)} from a defensive perspective. Compare goalkeeper reliability, "
                "defensive anchors, likely veteran stability at the back, and the main defensive risks or weak points."
            )
        elif preset_id == "attacking_core":
            teams = _resolve_team_scope(
                team_ids,
                auto_max_teams=2,
                min_teams=1,
                max_teams=3,
            )
            names = [team["team_name"] for team in teams]
            generated_question = (
                f"Analyze the attacking core of {_format_team_names(names)}. Focus on scorers, creators, forward depth, "
                "and whether the attack looks distributed or dependent on one or two players."
            )
        else:
            raise ValueError(f"Unsupported advisor preset: {preset_id}")

        return {
            "question": generated_question,
            "team_ids": [team["team_id"] for team in teams],
            "preset": preset,
            "session_title": _build_preset_session_title(preset_id, names),
        }

    if cleaned_question:
        return {
            "question": cleaned_question,
            "team_ids": team_ids or None,
            "preset": None,
            "session_title": None,
        }

    raise ValueError("Provide a question or choose a preset.")
