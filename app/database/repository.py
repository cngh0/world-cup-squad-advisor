"""Minimal repository layer for Phase 1."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.database.models import (
    AdvisorMessage,
    AdvisorSession,
    CrawlRun,
    DataSource,
    Player,
    PlayerReport,
    RawDocument,
    SquadMembership,
    Team,
    TeamReport,
    Tournament,
    utcnow,
)
from app.domain.ids import slugify


class SquadAdvisorRepository:
    """Wrap the database access used by the first project phases."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    def close(self) -> None:
        self.session.close()

    def get_data_source_by_id(self, source_id: str) -> Optional[DataSource]:
        return self.session.query(DataSource).filter_by(id=source_id).first()

    def list_data_sources(self) -> list[DataSource]:
        return self.session.query(DataSource).order_by(DataSource.id).all()

    def upsert_data_source(self, source: DataSource) -> DataSource:
        existing = self.get_data_source_by_id(source.id)
        if existing is None:
            self.session.add(source)
            self.session.commit()
            return source

        existing.name = source.name
        existing.base_url = source.base_url
        existing.source_type = source.source_type
        existing.coverage_type = source.coverage_type
        existing.reliability_level = source.reliability_level
        existing.enabled = source.enabled
        self.session.commit()
        return existing

    def create_crawl_run(self, crawl_run: CrawlRun) -> CrawlRun:
        self.session.add(crawl_run)
        self.session.commit()
        return crawl_run

    def finish_crawl_run(
        self,
        crawl_run_id: str,
        status: str,
        fetched_count: int,
        saved_count: int,
        error_summary: str | None = None,
        finished_at=None,
    ) -> bool:
        crawl_run = self.session.query(CrawlRun).filter_by(id=crawl_run_id).first()
        if crawl_run is None:
            return False

        crawl_run.status = status
        crawl_run.fetched_count = fetched_count
        crawl_run.saved_count = saved_count
        crawl_run.error_summary = error_summary
        crawl_run.finished_at = finished_at
        self.session.commit()
        return True

    def get_raw_document(self, source_id: str, external_id: str) -> Optional[RawDocument]:
        return (
            self.session.query(RawDocument)
            .filter_by(source_id=source_id, external_id=external_id)
            .first()
        )

    def save_raw_document(self, document: RawDocument) -> RawDocument:
        existing = self.get_raw_document(document.source_id, document.external_id)
        if existing is None:
            self.session.add(document)
            self.session.commit()
            return document

        existing.url = document.url
        existing.document_type = document.document_type
        existing.title = document.title
        existing.raw_html = document.raw_html
        existing.raw_text = document.raw_text
        existing.content_hash = document.content_hash
        existing.crawl_run_id = document.crawl_run_id
        existing.fetched_at = document.fetched_at
        self.session.commit()
        return existing

    def list_raw_documents(self, limit: int = 10) -> list[RawDocument]:
        return (
            self.session.query(RawDocument)
            .order_by(RawDocument.fetched_at.desc())
            .limit(limit)
            .all()
        )

    def get_latest_raw_document_by_source(self, source_id: str) -> Optional[RawDocument]:
        return (
            self.session.query(RawDocument)
            .filter_by(source_id=source_id)
            .order_by(RawDocument.fetched_at.desc())
            .first()
        )

    def get_tournament_by_id(self, tournament_id: str) -> Optional[Tournament]:
        return self.session.query(Tournament).filter_by(id=tournament_id).first()

    def list_tournaments(self) -> list[Tournament]:
        return self.session.query(Tournament).order_by(Tournament.year, Tournament.id).all()

    def upsert_tournament(self, tournament: Tournament) -> Tournament:
        existing = self.get_tournament_by_id(tournament.id)
        if existing is None:
            self.session.add(tournament)
            self.session.commit()
            return tournament

        existing.name = tournament.name
        existing.year = tournament.year
        existing.host = tournament.host
        existing.status = tournament.status
        self.session.commit()
        return existing

    def get_team_by_id(self, team_id: str) -> Optional[Team]:
        return self.session.query(Team).filter_by(id=team_id).first()

    def list_teams(self) -> list[Team]:
        return self.session.query(Team).order_by(Team.name).all()

    def list_teams_without_report(self, limit: int | None = None) -> list[Team]:
        query = (
            self.session.query(Team)
            .outerjoin(TeamReport, TeamReport.team_id == Team.id)
            .filter(TeamReport.team_id.is_(None))
            .order_by(Team.name.asc())
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def upsert_team(self, team: Team) -> Team:
        existing = self.get_team_by_id(team.id)
        if existing is None:
            self.session.add(team)
            self.session.commit()
            return team

        existing.tournament_id = team.tournament_id
        existing.name = team.name
        existing.fifa_code = team.fifa_code
        existing.group_name = team.group_name
        existing.confederation = team.confederation
        existing.coach_name = team.coach_name
        existing.official_page_url = team.official_page_url
        self.session.commit()
        return existing

    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        return self.session.query(Player).filter_by(id=player_id).first()

    def list_players(self) -> list[Player]:
        return self.session.query(Player).order_by(Player.full_name).all()

    def list_players_without_report(
        self,
        limit: int | None = None,
    ) -> list[tuple[Player, SquadMembership, Team]]:
        query = (
            self.session.query(Player, SquadMembership, Team)
            .join(SquadMembership, SquadMembership.player_id == Player.id)
            .join(Team, Team.id == SquadMembership.team_id)
            .outerjoin(PlayerReport, PlayerReport.player_id == Player.id)
            .filter(PlayerReport.player_id.is_(None))
            .order_by(Team.name.asc(), SquadMembership.shirt_number.asc(), Player.full_name.asc())
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def upsert_player(self, player: Player) -> Player:
        existing = self.get_player_by_id(player.id)
        if existing is None:
            self.session.add(player)
            self.session.commit()
            return player

        existing.full_name = player.full_name
        existing.normalized_name = player.normalized_name
        existing.birth_date = player.birth_date
        existing.nationality = player.nationality
        existing.club_name = player.club_name
        existing.club_country = player.club_country
        existing.preferred_position = player.preferred_position
        existing.profile_source_url = player.profile_source_url
        self.session.commit()
        return existing

    def get_squad_membership_by_id(self, membership_id: str) -> Optional[SquadMembership]:
        return self.session.query(SquadMembership).filter_by(id=membership_id).first()

    def delete_squad_membership_by_id(self, membership_id: str) -> bool:
        membership = self.get_squad_membership_by_id(membership_id)
        if membership is None:
            return False

        self.session.delete(membership)
        self.session.commit()
        return True

    def upsert_squad_membership(self, membership: SquadMembership) -> SquadMembership:
        existing = self.get_squad_membership_by_id(membership.id)
        if existing is None:
            self.session.add(membership)
            self.session.commit()
            return membership

        existing.tournament_id = membership.tournament_id
        existing.team_id = membership.team_id
        existing.player_id = membership.player_id
        existing.source_document_id = membership.source_document_id
        existing.shirt_number = membership.shirt_number
        existing.position_group = membership.position_group
        existing.caps = membership.caps
        existing.goals = membership.goals
        existing.is_captain = membership.is_captain
        existing.status = membership.status
        self.session.commit()
        return existing

    def get_team_squad(self, team_id: str) -> list[tuple[SquadMembership, Player]]:
        return (
            self.session.query(SquadMembership, Player)
            .join(Player, Player.id == SquadMembership.player_id)
            .filter(SquadMembership.team_id == team_id)
            .order_by(SquadMembership.shirt_number.asc(), Player.full_name.asc())
            .all()
        )

    def search_player_rows(
        self,
        name_query: str | None = None,
        team_id: str | None = None,
        position_group: str | None = None,
        limit: int | None = None,
    ) -> list[tuple[Player, SquadMembership, Team, PlayerReport | None]]:
        query = (
            self.session.query(Player, SquadMembership, Team, PlayerReport)
            .join(SquadMembership, SquadMembership.player_id == Player.id)
            .join(Team, Team.id == SquadMembership.team_id)
            .outerjoin(PlayerReport, PlayerReport.player_id == Player.id)
        )

        if name_query:
            like_term = f"%{name_query}%"
            normalized_term = f"%{slugify(name_query)}%"
            query = query.filter(
                or_(
                    Player.full_name.ilike(like_term),
                    Player.normalized_name.ilike(normalized_term),
                )
            )

        if team_id:
            query = query.filter(SquadMembership.team_id == team_id)

        if position_group:
            query = query.filter(SquadMembership.position_group == position_group)

        query = query.order_by(
            Team.name.asc(),
            SquadMembership.shirt_number.asc(),
            Player.full_name.asc(),
        )

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_player_context(
        self,
        player_id: str,
    ) -> Optional[tuple[Player, SquadMembership, Team, PlayerReport | None]]:
        return (
            self.session.query(Player, SquadMembership, Team, PlayerReport)
            .join(SquadMembership, SquadMembership.player_id == Player.id)
            .join(Team, Team.id == SquadMembership.team_id)
            .outerjoin(PlayerReport, PlayerReport.player_id == Player.id)
            .filter(Player.id == player_id)
            .first()
        )

    def get_player_report(self, player_id: str) -> Optional[PlayerReport]:
        return self.session.query(PlayerReport).filter_by(player_id=player_id).first()

    def create_player_report(self, report: PlayerReport) -> Optional[PlayerReport]:
        existing = self.get_player_report(report.player_id)
        if existing is not None:
            return None
        self.session.add(report)
        self.session.commit()
        return report

    def update_player_report(
        self,
        player_id: str,
        summary: str,
        strengths: str | None = None,
        concerns: str | None = None,
        role_tags: str | None = None,
        evidence_note: str | None = None,
        prompt_version: str | None = None,
        model_name: str | None = None,
        source_document_id: str | None = None,
    ) -> bool:
        report = self.get_player_report(player_id)
        if report is None:
            return False

        report.summary = summary
        report.strengths = strengths
        report.concerns = concerns
        report.role_tags = role_tags
        report.evidence_note = evidence_note
        report.prompt_version = prompt_version
        report.model_name = model_name
        report.source_document_id = source_document_id
        report.created_at = utcnow()
        self.session.commit()
        return True

    def get_team_report(self, team_id: str) -> Optional[TeamReport]:
        return self.session.query(TeamReport).filter_by(team_id=team_id).first()

    def create_team_report(self, report: TeamReport) -> Optional[TeamReport]:
        existing = self.get_team_report(report.team_id)
        if existing is not None:
            return None
        self.session.add(report)
        self.session.commit()
        return report

    def update_team_report(
        self,
        team_id: str,
        summary: str,
        style_of_play: str | None = None,
        strengths: str | None = None,
        risks: str | None = None,
        watch_players: str | None = None,
        evidence_note: str | None = None,
        prompt_version: str | None = None,
        model_name: str | None = None,
        source_document_id: str | None = None,
    ) -> bool:
        report = self.get_team_report(team_id)
        if report is None:
            return False

        report.summary = summary
        report.style_of_play = style_of_play
        report.strengths = strengths
        report.risks = risks
        report.watch_players = watch_players
        report.evidence_note = evidence_note
        report.prompt_version = prompt_version
        report.model_name = model_name
        report.source_document_id = source_document_id
        report.created_at = utcnow()
        self.session.commit()
        return True

    def get_recent_team_reports(self, limit: int = 10) -> list[tuple[TeamReport, Team]]:
        return (
            self.session.query(TeamReport, Team)
            .join(Team, Team.id == TeamReport.team_id)
            .order_by(TeamReport.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent_player_reports(
        self,
        limit: int = 10,
    ) -> list[tuple[PlayerReport, Player, SquadMembership, Team]]:
        return (
            self.session.query(PlayerReport, Player, SquadMembership, Team)
            .join(Player, Player.id == PlayerReport.player_id)
            .join(SquadMembership, SquadMembership.player_id == Player.id)
            .join(Team, Team.id == SquadMembership.team_id)
            .order_by(PlayerReport.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_team_report_count(self) -> int:
        return self.session.query(TeamReport).count()

    def get_player_report_count(self) -> int:
        return self.session.query(PlayerReport).count()

    def get_advisor_session_by_id(self, session_id: str) -> Optional[AdvisorSession]:
        return self.session.query(AdvisorSession).filter_by(id=session_id).first()

    def list_advisor_sessions(self, limit: int = 20) -> list[AdvisorSession]:
        return (
            self.session.query(AdvisorSession)
            .order_by(AdvisorSession.updated_at.desc(), AdvisorSession.created_at.desc())
            .limit(limit)
            .all()
        )

    def create_advisor_session(self, advisor_session: AdvisorSession) -> AdvisorSession:
        self.session.add(advisor_session)
        self.session.commit()
        return advisor_session

    def update_advisor_session(
        self,
        session_id: str,
        *,
        title: str | None = None,
        selected_team_ids: str | None = None,
        updated_at=None,
    ) -> bool:
        advisor_session = self.get_advisor_session_by_id(session_id)
        if advisor_session is None:
            return False

        if title is not None:
            advisor_session.title = title
        if selected_team_ids is not None:
            advisor_session.selected_team_ids = selected_team_ids
        advisor_session.updated_at = updated_at or utcnow()
        self.session.commit()
        return True

    def save_advisor_turn(
        self,
        *,
        advisor_messages: list[AdvisorMessage],
        session_id: str | None = None,
        new_session: AdvisorSession | None = None,
        title: str | None = None,
        selected_team_ids: str | None = None,
        updated_at=None,
    ) -> AdvisorSession:
        if new_session is None and session_id is None:
            raise ValueError("Provide session_id or new_session when saving an advisor turn.")

        try:
            if new_session is not None:
                advisor_session = new_session
                if title is not None:
                    advisor_session.title = title
                if selected_team_ids is not None:
                    advisor_session.selected_team_ids = selected_team_ids
                advisor_session.updated_at = updated_at or utcnow()
                self.session.add(advisor_session)
                self.session.flush()
            else:
                advisor_session = self.get_advisor_session_by_id(session_id)
                if advisor_session is None:
                    raise ValueError(f"Advisor session not found: {session_id}")
                if title is not None:
                    advisor_session.title = title
                if selected_team_ids is not None:
                    advisor_session.selected_team_ids = selected_team_ids
                advisor_session.updated_at = updated_at or utcnow()

            self.session.add_all(advisor_messages)
            self.session.commit()
            return advisor_session
        except Exception:
            self.session.rollback()
            raise

    def list_advisor_messages(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[AdvisorMessage]:
        asc_role_rank = case((AdvisorMessage.role == "user", 0), else_=1)
        desc_role_rank = case((AdvisorMessage.role == "assistant", 0), else_=1)

        query = (
            self.session.query(AdvisorMessage)
            .filter(AdvisorMessage.session_id == session_id)
            .order_by(
                AdvisorMessage.created_at.asc(),
                asc_role_rank.asc(),
                AdvisorMessage.id.asc(),
            )
        )

        if limit is None:
            return query.all()

        recent = (
            self.session.query(AdvisorMessage)
            .filter(AdvisorMessage.session_id == session_id)
            .order_by(
                AdvisorMessage.created_at.desc(),
                desc_role_rank.asc(),
                AdvisorMessage.id.desc(),
            )
            .limit(limit)
            .all()
        )
        recent.reverse()
        return recent

    def create_advisor_message(self, advisor_message: AdvisorMessage) -> AdvisorMessage:
        self.session.add(advisor_message)
        self.session.commit()
        return advisor_message

    def create_advisor_messages(self, advisor_messages: list[AdvisorMessage]) -> list[AdvisorMessage]:
        self.session.add_all(advisor_messages)
        self.session.commit()
        return advisor_messages

    def get_advisor_session_count(self) -> int:
        return self.session.query(AdvisorSession).count()

    def get_advisor_message_count(self, session_id: str | None = None) -> int:
        query = self.session.query(AdvisorMessage)
        if session_id is not None:
            query = query.filter(AdvisorMessage.session_id == session_id)
        return query.count()

    def delete_player_if_unreferenced(self, player_id: str) -> bool:
        player = self.get_player_by_id(player_id)
        if player is None:
            return False

        remaining_membership = (
            self.session.query(SquadMembership)
            .filter(SquadMembership.player_id == player_id)
            .first()
        )
        if remaining_membership is not None:
            return False

        self.session.delete(player)
        self.session.commit()
        return True

    def get_team_count(self) -> int:
        return self.session.query(Team).count()

    def get_tournament_count(self) -> int:
        return self.session.query(Tournament).count()

    def get_data_source_count(self) -> int:
        return self.session.query(DataSource).count()

    def get_player_count(self) -> int:
        return self.session.query(Player).count()

    def get_raw_document_count(self) -> int:
        return self.session.query(RawDocument).count()
