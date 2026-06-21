"""SQLAlchemy models for the Phase 1 schema."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


def utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    coverage_type = Column(String, nullable=False)
    reliability_level = Column(String, nullable=False, default="medium")
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    target_key = Column(String, nullable=True)
    status = Column(String, nullable=False, default="started")
    fetched_count = Column(Integer, nullable=False, default=0)
    saved_count = Column(Integer, nullable=False, default=0)
    error_summary = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)


class RawDocument(Base):
    __tablename__ = "raw_documents"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_raw_documents_source_external"),
    )

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    crawl_run_id = Column(String, ForeignKey("crawl_runs.id"), nullable=True)
    external_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    title = Column(String, nullable=True)
    raw_html = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    content_hash = Column(String, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    host = Column(String, nullable=False)
    status = Column(String, nullable=False)


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("tournament_id", "name", name="uq_teams_tournament_name"),
    )

    id = Column(String, primary_key=True)
    tournament_id = Column(String, ForeignKey("tournaments.id"), nullable=False)
    name = Column(String, nullable=False)
    fifa_code = Column(String, nullable=True)
    group_name = Column(String, nullable=True)
    confederation = Column(String, nullable=True)
    coach_name = Column(String, nullable=True)
    official_page_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class Player(Base):
    __tablename__ = "players"

    id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False)
    birth_date = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    club_name = Column(String, nullable=True)
    club_country = Column(String, nullable=True)
    preferred_position = Column(String, nullable=True)
    profile_source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class SquadMembership(Base):
    __tablename__ = "squad_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "team_id",
            "player_id",
            name="uq_squad_memberships_tournament_team_player",
        ),
    )

    id = Column(String, primary_key=True)
    tournament_id = Column(String, ForeignKey("tournaments.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    source_document_id = Column(String, ForeignKey("raw_documents.id"), nullable=True)
    shirt_number = Column(Integer, nullable=True)
    position_group = Column(String, nullable=True)
    caps = Column(Integer, nullable=True)
    goals = Column(Integer, nullable=True)
    is_captain = Column(Boolean, nullable=False, default=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class PlayerReport(Base):
    __tablename__ = "player_reports"

    player_id = Column(String, ForeignKey("players.id"), primary_key=True)
    source_document_id = Column(String, ForeignKey("raw_documents.id"), nullable=True)
    summary = Column(Text, nullable=False)
    strengths = Column(Text, nullable=True)
    concerns = Column(Text, nullable=True)
    role_tags = Column(Text, nullable=True)
    evidence_note = Column(Text, nullable=True)
    prompt_version = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class TeamReport(Base):
    __tablename__ = "team_reports"

    team_id = Column(String, ForeignKey("teams.id"), primary_key=True)
    source_document_id = Column(String, ForeignKey("raw_documents.id"), nullable=True)
    summary = Column(Text, nullable=False)
    style_of_play = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    risks = Column(Text, nullable=True)
    watch_players = Column(Text, nullable=True)
    evidence_note = Column(Text, nullable=True)
    prompt_version = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class AdvisorSession(Base):
    __tablename__ = "advisor_sessions"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    selected_team_ids = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class AdvisorMessage(Base):
    __tablename__ = "advisor_messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("advisor_sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    generated = Column(Boolean, nullable=False, default=True)
    task_type = Column(String, nullable=True)
    task_label = Column(String, nullable=True)
    tool_trace = Column(Text, nullable=True)
    scope_mode = Column(String, nullable=True)
    scope_team_ids = Column(Text, nullable=True)
    scope_team_count = Column(Integer, nullable=True)
    scope_player_count = Column(Integer, nullable=True)
    key_points = Column(Text, nullable=True)
    cited_team_ids = Column(Text, nullable=True)
    cited_player_ids = Column(Text, nullable=True)
    follow_up_suggestions = Column(Text, nullable=True)
    prompt_version = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
