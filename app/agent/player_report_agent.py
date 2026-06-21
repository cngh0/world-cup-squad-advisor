"""Generate structured scouting-style reports for one player."""

from __future__ import annotations

import json
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()


class PlayerReportOutput(BaseModel):
    summary: str
    strengths: str
    concerns: str
    role_tags: str
    evidence_note: str


PROMPT_VERSION = "v1-player-report-from-normalized-squad"


SYSTEM_PROMPT = """You are a football analyst writing concise player notes for a World Cup squad workbench.

You are given normalized data for one player and a small amount of team context.
Write a careful player report based only on that provided data.

Output rules:
- summary: exactly 2 sentences
- strengths: 2-3 sentences describing what stands out positively from the player's role, production, experience, or context
- concerns: 1-2 sentences describing uncertainty, limited experience, role risk, or lack of evidence
- role_tags: 3 to 5 short comma-separated tags such as veteran defender, primary scorer, wide attacker, low-experience backup
- evidence_note: 1 sentence saying this report was inferred from normalized squad data and the stored source page

Constraints:
- Do not invent club form, injuries, personality, or detailed style claims not supported by the data
- Use concrete facts from caps, goals, position group, team context, and relative ranking when available
- If the data is thin, say so directly
- Write like a neutral analyst, not a fan post
"""


class PlayerReportAgent:
    """LLM wrapper for one structured player report."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.prompt_version = PROMPT_VERSION
        self.system_prompt = SYSTEM_PROMPT

    def generate_player_report(
        self,
        profile: dict,
    ) -> Optional[PlayerReportOutput]:
        user_prompt = (
            "Create a World Cup player report from the following normalized player data.\n"
            "Return a direct player report, not commentary about the data source.\n\n"
            f"{json.dumps(profile, ensure_ascii=False, indent=2)[:14000]}"
        )

        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=self.system_prompt,
                temperature=0.2,
                input=user_prompt,
                text_format=PlayerReportOutput,
            )
            if response.output_parsed is not None:
                return response.output_parsed

            fallback_response = self.client.responses.create(
                model=self.model,
                instructions=(
                    f"{self.system_prompt}\n\n"
                    "Return valid JSON only. Use this exact shape: "
                    '{"summary":"...","strengths":"...","concerns":"...",'
                    '"role_tags":"...","evidence_note":"..."}'
                ),
                temperature=0.2,
                input=user_prompt,
            )

            raw_text = getattr(fallback_response, "output_text", "") or ""
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()

            parsed = json.loads(cleaned)
            return PlayerReportOutput(**parsed)
        except Exception as exc:
            print(f"Error generating player report: {exc}")
            return None
