"""LLM-backed advisor for answering World Cup squad questions from stored data."""

from __future__ import annotations

import json
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()


class AdvisorAnswerOutput(BaseModel):
    answer: str
    key_points: list[str]
    cited_team_ids: list[str]
    cited_player_ids: list[str]
    follow_up_suggestions: list[str]


PROMPT_VERSION = "v2-world-cup-task-routed-advisor"


SYSTEM_PROMPT = """You are a World Cup squad advisor inside a football intelligence workbench.

Your job is to answer the user's question using only the provided workbench outputs.

Rules:
- Use only the provided tool outputs and scoped workbench context. Do not invent facts, injuries, tactics, or form data.
- If the context is insufficient, say that clearly and explain what is missing.
- Prefer direct, decision-oriented answers over generic summaries.
- Follow the routed task type when shaping the answer.
- When comparing teams or players, ground the comparison in the supplied caps, goals, positions, and saved reports.

Output rules:
- answer: 2 to 4 concise paragraphs
- key_points: 3 to 6 short bullet-like points
- cited_team_ids: include only team ids that are clearly relevant from the provided context
- cited_player_ids: include only player ids that are clearly relevant from the provided context
- follow_up_suggestions: 2 to 4 concrete next questions the user could ask
"""


class AdvisorAgent:
    """Generate a structured advisor answer from scoped stored context."""

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

    def answer(
        self,
        question: str,
        agent_context: dict,
        conversation_history: list[dict] | None = None,
    ) -> Optional[AdvisorAnswerOutput]:
        history_block = ""
        if conversation_history:
            history_block = (
                "Recent conversation history:\n"
                f"{json.dumps(conversation_history, ensure_ascii=False, indent=2)[:5000]}\n\n"
            )

        user_prompt = (
            "Answer the user's World Cup squad question from the following routed workbench context.\n\n"
            f"{history_block}"
            f"Question:\n{question}\n\n"
            "Routed workbench context:\n"
            f"{json.dumps(agent_context, ensure_ascii=False, indent=2)[:18000]}"
        )

        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=self.system_prompt,
                temperature=0.2,
                input=user_prompt,
                text_format=AdvisorAnswerOutput,
            )
            if response.output_parsed is not None:
                return response.output_parsed

            fallback_response = self.client.responses.create(
                model=self.model,
                instructions=(
                    f"{self.system_prompt}\n\n"
                    "Return valid JSON only. Use this exact shape: "
                    '{"answer":"...","key_points":["..."],"cited_team_ids":["..."],'
                    '"cited_player_ids":["..."],"follow_up_suggestions":["..."]}'
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
            return AdvisorAnswerOutput(**parsed)
        except Exception as exc:
            print(f"Error generating advisor answer: {exc}")
            return None
