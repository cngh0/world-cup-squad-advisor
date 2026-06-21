"""Batch extract all team sections from the stored Wikipedia squads page."""

from __future__ import annotations

from app.database.repository import SquadAdvisorRepository
from app.services.extract_wikipedia_team import (
    build_soup,
    extract_team_from_soup,
    list_extractable_team_names,
    load_wikipedia_raw_document,
)


def main(limit: int | None = None) -> None:
    repo = SquadAdvisorRepository()
    try:
        raw_document = load_wikipedia_raw_document(repo)
        soup = build_soup(raw_document.raw_html)
        team_names = list_extractable_team_names(soup)
        if limit is not None:
            team_names = team_names[:limit]

        total = len(team_names)
        failures: list[tuple[str, str]] = []
        success_count = 0
        total_players_inserted = 0
        total_players_updated = 0
        total_memberships_inserted = 0
        total_memberships_updated = 0
        total_deleted_memberships = 0
        total_deleted_players = 0

        for index, team_name in enumerate(team_names, start=1):
            try:
                result = extract_team_from_soup(repo, raw_document, soup, team_name)
                success_count += 1
                total_players_inserted += result["players_inserted"]
                total_players_updated += result["players_updated"]
                total_memberships_inserted += result["memberships_inserted"]
                total_memberships_updated += result["memberships_updated"]
                total_deleted_memberships += result["deleted_memberships"]
                total_deleted_players += result["deleted_players"]
                print(
                    f"[{index}/{total}] {team_name} | "
                    f"team={result['team_action']} | "
                    f"players={result['player_rows']}"
                )
            except Exception as exc:
                failures.append((team_name, str(exc)))
                print(f"[{index}/{total}] {team_name} | failed | {exc}")

        print()
        print("Wikipedia batch extraction summary")
        print(f"teams_targeted={total}")
        print(f"teams_succeeded={success_count}")
        print(f"teams_failed={len(failures)}")
        print(f"players_inserted={total_players_inserted}")
        print(f"players_updated={total_players_updated}")
        print(f"memberships_inserted={total_memberships_inserted}")
        print(f"memberships_updated={total_memberships_updated}")
        print(f"cleanup_deleted_memberships={total_deleted_memberships}")
        print(f"cleanup_deleted_players={total_deleted_players}")

        if failures:
            print()
            print("Failures")
            for team_name, error in failures:
                print(f"- {team_name}: {error}")
            raise SystemExit(1)
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py extract-wikipedia-all-teams [limit]`")
