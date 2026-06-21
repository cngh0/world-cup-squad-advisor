"""Read back the seeded tournament and source records."""

from __future__ import annotations

from app.database.repository import SquadAdvisorRepository


def main() -> None:
    repo = SquadAdvisorRepository()
    try:
        tournaments = repo.list_tournaments()
        sources = repo.list_data_sources()

        print("Tournaments")
        print("-" * 40)
        for tournament in tournaments:
            print(
                f"{tournament.id} | {tournament.name} | {tournament.year} | "
                f"{tournament.status}"
            )

        print()
        print("Data Sources")
        print("-" * 40)
        for source in sources:
            enabled_flag = "enabled" if source.enabled else "disabled"
            print(
                f"{source.id} | {source.source_type} | {source.coverage_type} | "
                f"{enabled_flag}"
            )
            print(f"  {source.name}")
            print(f"  {source.base_url}")
    finally:
        repo.close()


if __name__ == "__main__":
    main()
