"""CLI readback for saved advisor sessions."""

from __future__ import annotations

from app.services.advisor_service import list_advisor_session_summaries


def main(limit: int = 10) -> None:
    sessions = list_advisor_session_summaries(limit=limit)

    print(f"Found {len(sessions)} advisor sessions")
    print("-" * 60)
    for session in sessions:
        print(session["session_id"])
        print(session["title"])
        print(
            f"messages={session['message_count']} "
            f"updated={session['updated_at_label']}"
        )
        selected = ", ".join(session["selected_team_ids"]) or "-"
        print(f"teams={selected}")
        print("-" * 60)


if __name__ == "__main__":
    main()
