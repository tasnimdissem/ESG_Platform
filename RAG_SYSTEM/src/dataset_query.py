from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from . import config

logger = logging.getLogger(__name__)

_DATASET_CACHE: Optional[pd.DataFrame] = None

# Generic words common in company names — too ambiguous to use as unique identifiers.
_COMPANY_WORD_BLACKLIST = {
    "group", "holding", "holdings", "limited", "corporation", "incorporated",
    "company", "companies", "enterprise", "enterprises", "global", "national",
    "services", "systems", "solutions", "management", "capital", "financial",
    "bank", "investment", "energy", "power", "resources", "development",
    "properties", "industrial", "international", "commercial", "technology",
    "technologies", "healthcare", "pharma", "pharmaceutical", "chemical",
    "media", "digital", "electric", "electrical", "science", "sciences",
    "research", "products", "materials", "industries", "infrastructure",
    "communications", "logistics", "trading", "retail", "estate", "realty",
    "insurance", "asset", "private", "public", "markets", "ventures",
}


def _load_dataset() -> Optional[pd.DataFrame]:
    global _DATASET_CACHE
    if _DATASET_CACHE is not None:
        return _DATASET_CACHE

    for pattern in ("*.xls", "*.xlsx", "*.csv"):
        for p in config.RAW_DATASETS_DIR.glob(pattern):
            try:
                df = pd.read_csv(p, encoding="utf-8", on_bad_lines="skip")
                if "company_name" in df.columns and "esg_score_v3" in df.columns:
                    _DATASET_CACHE = df
                    logger.info("Dataset loaded: %s (%d rows)", p.name, len(df))
                    return df
            except Exception as exc:
                logger.warning("Could not load dataset %s: %s", p.name, exc)
    return None


def _row_to_text(row: pd.Series) -> str:
    def fmt(val, d: int = 4) -> str:
        try:
            return f"{float(val):.{d}f}"
        except (TypeError, ValueError):
            return str(val)

    parts = [
        f"Company: {row.get('company_name', '')}",
        f"Sector: {row.get('primary_industry', '')}",
        f"Country: {row.get('hq_country', '')}",
        f"Year: {row.get('year', '')}",
        f"Ticker: {row.get('ticker', '')}",
        f"ESG Score (0-100): {fmt(row.get('esg_score_v3', ''))}",
        f"Environmental Score: {fmt(row.get('score_E', ''))}",
        f"Social Score: {fmt(row.get('score_S', ''))}",
        f"Governance Score: {fmt(row.get('score_G', ''))}",
        f"Scope 1 Emissions (log): {fmt(row.get('log_scope_1', ''))}",
        f"Scope 2 Emissions (log): {fmt(row.get('log_scope_2', ''))}",
        f"Scope 3 Emissions (log): {fmt(row.get('log_scope_3', ''))}",
        f"Energy Consumption (log): {fmt(row.get('log_energy_consumption', ''))}",
        f"Waste Production (log): {fmt(row.get('log_waste_production', ''))}",
        f"Water Consumption (log): {fmt(row.get('log_water_consumption', ''))}",
        f"Board Independence (%): {fmt(row.get('independent_board_members_percentage', ''))}",
        f"Employees (log): {fmt(row.get('log_employees', ''))}",
        f"Market Cap (log): {fmt(row.get('log_market_cap', ''))}",
    ]
    return " | ".join(parts)


def _exact_company_hits(df: pd.DataFrame, q_lower: str) -> list[str]:
    """Full company name appears as substring in the question."""
    return [
        str(name)
        for name in df["company_name"].dropna().unique()
        if str(name).lower() in q_lower
    ]


def _word_company_hits(df: pd.DataFrame, q_lower: str) -> list[str]:
    """
    Word-level company match — used only as last resort when no sector/country/year.
    Requires 2+ unique tokens (>= 5 chars, not blacklisted) or 1 token >= 8 chars.
    """
    hits = []
    for name in df["company_name"].dropna().unique():
        name_lower = str(name).lower()
        tokens = [
            w for w in name_lower.split()
            if len(w) >= 5
            and w not in _COMPANY_WORD_BLACKLIST
            and not w.replace(".", "").replace(",", "").replace("'", "").isdigit()
        ]
        n_match = sum(1 for t in tokens if t in q_lower)
        if n_match >= 2:
            hits.append(str(name))
        elif n_match == 1 and any(len(t) >= 8 and t in q_lower for t in tokens):
            hits.append(str(name))
    return hits


def lookup_exact(question: str, top_k: int = 10) -> str:
    """
    Query the raw dataset with pandas for exact keyword matches.
    Returns formatted rows with verbatim values, or "" if no match found.

    Priority (to avoid false positives):
      1. Exact company name found  → filter by company (+ year if present)
      2. Sector or country found   → filter by those (+ year if present)
      3. Only year found           → filter by year, return top-k by ESG score
      4. Only ambiguous word match → filter by word-matched companies
      5. Nothing found             → return ""
    """
    df = _load_dataset()
    if df is None:
        return ""

    q_lower = question.lower()

    # Year: 4-digit number present in question
    year_hits = [
        int(y)
        for y in df["year"].dropna().unique()
        if str(int(y)) in q_lower
    ]

    # Sector: full phrase match (e.g. "industrial machinery" in question)
    sector_hits = [
        str(s)
        for s in df["primary_industry"].dropna().unique()
        if str(s).lower() in q_lower
    ]

    # Country: full phrase match (e.g. "sweden", "united states")
    country_hits = [
        str(c)
        for c in df["hq_country"].dropna().unique()
        if str(c).lower() in q_lower
    ]

    # Company: exact full name match first
    exact_co = _exact_company_hits(df, q_lower)

    # Build mask based on priority
    mask = pd.Series([True] * len(df), index=df.index)

    if exact_co:
        # Priority 1: exact company name
        mask &= df["company_name"].isin(exact_co)
        if year_hits:
            mask &= df["year"].isin(year_hits)

    elif sector_hits or country_hits:
        # Priority 2: sector / country filters
        if sector_hits:
            mask &= df["primary_industry"].isin(sector_hits)
        if country_hits:
            mask &= df["hq_country"].isin(country_hits)
        if year_hits:
            mask &= df["year"].isin(year_hits)

    elif year_hits:
        # Priority 3: year only → top-k by ESG for that year
        mask &= df["year"].isin(year_hits)

    else:
        # Priority 4: word-level company match (last resort)
        word_co = _word_company_hits(df, q_lower)
        if not word_co:
            return ""
        mask &= df["company_name"].isin(word_co)

    subset = df[mask].copy()
    if subset.empty:
        return ""

    subset = subset.sort_values("esg_score_v3", ascending=False)
    rows = [_row_to_text(row) for _, row in subset.head(top_k).iterrows()]
    total = len(subset)
    header = f"[{total} matching record(s) — showing top {min(top_k, total)} by ESG score]"
    return header + "\n" + "\n".join(rows)
