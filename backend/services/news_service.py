import requests
from typing import Any
import os
import logging
from dotenv import load_dotenv

from backend.services.news_scraper import scrape_esg_news

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

_ENV_KEYWORDS = {"climate", "carbon", "emission", "renewable", "energy", "environment", "green", "biodiversity", "water", "pollution", "deforestation", "net zero", "ghg"}
_SOC_KEYWORDS = {"social", "diversity", "inclusion", "human rights", "labor", "employee", "community", "gender", "equity", "health", "safety", "workforce"}
_GOV_KEYWORDS = {"governance", "board", "executive", "compliance", "transparency", "audit", "shareholder", "regulation", "ethics", "corruption", "disclosure"}


def _classify_category(text: str) -> str:
    """Classify an article into E, S, G or ESG based on keyword matching."""
    lower = text.lower()
    scores = {
        "Environnement": sum(1 for k in _ENV_KEYWORDS if k in lower),
        "Social": sum(1 for k in _SOC_KEYWORDS if k in lower),
        "Gouvernance": sum(1 for k in _GOV_KEYWORDS if k in lower),
    }
    best_cat, best_score = max(scores.items(), key=lambda x: x[1])
    return best_cat if best_score > 0 else "ESG"


def fetch_esg_news(limit: int = 8) -> list[dict[str, Any]]:
    url = "https://newsapi.org/v2/everything"

    logger.debug(f"NEWS_API_KEY loaded: {bool(API_KEY)}")

    if not API_KEY:
        logger.warning("NEWS_API_KEY not set — falling back to web scraping")
        return scrape_esg_news(limit)

    params = {
        "q": (
            '"ESG score" OR "ESG rating" OR "sustainable finance" OR "green bond" '
            'OR "carbon offset" OR "climate risk" OR "social impact" OR "corporate governance"'
        ),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": API_KEY,
    }

    try:
        logger.debug(f"Fetching news from {url}")
        response = requests.get(url, params=params, timeout=5)
        logger.debug(f"Response status code: {response.status_code}")

        response.raise_for_status()
        data = response.json()

        articles = data.get("articles", [])
        logger.debug(f"Number of articles fetched: {len(articles)}")

        news = []
        for i, article in enumerate(articles, start=1):
            title = article.get("title") or ""
            description = article.get("description") or ""
            combined = f"{title} {description}"
            news.append({
                "id": i,
                "title": title,
                "description": description,
                "source": article.get("source", {}).get("name", ""),
                "region": "Global",
                "category": _classify_category(combined),
                "date": article.get("publishedAt", ""),
                "url": article.get("url", ""),
            })

        logger.debug(f"Returning {len(news)} formatted news items")
        if not news:
            logger.warning("News API returned 0 articles — falling back to web scraping")
            return scrape_esg_news(limit)
        return news

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching news: {e} — falling back to web scraping")
        return scrape_esg_news(limit)
    except Exception as e:
        logger.error(f"Erreur News API: {e}", exc_info=True)
        return scrape_esg_news(limit)