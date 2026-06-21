"""Show recently saved raw documents."""

from __future__ import annotations

from app.database.repository import SquadAdvisorRepository


def main(limit: int = 5) -> None:
    repo = SquadAdvisorRepository()
    try:
        documents = repo.list_raw_documents(limit=limit)
        print(f"Raw Documents: {len(documents)}")
        print("-" * 60)
        for document in documents:
            print(document.id)
            print(document.source_id)
            print(document.document_type)
            print(document.title)
            print(document.url)
            print(
                f"html_len={len(document.raw_html or '')} "
                f"text_len={len(document.raw_text or '')}"
            )
            preview = (document.raw_text or "")[:240].replace("\n", " ")
            print(f"preview={preview}")
            print("-" * 60)
    finally:
        repo.close()


if __name__ == "__main__":
    main()
