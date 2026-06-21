"""Server-rendered routes for the World Cup Squad Advisor web layer."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.web.viewmodels import (
    build_advisor_page_data,
    build_compare_page_data,
    build_dashboard_page_data,
    build_player_detail_page_data,
    build_players_page_data,
    build_team_detail_page_data,
    build_teams_page_data,
)


router = APIRouter()
WEB_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


@router.get("/")
def dashboard_page(request: Request):
    context = build_dashboard_page_data()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=context,
    )


@router.get("/teams")
def teams_page(request: Request, group: str | None = None):
    context = build_teams_page_data(group=group)
    return templates.TemplateResponse(
        request=request,
        name="teams.html",
        context=context,
    )


@router.get("/teams/{team_id}")
def team_detail_page(request: Request, team_id: str):
    context = build_team_detail_page_data(team_id=team_id)
    return templates.TemplateResponse(
        request=request,
        name="team_detail.html",
        context=context,
    )


@router.get("/players")
def players_page(
    request: Request,
    q: str | None = None,
    team_id: str | None = None,
    position_group: str | None = None,
):
    context = build_players_page_data(
        q=q,
        team_id=team_id,
        position_group=position_group,
    )
    return templates.TemplateResponse(
        request=request,
        name="players.html",
        context=context,
    )


@router.get("/players/{player_id}")
def player_detail_page(request: Request, player_id: str):
    context = build_player_detail_page_data(player_id=player_id)
    return templates.TemplateResponse(
        request=request,
        name="player_detail.html",
        context=context,
    )


@router.get("/compare")
def compare_page(
    request: Request,
    left_team_id: str | None = None,
    right_team_id: str | None = None,
):
    context = build_compare_page_data(
        left_team_id=left_team_id,
        right_team_id=right_team_id,
    )
    return templates.TemplateResponse(
        request=request,
        name="compare.html",
        context=context,
    )


@router.get("/advisor")
def advisor_page(
    request: Request,
    session_id: str | None = Query(default=None),
):
    context = build_advisor_page_data(
        session_id=session_id,
    )
    return templates.TemplateResponse(
        request=request,
        name="advisor.html",
        context=context,
    )


@router.post("/advisor")
def advisor_submit_page(
    session_id: str | None = Form(default=None),
    question: str = Form(default=""),
    preset_id: str | None = Form(default=None),
    team_id: list[str] | None = Form(default=None),
):
    from app.services.advisor_service import run_advisor_turn

    cleaned_question = question.strip()
    if not cleaned_question and not preset_id:
        redirect_target = "/advisor"
        if session_id:
            redirect_target = f"/advisor?session_id={quote(session_id)}"
        return RedirectResponse(url=redirect_target, status_code=303)

    result = run_advisor_turn(
        question=cleaned_question or None,
        preset_id=preset_id,
        team_ids=team_id or None,
        session_id=session_id or None,
    )
    redirect_session_id = quote(result["session"]["session_id"])
    return RedirectResponse(url=f"/advisor?session_id={redirect_session_id}", status_code=303)
