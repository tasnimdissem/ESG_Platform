from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List

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


def _read_dataset(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return _read_text(file_path)

    if suffix in {".xlsx", ".xls"}:
        try:
            import pandas as pd  # type: ignore
        except ImportError as exc:
            logger.warning(
                "Skipping Excel file %s because pandas is not installed. "
                "Install pandas only if you need Excel ingestion.",
                file_path.name,
            )
            return ""

        df = pd.read_excel(file_path)
        texts = []
        for _, row in df.iterrows():
            text = f"""
Company: {row.get('company', '')}
Sector: {row.get('sector', '')}
CO2 emissions: {row.get('co2', '')}
Energy consumption: {row.get('energy', '')}
Employee satisfaction: {row.get('employee', '')}
Board diversity: {row.get('board', '')}
"""
            texts.append(_clean_text(text))
        return "\n".join(texts)

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

    for pdf_path in sorted(config.RAW_PDFS_DIR.glob("*.pdf")):
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

    for article_path in sorted(config.RAW_ARTICLES_DIR.glob("*")):
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

    for dataset_path in sorted(config.RAW_DATASETS_DIR.glob("*")):
        if dataset_path.is_dir():
            continue
        text = _read_dataset(dataset_path)
        for i, chunk in enumerate(_chunk_text(text)):
            documents.append(
                {
                    "source_type": "dataset",
                    "source_name": dataset_path.name,
                    "chunk_id": f"dataset-{dataset_path.stem}-{i}",
                    "text": chunk,
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
