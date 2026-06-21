"""Generate one AI-enriched report for a normalized player."""

from __future__ import annotations

import sys

from app.agent.player_report_agent import PlayerReportAgent, PlayerReportOutput
from app.database.models import PlayerReport
from app.database.repository import SquadAdvisorRepository
from app.services.player_queries import get_player_profile_data


def _safe_preview(text: str | None, limit: int = 500) -> str:
    preview = (text or "")[:limit]
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return preview.encode(encoding, errors="replace").decode(encoding)


def _ask_yes_no(prompt: str) -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def _save_player_report(
    repo: SquadAdvisorRepository,
    player_id: str,
    report_result: PlayerReportOutput,
    agent: PlayerReportAgent,
    source_document_id: str | None,
    had_existing: bool,
) -> tuple[bool, str]:
    if not had_existing:
        created = repo.create_player_report(
            PlayerReport(
                player_id=player_id,
                source_document_id=source_document_id,
                summary=report_result.summary,
                strengths=report_result.strengths,
                concerns=report_result.concerns,
                role_tags=report_result.role_tags,
                evidence_note=report_result.evidence_note,
                prompt_version=agent.prompt_version,
                model_name=agent.model,
            )
        )
        return created is not None, "create"

    saved = repo.update_player_report(
        player_id=player_id,
        source_document_id=source_document_id,
        summary=report_result.summary,
        strengths=report_result.strengths,
        concerns=report_result.concerns,
        role_tags=report_result.role_tags,
        evidence_note=report_result.evidence_note,
        prompt_version=agent.prompt_version,
        model_name=agent.model,
    )
    return saved, "replace"


def generate_player_report(
    player_id: str,
    replace: bool = False,
    confirm_save: bool = False,
) -> dict:
    repo = SquadAdvisorRepository()
    agent = PlayerReportAgent()

    try:
        row = repo.get_player_context(player_id)
        if row is None:
            print(f"Player not found: {player_id}")
            return {"found": False, "generated": False, "saved": False}

        existing = repo.get_player_report(player_id)
        profile = get_player_profile_data(player_id=player_id, repo=repo)

        print(f"Processing player: {profile['full_name']}")
        print(f"team: {profile['team_name']}")
        print(f"position: {profile['position_group']}")
        print(f"caps: {profile['caps']}")
        print(f"goals: {profile['goals']}")
        print("-" * 60)

        if existing is not None:
            print("Existing player report")
            print(f"summary: {_safe_preview(existing.summary, 300)}")
            print(
                "meta: "
                f"prompt={existing.prompt_version} "
                f"model={existing.model_name}"
            )
            print("-" * 60)
        else:
            print("Existing player report: none")
            print("-" * 60)

        result = agent.generate_player_report(profile)
        if result is None:
            print("Failed to generate player report")
            return {
                "found": True,
                "generated": False,
                "saved": False,
                "had_existing": existing is not None,
            }

        print("Generated candidate player report")
        print(f"summary: {_safe_preview(result.summary, 360)}")
        print(f"strengths: {_safe_preview(result.strengths, 320)}")
        print(f"concerns: {_safe_preview(result.concerns, 240)}")
        print(f"role_tags: {_safe_preview(result.role_tags, 160)}")
        print("-" * 60)

        saved = False
        action = "preview"
        if replace:
            saved, action = _save_player_report(
                repo=repo,
                player_id=player_id,
                report_result=result,
                agent=agent,
                source_document_id=profile.get("source_document_id"),
                had_existing=existing is not None,
            )
        elif confirm_save:
            target = "create" if existing is None else "replace"
            if _ask_yes_no(f"Save this generated player report now? [{target}] [y/N]: "):
                saved, action = _save_player_report(
                    repo=repo,
                    player_id=player_id,
                    report_result=result,
                    agent=agent,
                    source_document_id=profile.get("source_document_id"),
                    had_existing=existing is not None,
                )
            else:
                print("Save skipped. Existing player report was left unchanged.")
        else:
            print("Preview only. Existing player report was left unchanged.")
            print("Tip: use --confirm-save to save this same generated result now.")

        if saved:
            if action == "create":
                print("Saved new player report.")
            elif action == "replace":
                print("Replaced existing player report.")
        elif action in {"create", "replace"}:
            if action == "create":
                print("Failed to save new player report.")
            else:
                print("Failed to replace existing player report.")

        return {
            "found": True,
            "generated": True,
            "saved": saved,
            "had_existing": existing is not None,
            "replaced": action == "replace" and saved,
        }
    finally:
        repo.close()


def main(player_id: str, replace: bool = False, confirm_save: bool = False) -> None:
    result = generate_player_report(
        player_id=player_id,
        replace=replace,
        confirm_save=confirm_save,
    )
    print(f"found={result['found']}")
    print(f"generated={result['generated']}")
    print(f"saved={result['saved']}")


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py generate-player-report <player_id>`")
