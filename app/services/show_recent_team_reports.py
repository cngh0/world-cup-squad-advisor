"""Read back recently generated team reports."""

from __future__ import annotations

import sys

from app.database.repository import SquadAdvisorRepository


def _safe_preview(text: str | None, limit: int = 260) -> str:
    preview = (text or "")[:limit]
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return preview.encode(encoding, errors="replace").decode(encoding)


def main(limit: int = 5) -> None:
    repo = SquadAdvisorRepository()
    try:
        rows = repo.get_recent_team_reports(limit=limit)
        print(f"Found {len(rows)} team reports")
        for report, team in rows:
            print("-" * 60)
            print(team.id)
            print(team.name)
            print(f"summary: {_safe_preview(report.summary)}")
            print(f"style_of_play: {_safe_preview(report.style_of_play, 180)}")
            print(
                "meta: "
                f"prompt={report.prompt_version} "
                f"model={report.model_name}"
            )
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py show-recent-team-reports`")
