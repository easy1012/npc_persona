from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import psycopg
from psycopg.types.json import Jsonb


SUPPORTED_SUFFIXES = {".md", ".yaml", ".yml", ".json"}


@dataclass(frozen=True, slots=True)
class CorpusDocument:
    id: UUID
    source_id: str
    source_type: str
    title: str
    content: str
    metadata: dict[str, str]


def _title(path: Path, content: str) -> str:
    if path.suffix.lower() == ".md":
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return path.stem.replace("_", " ")


def discover_documents(source_dir: Path) -> tuple[CorpusDocument, ...]:
    documents: list[CorpusDocument] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(source_dir).as_posix()
        source_id = f"rsc/data/{relative}"
        documents.append(
            CorpusDocument(
                id=uuid5(NAMESPACE_URL, source_id),
                source_id=source_id,
                source_type=path.parent.name,
                title=_title(path, content),
                content=content,
                metadata={"path": source_id, "format": path.suffix.lower().lstrip(".")},
            )
        )
    return tuple(documents)


def _psycopg_dsn(dsn: str) -> str:
    return dsn.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg://", "postgresql://"
    )


def ingest_documents(dsn: str, documents: tuple[CorpusDocument, ...]) -> int:
    statement = """
    INSERT INTO full_knowledge_documents
        (id, source_id, source_type, title, content, document_metadata)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (source_id) DO UPDATE SET
        source_type = EXCLUDED.source_type,
        title = EXCLUDED.title,
        content = EXCLUDED.content,
        document_metadata = EXCLUDED.document_metadata
    """
    rows = [
        (
            document.id,
            document.source_id,
            document.source_type,
            document.title,
            document.content,
            Jsonb(document.metadata),
        )
        for document in documents
    ]
    with psycopg.connect(_psycopg_dsn(dsn)) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(statement, rows)
    return len(rows)


def main() -> None:
    source_dir = Path(os.getenv("CORPUS_SOURCE_DIR", "rsc/data"))
    documents = discover_documents(source_dir)
    count = ingest_documents(os.environ["POSTGRES_DSN"], documents)
    print(f"Upserted {count} full-corpus documents.")


if __name__ == "__main__":
    main()
