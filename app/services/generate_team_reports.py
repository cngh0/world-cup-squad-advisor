"""Batch-generate AI team reports for teams that do not have one yet."""

from __future__ import annotations

from app.services.generate_team_report import generate_team_report
from app.database.repository import SquadAdvisorRepository


def main(limit: int = 5, replace_existing: bool = False) -> None:
    repo = SquadAdvisorRepository()
    try:
        if replace_existing:
            teams = repo.list_teams()[:limit]
        else:
            teams = repo.list_teams_without_report(limit=limit)
    finally:
        repo.close()

    print(f"Starting batch team report generation for {len(teams)} teams")
    processed = 0
    failed = 0

    for index, team in enumerate(teams, start=1):
        print(f"[{index}/{len(teams)}] Processing {team.name}")
        result = generate_team_report(
            team_name=team.name,
            replace=True,
            confirm_save=False,
        )
        if result.get("saved"):
            processed += 1
            print("Team report saved.")
        else:
            failed += 1
            print("Team report failed.")

    print(f"Total teams: {len(teams)}")
    print(f"Processed: {processed}")
    print(f"Failed: {failed}")
