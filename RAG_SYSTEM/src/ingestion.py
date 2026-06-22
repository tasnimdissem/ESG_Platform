from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from PyPDF2 import PdfReader

from . import config
from .structured_transform import transform_chunks


logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _read_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return _clean_text("\n".join(pages))


def _read_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore").strip()


def _df_to_rows(df: Any) -> List[Dict[str, str]]:
    """Convert a structured ESG DataFrame to a list of {text, sector, company, year}."""
    rows: List[Dict[str, str]] = []
    for _, row in df.iterrows():
        company   = row.get("company_name") or row.get("company", "")
        sector    = row.get("primary_industry") or row.get("sector", "")
        country   = row.get("hq_country", "")
        year      = row.get("year", "")
        ticker    = row.get("ticker", "")
        esg_score = row.get("esg_score_v3", "")
        score_e   = row.get("score_E", "")
        score_s   = row.get("score_S", "")
        score_g   = row.get("score_G", "")
        scope1    = row.get("log_scope_1") or row.get("co2", "")
        scope2    = row.get("log_scope_2", "")
        scope3    = row.get("log_scope_3", "")
        energy    = row.get("log_energy_consumption") or row.get("energy", "")
        board     = row.get("independent_board_members_percentage") or row.get("board", "")
        employees = row.get("log_employees") or row.get("employee", "")
        training  = row.get("log_hours_of_training_wins", "")
        waste     = row.get("log_waste_production", "")
        water     = row.get("log_water_consumption", "")

        parts = [f"Company: {company}", f"Sector: {sector}"]
        if country:        parts.append(f"Country: {country}")
        if year:           parts.append(f"Year: {year}")
        if ticker:         parts.append(f"Ticker: {ticker}")
        if esg_score != "": parts.append(f"ESG Score: {esg_score}")
        if score_e   != "": parts.append(f"Environmental Score: {score_e}")
        if score_s   != "": parts.append(f"Social Score: {score_s}")
        if score_g   != "": parts.append(f"Governance Score: {score_g}")
        if scope1    != "": parts.append(f"Scope 1 Emissions (log): {scope1}")
        if scope2    != "": parts.append(f"Scope 2 Emissions (log): {scope2}")
        if scope3    != "": parts.append(f"Scope 3 Emissions (log): {scope3}")
        if energy    != "": parts.append(f"Energy Consumption (log): {energy}")
        if waste     != "": parts.append(f"Waste Production (log): {waste}")
        if water     != "": parts.append(f"Water Consumption (log): {water}")
        if board     != "": parts.append(f"Board Independence: {board}")
        if employees != "": parts.append(f"Employees (log): {employees}")
        if training  != "": parts.append(f"Training Hours (log): {training}")

        rows.append({
            "text": _clean_text(" | ".join(parts)),
            "sector": str(sector).strip() if sector else "",
            "company": str(company).strip() if company else "",
            "year": str(year).strip() if year else "",
        })
    return rows


def _read_dataset_rows(file_path: Path) -> List[Dict[str, str]]:
    """Read a structured dataset and return per-row dicts with sector metadata.

    Returns a list of {text, sector, company, year} for Excel/CSV files,
    or a single {text, sector:"", ...} item for other formats.
    """
    suffix = file_path.suffix.lower()

    if suffix in {".xlsx", ".xls", ".csv"}:
        try:
            import pandas as pd  # type: ignore
        except ImportError:
            logger.warning("Skipping %s — pandas not installed.", file_path.name)
            return []

        try:
            if suffix == ".xlsx":
                df = pd.read_excel(file_path, engine="openpyxl")
            elif suffix == ".xls":
                try:
                    df = pd.read_excel(file_path, engine="xlrd")
                except Exception:
                    df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
            else:
                df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
        except Exception as exc:
            logger.warning("Could not read dataset %s: %s", file_path.name, exc)
            return []

        return _df_to_rows(df)

    # Fallback for JSON, TSV, plain text — no sector metadata available
    text = _read_dataset(file_path)
    return [{"text": text, "sector": "", "company": "", "year": ""}] if text else []


