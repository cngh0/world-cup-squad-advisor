"""CLI entrypoint for the first World Cup squad advisor."""

from __future__ import annotations

from app.services.advisor_service import run_advisor_turn


def main(
    question: str | None = None,
    team_ids: list[str] | None = None,
    session_id: str | None = None,
    preset_id: str | None = None,
) -> None:
    result = run_advisor_turn(
        question=question,
        preset_id=preset_id,
        team_ids=team_ids,
        session_id=session_id,
    )

    if result["preset"] is not None:
        print("Advisor Preset")
        print("-" * 60)
        print(f"id={result['preset']['id']}")
        print(f"label={result['preset']['label']}")
        print()
    print("Advisor Question")
    print("-" * 60)
    print(result["question"])
    print()
    print("Session")
    print("-" * 60)
    print(f"id={result['session']['session_id']}")
    print(f"title={result['session']['title']}")
    print(f"created={result['session']['created']}")
    print(f"message_count={result['session']['message_count']}")
    print()
    print("Scope")
    print("-" * 60)
    print(f"teams={result['context']['team_count']}")
    print(f"players={result['context']['player_count']}")
    print(f"selected_team_ids={', '.join(result['context']['selected_team_ids']) or '-'}")
    print()
    print("Execution")
    print("-" * 60)
    print(f"task_type={result['execution']['route_id']}")
    print(f"task_label={result['execution']['route_label']}")
    print(f"reason={result['execution']['route_reason']}")
    focus_tags = ", ".join(result["execution"]["focus_tags"]) or "-"
    print(f"focus_tags={focus_tags}")
    print("tool_trace:")
    for step in result["execution"]["tool_trace"]:
        print(f"- {step['label']}: {step['detail']}")
    print()

    if not result["generated"]:
        print("Failed to generate advisor answer.")
        return

    answer = result["answer"]
    print("Answer")
    print("-" * 60)
    print(answer["answer"])
    print()
    print("Key Points")
    print("-" * 60)
    for point in answer["key_points"]:
        print(f"- {point}")
    print()
    print("Follow-Ups")
    print("-" * 60)
    for suggestion in answer["follow_up_suggestions"]:
        print(f"- {suggestion}")
    print()
    print(
        "meta: "
        f"prompt={answer['prompt_version']} "
        f"model={answer['model_name']}"
    )
