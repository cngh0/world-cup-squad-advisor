from __future__ import annotations

import sys

from app.database.create_tables import main as create_tables_main
from app.services.ask_advisor import main as ask_advisor_main
from app.services.compare_teams import main as compare_teams_main
from app.services.crawl_source_once import main as crawl_source_once_main
from app.services.extract_wikipedia_all_teams import main as extract_wikipedia_all_teams_main
from app.services.extract_wikipedia_team import main as extract_wikipedia_team_main
from app.services.generate_player_report import main as generate_player_report_main
from app.services.generate_player_reports import main as generate_player_reports_main
from app.services.generate_team_report import main as generate_team_report_main
from app.services.generate_team_reports import main as generate_team_reports_main
from app.services.seed_reference_data import main as seed_reference_data_main
from app.services.show_advisor_session import main as show_advisor_session_main
from app.services.show_advisor_presets import main as show_advisor_presets_main
from app.services.show_advisor_sessions import main as show_advisor_sessions_main
from app.services.show_raw_documents import main as show_raw_documents_main
from app.services.show_recent_player_reports import main as show_recent_player_reports_main
from app.services.show_recent_team_reports import main as show_recent_team_reports_main
from app.services.show_reference_data import main as show_reference_data_main
from app.services.show_team_overview import main as show_team_overview_main
from app.services.show_team_squad import main as show_team_squad_main


def configure_stdout() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def print_usage() -> None:
    print("Commands:")
    print("  create-tables")
    print("  seed-reference-data")
    print("  show-reference-data")
    print("  crawl-source <source_id>")
    print("  show-raw-documents [limit]")
    print('  extract-wikipedia-team "<team_name>"')
    print("  extract-wikipedia-all-teams [limit]")
    print('  show-team-overview "<team_name>"')
    print('  show-team-squad "<team_name>"')
    print('  compare-teams "<team_a>" "<team_b>"')
    print('  ask-advisor "<question>" [team_id ...] [--session <session_id>]')
    print("  run-advisor-preset <preset_id> [team_id ...] [--session <session_id>]")
    print("  show-advisor-presets")
    print("  show-advisor-sessions [limit]")
    print("  show-advisor-session <session_id>")
    print('  generate-player-report "<player_id>" [--replace] [--confirm-save]')
    print("  generate-player-reports [limit] [--replace-existing]")
    print("  show-recent-player-reports [limit]")
    print('  generate-team-report "<team_name>" [--replace] [--confirm-save]')
    print("  generate-team-reports [limit] [--replace-existing]")
    print("  show-recent-team-reports [limit]")


