"""Extract one team and its squad rows from the stored Wikipedia raw document."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from app.database.models import Player, SquadMembership, Team
from app.database.repository import SquadAdvisorRepository
from app.domain.ids import (
    build_membership_id,
    build_player_id,
    build_team_id,
    slugify,
)


TOURNAMENT_ID = "fifa-world-cup-2026"
SOURCE_ID = "wikipedia_world_cup_squads"


def clean_text(value: str) -> str:
    return " ".join(value.split())


def parse_birth_date(raw_text: str) -> str | None:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", raw_text)
    if match:
        return match.group(1)
    cleaned = clean_text(raw_text)
    return cleaned or None


def parse_position_group(raw_text: str) -> str | None:
    match = re.search(r"\b(GK|DF|MF|FW)\b", raw_text)
    if match:
        return match.group(1)
    return None


def parse_int(raw_text: str) -> int | None:
    text = clean_text(raw_text)
    if text.isdigit():
        return int(text)
    return None


def parse_player_name(raw_text: str) -> tuple[str, bool]:
    cleaned = clean_text(raw_text)
    is_captain = "( captain )" in cleaned.lower()
    cleaned = re.sub(r"\(\s*captain\s*\)", "", cleaned, flags=re.IGNORECASE)
    return clean_text(cleaned), is_captain


def find_team_heading(soup: BeautifulSoup, team_name: str):
    for heading in soup.find_all("h3"):
        text = clean_text(heading.get_text(" ", strip=True))
        if text == team_name:
            return heading
    return None


def load_wikipedia_raw_document(repo: SquadAdvisorRepository):
    raw_document = repo.get_latest_raw_document_by_source(SOURCE_ID)
    if raw_document is None:
        raise SystemExit(
            "No stored Wikipedia raw document found. Run `crawl-source wikipedia_world_cup_squads` first."
        )
    return raw_document


def build_soup(raw_html: str) -> BeautifulSoup:
    return BeautifulSoup(raw_html, "lxml")


def is_team_squad_table(table) -> bool:
    headers = [clean_text(th.get_text(" ", strip=True)) for th in table.find_all("th")[:7]]
    return headers[:3] == ["No.", "Pos.", "Player"]


def list_extractable_team_names(soup: BeautifulSoup) -> list[str]:
    team_names: list[str] = []
    for heading in soup.find_all("h3"):
        team_name = clean_text(heading.get_text(" ", strip=True))
        group_heading = heading.find_previous("h2")
        group_name = clean_text(group_heading.get_text(" ", strip=True)) if group_heading else ""
        table = heading.find_next("table")
        if not group_name.startswith("Group "):
            continue
        if table is None or not is_team_squad_table(table):
            continue
        team_names.append(team_name)
    return team_names


def extract_team_rows(team_heading) -> tuple[str | None, list[list[str]]]:
    group_heading = team_heading.find_previous("h2")
    group_name = None
    if group_heading is not None:
        group_name = clean_text(group_heading.get_text(" ", strip=True))

    table = team_heading.find_next("table")
    if table is None:
        raise ValueError("No squad table found after team heading")

    rows: list[list[str]] = []
    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 7:
            continue
        values = [clean_text(cell.get_text(" ", strip=True)) for cell in cells[:7]]
        if parse_int(values[0]) is None:
            continue
        if values[2].lower() == "player":
            continue
        rows.append(values)

    if not rows:
        raise ValueError("No player rows found in squad table")

    return group_name, rows


def extract_team_from_soup(
    repo: SquadAdvisorRepository,
    raw_document,
    soup: BeautifulSoup,
    team_name: str,
) -> dict:
    team_heading = find_team_heading(soup, team_name)
    if team_heading is None:
        raise SystemExit(f"Team heading not found: {team_name}")

    group_name, rows = extract_team_rows(team_heading)

    team = Team(
        id=build_team_id(TOURNAMENT_ID, team_name),
        tournament_id=TOURNAMENT_ID,
        name=team_name,
        fifa_code=None,
        group_name=group_name,
        confederation=None,
        coach_name=None,
        official_page_url=raw_document.url,
    )

    existing_team = repo.get_team_by_id(team.id)
    repo.upsert_team(team)

    expected_membership_ids: set[str] = set()
    player_inserted = 0
    player_updated = 0
    membership_inserted = 0
    membership_updated = 0
    deleted_memberships = 0
    deleted_players = 0

    for row in rows:
        shirt_number_text, position_text, player_name, birth_text, caps_text, goals_text, club_name = row
        cleaned_player_name, is_captain = parse_player_name(player_name)

        player = Player(
            id=build_player_id(TOURNAMENT_ID, team_name, cleaned_player_name),
            full_name=cleaned_player_name,
            normalized_name=slugify(cleaned_player_name),
            birth_date=parse_birth_date(birth_text),
            nationality=team_name,
            club_name=club_name or None,
            club_country=None,
            preferred_position=parse_position_group(position_text),
            profile_source_url=raw_document.url,
        )
        existing_player = repo.get_player_by_id(player.id)
        repo.upsert_player(player)
        if existing_player is None:
            player_inserted += 1
        else:
            player_updated += 1

        membership = SquadMembership(
            id=build_membership_id(TOURNAMENT_ID, team_name, cleaned_player_name),
            tournament_id=TOURNAMENT_ID,
            team_id=team.id,
            player_id=player.id,
            source_document_id=raw_document.id,
            shirt_number=parse_int(shirt_number_text),
            position_group=parse_position_group(position_text),
            caps=parse_int(caps_text),
            goals=parse_int(goals_text),
            is_captain=is_captain,
            status="active",
        )
        expected_membership_ids.add(membership.id)
        existing_membership = repo.get_squad_membership_by_id(membership.id)
        repo.upsert_squad_membership(membership)
        if existing_membership is None:
            membership_inserted += 1
        else:
            membership_updated += 1

    current_squad = repo.get_team_squad(team.id)
    for existing_membership, existing_player in current_squad:
        if existing_membership.id in expected_membership_ids:
            continue

        if repo.delete_squad_membership_by_id(existing_membership.id):
            deleted_memberships += 1
            if repo.delete_player_if_unreferenced(existing_player.id):
                deleted_players += 1

    return {
        "team_name": team_name,
        "group_name": group_name,
        "team_action": "updated" if existing_team is not None else "inserted",
        "player_rows": len(rows),
        "players_inserted": player_inserted,
        "players_updated": player_updated,
        "memberships_inserted": membership_inserted,
        "memberships_updated": membership_updated,
        "deleted_memberships": deleted_memberships,
        "deleted_players": deleted_players,
    }


def main(team_name: str) -> None:
    repo = SquadAdvisorRepository()
    try:
        raw_document = load_wikipedia_raw_document(repo)
        soup = build_soup(raw_document.raw_html)
        result = extract_team_from_soup(repo, raw_document, soup, team_name)

        print("Wikipedia team extraction complete")
        print(f"team_name={result['team_name']}")
        print(f"group_name={result['group_name']}")
        print(f"team_action={result['team_action']}")
        print(f"player_rows={result['player_rows']}")
        print(
            f"players inserted={result['players_inserted']} "
            f"updated={result['players_updated']}"
        )
        print(
            f"memberships inserted={result['memberships_inserted']} "
            f"updated={result['memberships_updated']}"
        )
        print(
            f"cleanup deleted_memberships={result['deleted_memberships']} "
            f"deleted_players={result['deleted_players']}"
        )
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py extract-wikipedia-team <team_name>`")
