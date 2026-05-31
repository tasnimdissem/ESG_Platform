"""
Web scraper for ESG news articles.
Sources:
  1. ESG Today (esgtoday.com)       — primary
  2. GreenBiz (greenbiz.com/news)   — secondary fallback
"""

import logging
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_TIMEOUT = 8  # seconds


def _get_soup(url: str) -> BeautifulSoup | None:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as e:
        logger.warning(f"[scraper] Failed to fetch {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Source 1 — ESG Today (esgtoday.com)
# ---------------------------------------------------------------------------

def _scrape_esgtoday(limit: int) -> list[dict[str, Any]]:
    """Scrape latest articles from esgtoday.com."""
    soup = _get_soup("https://www.esgtoday.com/")
    if soup is None:
        return []

    articles = []

    # ESG Today articles are in <article> or <h2>/<h3> tags inside the main feed
    for card in soup.select("article")[:limit * 2]:
        # Title + URL
        title_tag = card.find(["h2", "h3", "h4"])
        if not title_tag:
            continue
        link_tag = title_tag.find("a") or card.find("a")
        if not link_tag:
            continue

        title = title_tag.get_text(strip=True)
        href = link_tag.get("href", "")
        if not href.startswith("http"):
            href = "https://www.esgtoday.com" + href

        # Date
        time_tag = card.find("time")
        date_str = time_tag.get("datetime", "") if time_tag else ""
        if not date_str:
            date_str = datetime.utcnow().isoformat()

        # Excerpt
        excerpt_tag = card.find("p")
        excerpt = excerpt_tag.get_text(strip=True) if excerpt_tag else ""

        articles.append({
            "title": title,
            "url": href,
            "date": date_str,
            "source": "ESG Today",
            "region": "Global",
            "category": "ESG",
            "excerpt": excerpt,
        })

        if len(articles) >= limit:
            break

    logger.info(f"[scraper] ESG Today: {len(articles)} articles scraped")
    return articles


# ---------------------------------------------------------------------------
# Source 2 — GreenBiz (greenbiz.com/news)
# ---------------------------------------------------------------------------

def _scrape_greenbiz(limit: int) -> list[dict[str, Any]]:
    """Scrape latest articles from greenbiz.com/news."""
    soup = _get_soup("https://www.greenbiz.com/news")
    if soup is None:
        return []

    articles = []

    # GreenBiz wraps articles in <article> or divs with class containing "teaser"
    for card in soup.select("article, .views-row")[:limit * 2]:
        title_tag = card.find(["h2", "h3"])
        if not title_tag:
            continue
        link_tag = title_tag.find("a") or card.find("a")
        if not link_tag:
            continue

        title = title_tag.get_text(strip=True)
        href = link_tag.get("href", "")
        if not href.startswith("http"):
            href = "https://www.greenbiz.com" + href

        time_tag = card.find("time")
        date_str = time_tag.get("datetime", "") if time_tag else datetime.utcnow().isoformat()

        excerpt_tag = card.find("p")
        excerpt = excerpt_tag.get_text(strip=True) if excerpt_tag else ""

        articles.append({
            "title": title,
            "url": href,
            "date": date_str,
            "source": "GreenBiz",
            "region": "Global",
            "category": "ESG",
            "excerpt": excerpt,
        })

        if len(articles) >= limit:
            break

    logger.info(f"[scraper] GreenBiz: {len(articles)} articles scraped")
    return articles


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scrape_esg_news(limit: int = 8) -> list[dict[str, Any]]:
    """
    Scrape ESG news from multiple sources and return up to `limit` articles.
    Tries ESG Today first, falls back to GreenBiz if not enough results.
    Each article has: id, title, url, date, source, region, category, excerpt.
    """
    results: list[dict[str, Any]] = []

    results.extend(_scrape_esgtoday(limit))

    if len(results) < limit:
        needed = limit - len(results)
        results.extend(_scrape_greenbiz(needed))

    # Deduplicate by URL
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in results:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    # Add sequential IDs
    for idx, item in enumerate(unique[:limit], start=1):
        item["id"] = idx

    logger.info(f"[scraper] Total scraped: {len(unique[:limit])} articles")
    return unique[:limit]
