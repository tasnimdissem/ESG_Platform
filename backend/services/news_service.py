from __future__ import annotations

from typing import Any


def fetch_esg_news(limit: int = 8) -> list[dict[str, Any]]:
    sample_news = [
        {
            'id': 1,
            'title': 'New EU climate disclosure guidance released',
            'source': 'ESG Monitor',
            'region': 'Europe',
            'category': 'Regulation',
            'date': '2026-04-15',
        },
        {
            'id': 2,
            'title': 'Green finance inflows rise across emerging markets',
            'source': 'Sustainable Finance Daily',
            'region': 'Global',
            'category': 'Finance',
            'date': '2026-04-14',
        },
        {
            'id': 3,
            'title': 'New social reporting standard enters into force',
            'source': 'Governance Insights',
            'region': 'Americas',
            'category': 'Governance',
            'date': '2026-04-13',
        },
        {
            'id': 4,
            'title': 'Supply chain transparency remains a board-level priority',
            'source': 'Sustainability Review',
            'region': 'Global',
            'category': 'Supply Chain',
            'date': '2026-04-12',
        },
    ]
    return sample_news[: max(1, limit)]
