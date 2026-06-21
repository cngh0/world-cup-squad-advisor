"""Batch-generate AI player reports for players that do not have one yet."""

from __future__ import annotations

from app.database.repository import SquadAdvisorRepository
from app.services.generate_player_report import generate_player_report


def main(limit: int = 5, replace_existing: bool = False) -> None:
    repo = SquadAdvisorRepository()
    try:
        if replace_existing:
            rows = repo.search_player_rows(limit=limit)
        else:
            rows = repo.list_players_without_report(limit=limit)
    finally:
        repo.close()

    print(f"Starting batch player report generation for {len(rows)} players")
    processed = 0
    failed = 0

    for index, row in enumerate(rows, start=1):
        if replace_existing:
            player, membership, team, _ = row
        else:
            player, membership, team = row
        print(f"[{index}/{len(rows)}] Processing {player.full_name} ({team.name})")
        result = generate_player_report(
            player_id=player.id,
            replace=True,
            confirm_save=False,
        )
        if result.get("saved"):
            processed += 1
            print("Player report saved.")
        else:
            failed += 1
            print("Player report failed.")

    print(f"Total players: {len(rows)}")
    print(f"Processed: {processed}")
    print(f"Failed: {failed}")
