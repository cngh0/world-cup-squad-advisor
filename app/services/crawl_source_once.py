"""Fetch one configured source page and save it as a raw document."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib

import requests
from bs4 import BeautifulSoup

from app.database.models import CrawlRun, RawDocument
from app.database.repository import SquadAdvisorRepository
from app.services.source_config import get_source_config


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def build_crawl_run_id(source_id: str) -> str:
    timestamp = utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"crawl:{source_id}:{timestamp}"


def infer_document_type(source_id: str) -> str:
    if source_id == "wikipedia_world_cup_squads":
        return "squad_page"
    if source_id == "fifa_teams":
        return "teams_index"
    return "source_page"


def fetch_page(url: str) -> tuple[str, str]:
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    return response.text, response.url


def extract_title_and_text(html: str, fallback_title: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    title = fallback_title
    if soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(strip=True)
    raw_text = soup.get_text("\n", strip=True)
    return title, raw_text


def main(source_id: str) -> None:
    source = get_source_config(source_id)
    if source is None:
        raise SystemExit(f"Unknown source_id: {source_id}")

    repo = SquadAdvisorRepository()
    crawl_run_id = build_crawl_run_id(source_id)
    crawl_run = CrawlRun(
        id=crawl_run_id,
        source_id=source_id,
        target_key=source["base_url"],
        status="started",
        started_at=utcnow(),
    )
    repo.create_crawl_run(crawl_run)

    try:
        html, final_url = fetch_page(source["base_url"])
        title, raw_text = extract_title_and_text(html, source["name"])
        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        external_id = final_url
        document = RawDocument(
            id=f"raw:{source_id}:{content_hash[:12]}",
            source_id=source_id,
            crawl_run_id=crawl_run_id,
            external_id=external_id,
            url=final_url,
            document_type=infer_document_type(source_id),
            title=title,
            raw_html=html,
            raw_text=raw_text,
            content_hash=content_hash,
            fetched_at=utcnow(),
        )

        existing = repo.get_raw_document(source_id, external_id)
        saved = repo.save_raw_document(document)
        repo.finish_crawl_run(
            crawl_run_id=crawl_run_id,
            status="success",
            fetched_count=1,
            saved_count=1,
            finished_at=utcnow(),
        )

        action = "updated" if existing is not None else "inserted"
        print("Crawl complete")
        print(f"source_id={source_id}")
        print(f"crawl_run_id={crawl_run_id}")
        print(f"document_id={saved.id}")
        print(f"action={action}")
        print(f"title={saved.title}")
        print(f"url={saved.url}")
        print(f"raw_text_length={len(saved.raw_text or '')}")
    except Exception as exc:
        repo.finish_crawl_run(
            crawl_run_id=crawl_run_id,
            status="failed",
            fetched_count=0,
            saved_count=0,
            error_summary=str(exc),
            finished_at=utcnow(),
        )
        raise
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit("Run via `python main.py crawl-source <source_id>`")