def main() -> None:
    configure_stdout()

    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    if command == "create-tables":
        create_tables_main()
        return

    if command == "seed-reference-data":
        seed_reference_data_main()
        return

    if command == "show-reference-data":
        show_reference_data_main()
        return

    if command == "crawl-source":
        if len(sys.argv) < 3:
            print("Usage: crawl-source <source_id>")
            return
        crawl_source_once_main(sys.argv[2])
        return

    if command == "show-raw-documents":
        limit = 5
        if len(sys.argv) >= 3:
            limit = int(sys.argv[2])
        show_raw_documents_main(limit=limit)
        return

    if command == "extract-wikipedia-team":
        if len(sys.argv) < 3:
            print('Usage: extract-wikipedia-team "<team_name>"')
            return
        team_name = " ".join(sys.argv[2:])
        extract_wikipedia_team_main(team_name)
        return

    if command == "extract-wikipedia-all-teams":
        limit = None
        if len(sys.argv) >= 3:
            limit = int(sys.argv[2])
        extract_wikipedia_all_teams_main(limit=limit)
        return

    if command == "show-team-squad":
        if len(sys.argv) < 3:
            print('Usage: show-team-squad "<team_name>"')
            return
        team_name = " ".join(sys.argv[2:])
        show_team_squad_main(team_name)
        return

    if command == "show-team-overview":
        if len(sys.argv) < 3:
            print('Usage: show-team-overview "<team_name>"')
            return
        team_name = " ".join(sys.argv[2:])
        show_team_overview_main(team_name)
        return

    if command == "compare-teams":
        if len(sys.argv) < 4:
            print('Usage: compare-teams "<team_a>" "<team_b>"')
            return
        compare_teams_main(sys.argv[2], sys.argv[3])
        return

    if command == "ask-advisor":
        if len(sys.argv) < 3:
            print('Usage: ask-advisor "<question>" [team_id ...] [--session <session_id>]')
            return
        question = sys.argv[2]
        args = sys.argv[3:]
        session_id = None
        team_ids = []
        index = 0
        while index < len(args):
            arg = args[index]
            if arg == "--session":
                if index + 1 >= len(args):
                    print('Usage: ask-advisor "<question>" [team_id ...] [--session <session_id>]')
                    return
                session_id = args[index + 1]
                index += 2
                continue
            team_ids.append(arg)
            index += 1
        ask_advisor_main(
            question=question,
            team_ids=team_ids or None,
            session_id=session_id,
        )
        return

    if command == "run-advisor-preset":
        if len(sys.argv) < 3:
            print("Usage: run-advisor-preset <preset_id> [team_id ...] [--session <session_id>]")
            return
        preset_id = sys.argv[2]
        args = sys.argv[3:]
        session_id = None
        team_ids = []
        index = 0
        while index < len(args):
            arg = args[index]
            if arg == "--session":
                if index + 1 >= len(args):
                    print("Usage: run-advisor-preset <preset_id> [team_id ...] [--session <session_id>]")
                    return
                session_id = args[index + 1]
                index += 2
                continue
            team_ids.append(arg)
            index += 1
        ask_advisor_main(
            question=None,
            team_ids=team_ids or None,
            session_id=session_id,
            preset_id=preset_id,
        )
        return

    if command == "show-advisor-presets":
        show_advisor_presets_main()
        return

    if command == "show-advisor-sessions":
        limit = 10
        if len(sys.argv) >= 3:
            limit = int(sys.argv[2])
        show_advisor_sessions_main(limit=limit)
        return

    if command == "show-advisor-session":
        if len(sys.argv) < 3:
            print("Usage: show-advisor-session <session_id>")
            return
        show_advisor_session_main(sys.argv[2])
        return

    if command == "generate-player-report":
        if len(sys.argv) < 3:
            print('Usage: generate-player-report "<player_id>" [--replace] [--confirm-save]')
            return
        args = sys.argv[2:]
        replace = "--replace" in args
        confirm_save = "--confirm-save" in args
        player_id_parts = [arg for arg in args if arg not in {"--replace", "--confirm-save"}]
        if not player_id_parts:
            print('Usage: generate-player-report "<player_id>" [--replace] [--confirm-save]')
            return
        player_id = " ".join(player_id_parts)
        generate_player_report_main(
            player_id=player_id,
            replace=replace,
            confirm_save=confirm_save,
        )
        return

    if command == "generate-player-reports":
        limit = 5
        replace_existing = "--replace-existing" in sys.argv[2:]
        for arg in sys.argv[2:]:
            if arg.startswith("--"):
                continue
            limit = int(arg)
            break
        generate_player_reports_main(limit=limit, replace_existing=replace_existing)
        return

    if command == "show-recent-player-reports":
        limit = 5
        if len(sys.argv) >= 3:
            limit = int(sys.argv[2])
        show_recent_player_reports_main(limit=limit)
        return

    if command == "generate-team-report":
        if len(sys.argv) < 3:
            print('Usage: generate-team-report "<team_name>" [--replace] [--confirm-save]')
            return
        args = sys.argv[2:]
        replace = "--replace" in args
        confirm_save = "--confirm-save" in args
        team_name_parts = [arg for arg in args if arg not in {"--replace", "--confirm-save"}]
        if not team_name_parts:
            print('Usage: generate-team-report "<team_name>" [--replace] [--confirm-save]')
            return
        team_name = " ".join(team_name_parts)
        generate_team_report_main(
            team_name=team_name,
            replace=replace,
            confirm_save=confirm_save,
        )
        return

    if command == "generate-team-reports":
        limit = 5
        replace_existing = "--replace-existing" in sys.argv[2:]
        for arg in sys.argv[2:]:
            if arg.startswith("--"):
                continue
            limit = int(arg)
            break
        generate_team_reports_main(limit=limit, replace_existing=replace_existing)
        return

    if command == "show-recent-team-reports":
        limit = 5
        if len(sys.argv) >= 3:
            limit = int(sys.argv[2])
        show_recent_team_reports_main(limit=limit)
        return

    print(f"Unknown command: {command}")
    print()
    print_usage()


if __name__ == "__main__":
    main()
