"""Seed the first tournament and source records."""

from __future__ import annotations

from app.database.models import DataSource, Tournament
from app.database.repository import SquadAdvisorRepository
from app.services.source_config import list_source_configs


def main() -> None:
    repo = SquadAdvisorRepository()
    tournament_inserted = 0
    tournament_updated = 0
    source_inserted = 0
    source_updated = 0

    try:
        tournament = Tournament(
            id="fifa-world-cup-2026",
            name="FIFA World Cup 2026",
            year=2026,
            host="Canada / Mexico / United States",
            status="upcoming",
        )
        existing_tournament = repo.get_tournament_by_id(tournament.id)
        repo.upsert_tournament(tournament)
        if existing_tournament is None:
            tournament_inserted += 1
        else:
            tournament_updated += 1

        for source_data in list_source_configs():
            source = DataSource(
                id=source_data["id"],
                name=source_data["name"],
                base_url=source_data["base_url"],
                source_type=source_data["source_type"],
                coverage_type=source_data["coverage_type"],
                reliability_level=source_data["reliability_level"],
                enabled=source_data["enabled"],
            )
            existing_source = repo.get_data_source_by_id(source.id)
            repo.upsert_data_source(source)
            if existing_source is None:
                source_inserted += 1
            else:
                source_updated += 1

        print("Seed reference data complete")
        print(f"tournaments inserted={tournament_inserted} updated={tournament_updated}")
        print(f"sources inserted={source_inserted} updated={source_updated}")
    finally:
        repo.close()


if __name__ == "__main__":
    main()