def _read_dataset(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return _read_text(file_path)

    if suffix in {".xlsx", ".xls"}:
        try:
            import pandas as pd  # type: ignore
        except ImportError:
            logger.warning(
                "Skipping Excel file %s because pandas is not installed.",
                file_path.name,
            )
            return ""

        # Some .xls files are actually CSVs — fall back gracefully.
        try:
            df = pd.read_excel(file_path)
        except Exception:
            try:
                df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
            except Exception as exc:
                logger.warning("Could not read dataset %s: %s", file_path.name, exc)
                return ""

        return "\n".join(r["text"] for r in _df_to_rows(df))

    if suffix == ".json":
        raw = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
        return json.dumps(raw, ensure_ascii=True)

    if suffix == ".tsv":
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f, delimiter="\t")
            return "\n".join(",".join(row) for row in reader)

    return _read_text(file_path)


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: List[str] = []
    start = 0
    text_len = len(cleaned)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Word-boundary adjustment: look backward for a space to avoid cutting a word in half.
        if end < text_len:
            last_space = cleaned.rfind(" ", start, end)
            if last_space != -1 and last_space > start + (chunk_size // 2):
                end = last_space

        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        if end >= text_len:
            break
            
        # Adjust next start so it doesn't start in the middle of a word
        start = end - overlap
        if start > 0 and cleaned[start - 1] != " ":
            next_space = cleaned.find(" ", start)
            if next_space != -1 and next_space < start + overlap:
                start = next_space + 1

    return chunks


def ingest_sources() -> List[Dict[str, str]]:
    documents: List[Dict[str, str]] = []

    for pdf_path in sorted(config.RAW_PDFS_DIR.rglob("*.pdf")):
        if not pdf_path.is_file():
            continue
        text = _read_pdf(pdf_path)
        for i, chunk in enumerate(_chunk_text(text)):
            documents.append(
                {
                    "source_type": "pdf",
                    "source_name": pdf_path.name,
                    "chunk_id": f"pdf-{pdf_path.stem}-{i}",
                    "text": chunk,
                }
            )

    for article_path in sorted(config.RAW_ARTICLES_DIR.rglob("*")):
        if article_path.is_dir():
            continue
        text = _read_text(article_path)
        for i, chunk in enumerate(_chunk_text(text)):
            documents.append(
                {
                    "source_type": "article",
                    "source_name": article_path.name,
                    "chunk_id": f"article-{article_path.stem}-{i}",
                    "text": chunk,
                }
            )

    for dataset_path in sorted(config.RAW_DATASETS_DIR.rglob("*")):
        if dataset_path.is_dir():
            continue
        suffix = dataset_path.suffix.lower()
        if suffix in {".xlsx", ".xls", ".csv"}:
            # Per-row ingestion preserves sector metadata for targeted retrieval
            rows = _read_dataset_rows(dataset_path)
            for row_idx, row_data in enumerate(rows):
                for i, chunk in enumerate(_chunk_text(row_data["text"])):
                    documents.append(
                        {
                            "source_type": "dataset",
                            "source_name": dataset_path.name,
                            "chunk_id": f"dataset-{dataset_path.stem}-r{row_idx}-{i}",
                            "text": chunk,
                            "sector": row_data.get("sector", ""),
                        }
                    )
        else:
            text = _read_dataset(dataset_path)
            for i, chunk in enumerate(_chunk_text(text)):
                documents.append(
                    {
                        "source_type": "dataset",
                        "source_name": dataset_path.name,
                        "chunk_id": f"dataset-{dataset_path.stem}-{i}",
                        "text": chunk,
                        "sector": "",
                    }
                )

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = config.PROCESSED_DIR / "chunks.json"
    out_path.write_text(json.dumps(documents, ensure_ascii=True, indent=2), encoding="utf-8")

    structured_documents = transform_chunks(documents)
    structured_out_path = config.PROCESSED_DIR / "structured_chunks.json"
    structured_out_path.write_text(
        json.dumps(structured_documents, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    return documents
