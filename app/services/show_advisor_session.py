"""CLI readback for one saved advisor session."""

from __future__ import annotations

from app.services.advisor_service import get_advisor_session_detail


def main(session_id: str) -> None:
    session = get_advisor_session_detail(session_id)
    if session is None:
        raise SystemExit(f"Advisor session not found: {session_id}")

    print("Advisor Session")
    print("-" * 60)
    print(f"id={session['session_id']}")
    print(f"title={session['title']}")
    print(f"messages={session['message_count']}")
    print(f"created={session['created_at_label']}")
    print(f"updated={session['updated_at_label']}")
    print(f"teams={', '.join(session['selected_team_ids']) or '-'}")
    print()

    print("Messages")
    print("-" * 60)
    for message in session["messages"]:
        print(f"[{message['created_at_label']}] {message['role']}")
        print(message["content"])
        if message["task_label"]:
            print(f"task={message['task_label']} ({message['task_type'] or '-'})")
        if message["tool_trace"]:
            print("tool_trace:")
            for step in message["tool_trace"]:
                print(f"- {step}")
        if message["role"] == "assistant" and message["generated"]:
            if message["key_points"]:
                print("key_points:")
                for point in message["key_points"]:
                    print(f"- {point}")
            if message["follow_up_suggestions"]:
                print("follow_ups:")
                for item in message["follow_up_suggestions"]:
                    print(f"- {item}")
            print(
                f"meta: scope={message['scope_team_count'] or 0} teams / "
                f"{message['scope_player_count'] or 0} players "
                f"model={message['model_name'] or '-'}"
            )
        print("-" * 60)


if __name__ == "__main__":
    raise SystemExit("Use: uv run python main.py show-advisor-session <session_id>")
