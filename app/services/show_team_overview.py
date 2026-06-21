"""Show a compact overview for one normalized team."""

from __future__ import annotations

from collections import Counter

from app.database.repository import SquadAdvisorRepository
from app.domain.ids import build_team_id


TOURNAMENT_ID = "fifa-world-cup-2026"


def _safe_sum(values: list[int | None]) -> int:
    return sum(value or 0 for value in values)


def main(team_name: str) -> None:
    repo = SquadAdvisorRepository()
    try:
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
        captains = [p.full_name for m, p in squad if m.is_captain]

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

        print("Team Overview")
        print("-" * 60)
        print(f"id={team.id}")
        print(f"name={team.name}")
        print(f"group={team.group_name}")
        print(f"squad_size={len(memberships)}")
        print(
            "positions="
            f"GK:{position_counts.get('GK', 0)} "
            f"DF:{position_counts.get('DF', 0)} "
            f"MF:{position_counts.get('MF', 0)} "
            f"FW:{position_counts.get('FW', 0)}"
        )
        print(f"total_caps={total_caps}")
        print(f"total_goals={total_goals}")
        print(f"average_caps={average_caps:.1f}")
        print(f"captains={', '.join(captains) if captains else '-'}")
        print()

        print("Most Capped")
        print("-" * 60)
        for membership, player in top_caps:
            print(
                f"{player.full_name} | caps={membership.caps or 0} "
                f"goals={membership.goals or 0} | club={player.club_name}"
            )
        print()

        print("Top Scorers")
        print("-" * 60)
        for membership, player in top_goals:
            print(
                f"{player.full_name} | goals={membership.goals or 0} "
                f"caps={membership.caps or 0} | club={player.club_name}"
            )
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py show-team-overview <team_name>`")
