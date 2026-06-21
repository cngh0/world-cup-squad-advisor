"""Helpers for reading configured sources."""

from __future__ import annotations

from pathlib import Path
import tomllib


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "sources.toml"


def list_source_configs() -> list[dict]:
    with CONFIG_PATH.open("rb") as file:
        data = tomllib.load(file)
    return data.get("sources", [])


def get_source_config(source_id: str) -> dict | None:
    for source in list_source_configs():
        if source["id"] == source_id:
            return source
    return None
