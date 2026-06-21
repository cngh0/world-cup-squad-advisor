"""Show one normalized team and its squad members."""

from __future__ import annotations

from app.database.repository import SquadAdvisorRepository
from app.domain.ids import build_team_id


TOURNAMENT_ID = "fifa-world-cup-2026"


def main(team_name: str) -> None:
    repo = SquadAdvisorRepository()
    try:
        team_id = build_team_id(TOURNAMENT_ID, team_name)
        team = repo.get_team_by_id(team_id)
        if team is None:
            raise SystemExit(f"Team not found: {team_name}")

        print("Team")
        print("-" * 50)
        print(f"id={team.id}")
        print(f"name={team.name}")
        print(f"group={team.group_name}")
        print(f"url={team.official_page_url}")
        print()

        squad = repo.get_team_squad(team_id)
        print(f"Squad Members: {len(squad)}")
        print("-" * 50)
        for membership, player in squad:
            print(
                f"#{membership.shirt_number or '-':>2} "
                f"{membership.position_group or '--':<2} "
                f"{player.full_name} | caps={membership.caps} "
                f"goals={membership.goals} | club={player.club_name}"
            )
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py show-team-squad <team_name>`")
