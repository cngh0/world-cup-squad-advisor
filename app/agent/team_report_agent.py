"""Generate structured scouting-style reports for one team."""

from __future__ import annotations

import json
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()


class TeamReportOutput(BaseModel):
    summary: str
    style_of_play: str
    strengths: str
    risks: str
    watch_players: str
    evidence_note: str


PROMPT_VERSION = "v1-team-report-from-normalized-squad"


SYSTEM_PROMPT = """You are a football squad analyst writing concise team reports.

You are given normalized squad data for one World Cup team.
Write an explainable report based only on the provided data.

Output rules:
- summary: exactly 2 sentences
- style_of_play: 1-2 sentences, but stay conservative if the data is not rich enough to prove a detailed tactical identity
- strengths: 2-3 sentences about the squad's strongest visible qualities from the provided data
- risks: 2-3 sentences about the squad's visible weaknesses, thin areas, or uncertainty
- watch_players: mention 3 to 5 players by name and explain why they stand out in this squad
- evidence_note: 1 sentence saying this report was inferred from normalized squad data and the stored source page

Constraints:
- Do not invent club form, injuries, or tactical systems that are not supported by the data
- Use concrete facts from the supplied caps, goals, positions, and player names
- If the data is limited, say so directly instead of pretending certainty
- Write like a neutral analyst, not a hype post
"""


class TeamReportAgent:
    """LLM wrapper for one structured team report."""

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

    def generate_team_report(
        self,
        overview: dict,
    ) -> Optional[TeamReportOutput]:
        user_prompt = (
            "Create a World Cup team report from the following normalized squad data.\n"
            "Return a direct team report, not commentary about the data source.\n\n"
            f"{json.dumps(overview, ensure_ascii=False, indent=2)[:14000]}"
        )

        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=self.system_prompt,
                temperature=0.2,
                input=user_prompt,
                text_format=TeamReportOutput,
            )
            if response.output_parsed is not None:
                return response.output_parsed

            fallback_response = self.client.responses.create(
                model=self.model,
                instructions=(
                    f"{self.system_prompt}\n\n"
                    "Return valid JSON only. Use this exact shape: "
                    '{"summary":"...","style_of_play":"...","strengths":"...",'
                    '"risks":"...","watch_players":"...","evidence_note":"..."}'
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
            return TeamReportOutput(**parsed)
        except Exception as exc:
            print(f"Error generating team report: {exc}")
            return None
