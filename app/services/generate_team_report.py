"""Generate one AI-enriched report for a normalized team."""

from __future__ import annotations

import sys

from app.agent.team_report_agent import TeamReportAgent, TeamReportOutput
from app.database.models import TeamReport
from app.database.repository import SquadAdvisorRepository
from app.domain.ids import build_team_id
from app.services.team_queries import get_team_overview_data


TOURNAMENT_ID = "fifa-world-cup-2026"


def _safe_preview(text: str | None, limit: int = 500) -> str:
    preview = (text or "")[:limit]
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return preview.encode(encoding, errors="replace").decode(encoding)


def _ask_yes_no(prompt: str) -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def _save_team_report(
    repo: SquadAdvisorRepository,
    team_id: str,
    report_result: TeamReportOutput,
    agent: TeamReportAgent,
    source_document_id: str | None,
    had_existing: bool,
) -> tuple[bool, str]:
    if not had_existing:
        created = repo.create_team_report(
            TeamReport(
                team_id=team_id,
                source_document_id=source_document_id,
                summary=report_result.summary,
                style_of_play=report_result.style_of_play,
                strengths=report_result.strengths,
                risks=report_result.risks,
                watch_players=report_result.watch_players,
                evidence_note=report_result.evidence_note,
                prompt_version=agent.prompt_version,
                model_name=agent.model,
            )
        )
        return created is not None, "create"

    saved = repo.update_team_report(
        team_id=team_id,
        source_document_id=source_document_id,
        summary=report_result.summary,
        style_of_play=report_result.style_of_play,
        strengths=report_result.strengths,
        risks=report_result.risks,
        watch_players=report_result.watch_players,
        evidence_note=report_result.evidence_note,
        prompt_version=agent.prompt_version,
        model_name=agent.model,
    )
    return saved, "replace"


def generate_team_report(
    team_name: str,
    replace: bool = False,
    confirm_save: bool = False,
) -> dict:
    repo = SquadAdvisorRepository()
    agent = TeamReportAgent()

    try:
        team_id = build_team_id(TOURNAMENT_ID, team_name)
        team = repo.get_team_by_id(team_id)
        if team is None:
            print(f"Team not found: {team_name}")
            return {"found": False, "generated": False, "saved": False}

        existing = repo.get_team_report(team_id)
        overview = get_team_overview_data(team_id=team_id, repo=repo)

        print(f"Processing team: {overview['team_name']}")
        print(f"group: {overview['group_name']}")
        print(f"squad_size: {overview['squad_size']}")
        print(f"total_caps: {overview['total_caps']}")
        print(f"total_goals: {overview['total_goals']}")
        print("-" * 60)

        if existing is not None:
            print("Existing team report")
            print(f"summary: {_safe_preview(existing.summary, 300)}")
            print(
                "meta: "
                f"prompt={existing.prompt_version} "
                f"model={existing.model_name}"
            )
            print("-" * 60)
        else:
            print("Existing team report: none")
            print("-" * 60)

        result = agent.generate_team_report(overview)
        if result is None:
            print("Failed to generate team report")
            return {
                "found": True,
                "generated": False,
                "saved": False,
                "had_existing": existing is not None,
            }

        print("Generated candidate team report")
        print(f"summary: {_safe_preview(result.summary, 400)}")
        print(f"style_of_play: {_safe_preview(result.style_of_play, 240)}")
        print(f"strengths: {_safe_preview(result.strengths, 300)}")
        print(f"risks: {_safe_preview(result.risks, 300)}")
        print(f"watch_players: {_safe_preview(result.watch_players, 260)}")
        print("-" * 60)

        saved = False
        action = "preview"
        if replace:
            saved, action = _save_team_report(
                repo=repo,
                team_id=team_id,
                report_result=result,
                agent=agent,
                source_document_id=overview.get("source_document_id"),
                had_existing=existing is not None,
            )
        elif confirm_save:
            target = "create" if existing is None else "replace"
            if _ask_yes_no(f"Save this generated team report now? [{target}] [y/N]: "):
                saved, action = _save_team_report(
                    repo=repo,
                    team_id=team_id,
                    report_result=result,
                    agent=agent,
                    source_document_id=overview.get("source_document_id"),
                    had_existing=existing is not None,
                )
            else:
                print("Save skipped. Existing team report was left unchanged.")
        else:
            print("Preview only. Existing team report was left unchanged.")
            print("Tip: use --confirm-save to save this same generated result now.")

        if saved:
            if action == "create":
                print("Saved new team report.")
            elif action == "replace":
                print("Replaced existing team report.")
        elif action in {"create", "replace"}:
            if action == "create":
                print("Failed to save new team report.")
            else:
                print("Failed to replace existing team report.")

        return {
            "found": True,
            "generated": True,
            "saved": saved,
            "had_existing": existing is not None,
            "replaced": action == "replace" and saved,
        }
    finally:
        repo.close()


def main(team_name: str, replace: bool = False, confirm_save: bool = False) -> None:
    result = generate_team_report(
        team_name=team_name,
        replace=replace,
        confirm_save=confirm_save,
    )
    print(f"found={result['found']}")
    print(f"generated={result['generated']}")
    print(f"saved={result['saved']}")


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py generate-team-report <team_name>`")
