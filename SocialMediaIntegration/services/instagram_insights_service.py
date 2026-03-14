"""
Instagram Insights Service

Fetches engagement metrics for published media via Instagram Graph API.
API: GET /{media_id}/insights?metric=engagement,impressions,reach,saved,shares
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.instagram.com"
GRAPH_API_VERSION = "v21.0"


@dataclass
class InsightsResult:
    success: bool
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    saves: int = 0
    shares: int = 0
    engagement_rate: float = 0.0
    raw_data: dict = field(default_factory=dict)
    error_message: Optional[str] = None


class InstagramInsightsService:

    def __init__(self):
        self.api_base = f"{GRAPH_API_BASE}/{GRAPH_API_VERSION}"

    def fetch_media_insights(self, media_id: str, access_token: str) -> InsightsResult:
        """Fetch insights for a published Instagram media."""
        url = f"{self.api_base}/{media_id}/insights"
        params = {
            "metric": "impressions,reach,saved,shares",
            "access_token": access_token,
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                logger.warning("Instagram API rate limit hit for media %s", media_id)
                return InsightsResult(
                    success=False,
                    error_message="Rate limit exceeded",
                )

            if response.status_code != 200:
                error_data = response.json().get("error", {})
                msg = error_data.get("message", response.text[:200])
                logger.warning(
                    "Instagram insights error for media %s: %s", media_id, msg
                )
                return InsightsResult(success=False, error_message=msg)

            data = response.json()
            metrics = self._parse_metrics(data)

            impressions = metrics.get("impressions", 0)
            reach = metrics.get("reach", 0)
            saves = metrics.get("saved", 0)
            shares = metrics.get("shares", 0)
            engagement = saves + shares
            engagement_rate = (engagement / reach * 100) if reach > 0 else 0.0

            return InsightsResult(
                success=True,
                impressions=impressions,
                reach=reach,
                engagement=engagement,
                saves=saves,
                shares=shares,
                engagement_rate=engagement_rate,
                raw_data=data,
            )

        except requests.RequestException as e:
            logger.error("Network error fetching insights for %s: %s", media_id, e)
            return InsightsResult(success=False, error_message=str(e))

    def _parse_metrics(self, data: dict) -> dict:
        """Parse Instagram insights API response into flat dict."""
        metrics = {}
        for item in data.get("data", []):
            name = item.get("name")
            values = item.get("values", [])
            if values:
                metrics[name] = values[0].get("value", 0)
        return metrics
