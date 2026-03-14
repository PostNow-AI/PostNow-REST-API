"""Testes para InstagramInsightsService."""

from unittest.mock import Mock, patch

from SocialMediaIntegration.services.instagram_insights_service import (
    InstagramInsightsService,
)


class TestInstagramInsightsService:

    def setup_method(self):
        self.service = InstagramInsightsService()

    @patch("SocialMediaIntegration.services.instagram_insights_service.requests")
    def test_fetch_metrics_success(self, mock_requests):
        import requests as real_requests
        mock_requests.RequestException = real_requests.RequestException
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"name": "impressions", "values": [{"value": 1000}]},
                {"name": "reach", "values": [{"value": 800}]},
                {"name": "saved", "values": [{"value": 50}]},
                {"name": "shares", "values": [{"value": 30}]},
            ]
        }
        mock_requests.get.return_value = mock_response

        result = self.service.fetch_media_insights("12345", "token")

        assert result.success is True
        assert result.impressions == 1000
        assert result.reach == 800
        assert result.saves == 50
        assert result.shares == 30
        assert result.engagement == 80  # saves + shares
        assert result.engagement_rate == 10.0  # 80/800*100

    @patch("SocialMediaIntegration.services.instagram_insights_service.requests")
    def test_fetch_metrics_rate_limit(self, mock_requests):
        import requests as real_requests
        mock_requests.RequestException = real_requests.RequestException

        mock_response = Mock()
        mock_response.status_code = 429
        mock_requests.get.return_value = mock_response

        result = self.service.fetch_media_insights("12345", "token")

        assert result.success is False
        assert "Rate limit" in result.error_message

    @patch("SocialMediaIntegration.services.instagram_insights_service.requests")
    def test_fetch_metrics_api_error(self, mock_requests):
        import requests as real_requests
        mock_requests.RequestException = real_requests.RequestException

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.json.return_value = {
            "error": {"message": "Invalid media ID"}
        }
        mock_requests.get.return_value = mock_response

        result = self.service.fetch_media_insights("bad_id", "token")

        assert result.success is False
        assert "Invalid media ID" in result.error_message

    @patch("SocialMediaIntegration.services.instagram_insights_service.requests")
    def test_fetch_metrics_network_error(self, mock_requests):
        import requests
        mock_requests.get.side_effect = requests.RequestException("timeout")
        mock_requests.RequestException = requests.RequestException

        result = self.service.fetch_media_insights("12345", "token")

        assert result.success is False
        assert "timeout" in result.error_message

    @patch("SocialMediaIntegration.services.instagram_insights_service.requests")
    def test_engagement_rate_zero_reach(self, mock_requests):
        import requests as real_requests
        mock_requests.RequestException = real_requests.RequestException
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"name": "impressions", "values": [{"value": 0}]},
                {"name": "reach", "values": [{"value": 0}]},
                {"name": "saved", "values": [{"value": 0}]},
                {"name": "shares", "values": [{"value": 0}]},
            ]
        }
        mock_requests.get.return_value = mock_response

        result = self.service.fetch_media_insights("12345", "token")

        assert result.success is True
        assert result.engagement_rate == 0.0
