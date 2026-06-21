"""Compare two normalized teams using simple roster metrics."""

from __future__ import annotations

from collections import Counter

from app.database.repository import SquadAdvisorRepository
from app.domain.ids import build_team_id


TOURNAMENT_ID = "fifa-world-cup-2026"


def _safe_sum(values: list[int | None]) -> int:
    return sum(value or 0 for value in values)


def _team_metrics(repo: SquadAdvisorRepository, team_name: str) -> dict:
    team_id = build_team_id(TOURNAMENT_ID, team_name)
    team = repo.get_team_by_id(team_id)
    if team is None:
        raise SystemExit(f"Team not found: {team_name}")

    squad = repo.get_team_squad(team_id)
    if not squad:
        raise SystemExit(f"No squad rows found for: {team_name}")

    memberships = [membership for membership, _ in squad]
    players = [player for _, player in squad]
    position_counts = Counter(m.position_group or "UNK" for m in memberships)
    total_caps = _safe_sum([m.caps for m in memberships])
    total_goals = _safe_sum([m.goals for m in memberships])
    average_caps = total_caps / len(memberships)

    top_caps = sorted(
        squad,
        key=lambda item: ((item[0].caps or 0), item[1].full_name),
        reverse=True,
    )[:3]
    top_goals = sorted(
        squad,
        key=lambda item: ((item[0].goals or 0), item[1].full_name),
        reverse=True,
    )[:3]

    return {
        "team": team,
        "squad": squad,
        "memberships": memberships,
        "players": players,
        "position_counts": position_counts,
        "total_caps": total_caps,
        "total_goals": total_goals,
        "average_caps": average_caps,
        "top_caps": top_caps,
        "top_goals": top_goals,
    }


def main(left_team_name: str, right_team_name: str) -> None:
    repo = SquadAdvisorRepository()
    try:
        left = _team_metrics(repo, left_team_name)
        right = _team_metrics(repo, right_team_name)

        print("Team Comparison")
        print("-" * 72)
        print(f"left={left['team'].name} | group={left['team'].group_name}")
        print(f"right={right['team'].name} | group={right['team'].group_name}")
        print()

        print("Roster Metrics")
        print("-" * 72)
        print(
            f"squad_size       {left['team'].name}: {len(left['memberships']):>3} | "
            f"{right['team'].name}: {len(right['memberships']):>3}"
        )
        print(
            f"total_caps       {left['team'].name}: {left['total_caps']:>3} | "
            f"{right['team'].name}: {right['total_caps']:>3}"
        )
        print(
            f"average_caps     {left['team'].name}: {left['average_caps']:>5.1f} | "
            f"{right['team'].name}: {right['average_caps']:>5.1f}"
        )
        print(
            f"total_goals      {left['team'].name}: {left['total_goals']:>3} | "
            f"{right['team'].name}: {right['total_goals']:>3}"
        )
        print(
            f"positions GK/DF/MF/FW "
            f"{left['position_counts'].get('GK', 0)}/"
            f"{left['position_counts'].get('DF', 0)}/"
            f"{left['position_counts'].get('MF', 0)}/"
            f"{left['position_counts'].get('FW', 0)}"
            " | "
            f"{right['position_counts'].get('GK', 0)}/"
            f"{right['position_counts'].get('DF', 0)}/"
            f"{right['position_counts'].get('MF', 0)}/"
            f"{right['position_counts'].get('FW', 0)}"
        )
        print()

        print(f"Most Capped - {left['team'].name}")
        print("-" * 72)
        for membership, player in left["top_caps"]:
            print(f"{player.full_name} | caps={membership.caps or 0} | goals={membership.goals or 0}")
        print()

        print(f"Most Capped - {right['team'].name}")
        print("-" * 72)
        for membership, player in right["top_caps"]:
            print(f"{player.full_name} | caps={membership.caps or 0} | goals={membership.goals or 0}")
        print()

        print(f"Top Scorers - {left['team'].name}")
        print("-" * 72)
        for membership, player in left["top_goals"]:
            print(f"{player.full_name} | goals={membership.goals or 0} | caps={membership.caps or 0}")
        print()

        print(f"Top Scorers - {right['team'].name}")
        print("-" * 72)
        for membership, player in right["top_goals"]:
            print(f"{player.full_name} | goals={membership.goals or 0} | caps={membership.caps or 0}")
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py compare-teams <team_a> <team_b>`")
