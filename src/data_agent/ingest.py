from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd
from docx import Document
from pypdf import PdfReader

TABLE_EXTENSIONS = {".csv", ".xlsx"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}
SUPPORTED_EXTENSIONS = TABLE_EXTENSIONS | DOCUMENT_EXTENSIONS


@dataclass(frozen=True)
class IngestSummary:
    files_seen: int
    tables_loaded: int
    text_pages_loaded: int
    skipped: tuple[str, ...]


def _identifier(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    if not value or value[0].isdigit():
        value = f"file_{value}"
    return value[:100]


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _document_pages(path: Path) -> list[tuple[str, str]]:
    if path.suffix.lower() == ".pdf":
        return [(f"page {n}", page.extract_text() or "") for n, page in enumerate(PdfReader(path).pages, 1)]
    if path.suffix.lower() in {".md", ".txt"}:
        return [("text", path.read_text(encoding="utf-8"))]
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table_number, table in enumerate(doc.tables, 1):
        rows = [" | ".join(cell.text.strip() for cell in row.cells) for row in table.rows]
        paragraphs.append(f"Table {table_number}\n" + "\n".join(rows))
    return [(f"section {n}", text) for n, text in enumerate(paragraphs, 1)]


def ingest_folder(folder: str | Path, database: str | Path) -> IngestSummary:
    """Load CSV/XLSX sheets as DuckDB tables and PDF/DOCX text as searchable pages.

    This local demo reprocesses discovered files on each run. Production ingestion
    should persist a file manifest and enqueue changed files incrementally.
    """
    folder = Path(folder)
    database = Path(database)
    if not folder.is_dir():
        raise ValueError(f"Input folder does not exist: {folder}")
    database.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)
    pages: list[tuple[str, str, str, str]] = []
    loaded_tables = 0
    skipped: list[str] = []
    con = duckdb.connect(str(database))
    try:
        con.execute("CREATE TABLE IF NOT EXISTS _documents (source VARCHAR, location VARCHAR, content VARCHAR, sha256 VARCHAR)")
        con.execute("DELETE FROM _documents")
        for path in files:
            relative = path.relative_to(folder).as_posix()
            digest = _digest(path)
            try:
                if path.suffix.lower() == ".csv":
                    name = _identifier(Path(relative).with_suffix("").as_posix())
                    con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM read_csv_auto(?)', [str(path)])
                    loaded_tables += 1
                elif path.suffix.lower() == ".xlsx":
                    for sheet, frame in pd.read_excel(path, sheet_name=None).items():
                        name = _identifier(f"{Path(relative).with_suffix('').as_posix()}_{sheet}")
                        con.register("_incoming_sheet", frame)
                        con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM _incoming_sheet')
                        con.unregister("_incoming_sheet")
                        loaded_tables += 1
                else:
                    pages.extend((relative, location, text, digest) for location, text in _document_pages(path) if text.strip())
            except Exception as exc:
                skipped.append(f"{relative}: {type(exc).__name__}: {exc}")
        if pages:
            con.executemany("INSERT INTO _documents VALUES (?, ?, ?, ?)", pages)
        return IngestSummary(len(files), loaded_tables, len(pages), tuple(skipped))
    finally:
        con.close()


def list_tables(database: str | Path) -> list[dict[str, str]]:
    con = duckdb.connect(str(database), read_only=True, config={"external_access": "false"})
    try:
        return [{"table": name, "columns": columns} for name, columns in con.execute(
            "SELECT table_name, string_agg(column_name, ', ' ORDER BY ordinal_position) "
            "FROM information_schema.columns WHERE table_schema = 'main' AND table_name <> '_documents' "
            "GROUP BY table_name ORDER BY table_name"
        ).fetchall()]
    finally:
        con.close()


def search_documents(database: str | Path, query: str, limit: int = 5) -> list[dict[str, str]]:
    """Small lexical baseline; replace with hybrid/vector retrieval after measuring recall."""
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    con = duckdb.connect(str(database), read_only=True, config={"external_access": "false"})
    try:
        rows = con.execute("SELECT source, location, content FROM _documents").fetchall()
    finally:
        con.close()
    scored = []
    for source, location, content in rows:
        words = set(re.findall(r"[a-z0-9]+", content.lower()))
        score = len(terms & words) / max(1, len(terms))
        if score:
            scored.append({"source": source, "location": location, "content": content, "score": score})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:max(1, limit)]


def run_readonly_sql(database: str | Path, sql: str, max_rows: int = 100) -> list[dict[str, object]]:
    """Execute a single SELECT over ingested tables; files are never exposed as SQL sources."""
    import sqlglot
    from sqlglot import exp

    parsed = sqlglot.parse(sql, read="duckdb")
    if len(parsed) != 1 or not isinstance(parsed[0], exp.Select):
        raise ValueError("Only one SELECT statement is allowed")
    allowed = {item["table"] for item in list_tables(database)}
    for table in parsed[0].find_all(exp.Table):
        if table.name.lower() not in allowed:
            raise ValueError(f"Unknown table: {table.name}")
    con = duckdb.connect(str(database), read_only=True, config={"external_access": "false", "threads": "2"})
    try:
        cursor = con.execute(sql)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchmany(max_rows)]
    finally:
        con.close()

