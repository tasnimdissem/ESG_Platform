import requests
from typing import Any
import os
import logging
from dotenv import load_dotenv

from backend.services.news_scraper import scrape_esg_news

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def fetch_esg_news(limit: int = 8) -> list[dict[str, Any]]:
    url = "https://newsapi.org/v2/everything"

    logger.debug(f"NEWS_API_KEY loaded: {bool(API_KEY)}")

    if not API_KEY:
        logger.warning("NEWS_API_KEY not set — falling back to web scraping")
        return scrape_esg_news(limit)

    params = {
"q": "\"ESG score\" OR \"ESG rating\" OR \"sustainable finance\" OR \"green bond\" OR \"carbon offset\"",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": API_KEY,
    }

    try:
        logger.debug(f"Fetching news from {url} with params: {params}")
        response = requests.get(url, params=params, timeout=5)
        logger.debug(f"Response status code: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()

        logger.debug(f"API Response: {data}")
        articles = data.get("articles", [])
        logger.debug(f"Number of articles fetched: {len(articles)}")

        news = []
        for i, article in enumerate(articles, start=1):
            news.append({
                "id": i,
                "title": article.get("title"),
                "source": article.get("source", {}).get("name"),
                "region": "Global",
                "category": "ESG",
                "date": article.get("publishedAt"),
                "url": article.get("url"),
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