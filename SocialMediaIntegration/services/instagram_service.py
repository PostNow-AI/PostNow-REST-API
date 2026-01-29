"""
Instagram Graph API Service
Handles all interactions with Instagram Graph API for fetching user data and insights.
"""

import time
from datetime import datetime

import requests


class InstagramGraphService:
    """
    Service for interacting with Instagram Graph API.
    Handles profile data, insights, media, with retry logic and rate limiting.
    """

    def __init__(self):
        self.graph_api_url = 'https://graph.instagram.com'
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def get_user_profile(self, instagram_user_id, access_token):
        """
        Fetch Instagram user profile information.

        Args:
            instagram_user_id: Instagram user ID
            access_token: Valid access token

        Returns:
            dict with profile data (username, followers, media_count, etc.)
        """
        url = f"{self.graph_api_url}/{instagram_user_id}"

        fields = [
            'id',
            'username',
            'account_type',
            'media_count',
            'profile_picture_url',
        ]

        params = {
            'fields': ','.join(fields),
            'access_token': access_token,
        }

        data = self._make_request('GET', url, params=params)

        # Get followers count separately (requires different endpoint)
        followers_data = self.get_followers_count(
            instagram_user_id, access_token)
        data['followers_count'] = followers_data.get('followers_count', 0)
        data['following_count'] = followers_data.get('follows_count', 0)

        return data

    def get_followers_count(self, instagram_user_id, access_token):
        """
        Get followers and following count.

        Args:
            instagram_user_id: Instagram user ID
            access_token: Valid access token

        Returns:
            dict with followers_count and follows_count
        """
        url = f"{self.graph_api_url}/{instagram_user_id}"

        params = {
            'fields': 'followers_count,follows_count',
            'access_token': access_token,
        }

        return self._make_request('GET', url, params=params)

    def get_account_insights(self, instagram_user_id, access_token, period='day', metrics=None):
        """
        Fetch Instagram account-level insights.

        Args:
            instagram_user_id: Instagram user ID
            access_token: Valid access token
            period: 'day', 'week', or 'days_28'
            metrics: List of metric names (default: impressions, reach, profile_views)

        Returns:
            dict with insights data
        """
        if metrics is None:
            metrics = ['impressions', 'reach', 'profile_views']

        url = f"{self.graph_api_url}/{instagram_user_id}/insights"

        params = {
            'metric': ','.join(metrics),
            'period': period,
            'access_token': access_token,
        }

        data = self._make_request('GET', url, params=params)

        # Transform data into easier format
        insights = {}
        for item in data.get('data', []):
            metric_name = item.get('name')
            values = item.get('values', [])
            if values:
                # Get the most recent value
                insights[metric_name] = values[-1].get('value', 0)

        return insights

    def get_media_insights(self, media_id, access_token, metrics=None):
        """
        Fetch insights for a specific media post.

        Args:
            media_id: Instagram media ID
            access_token: Valid access token
            metrics: List of metric names (default: engagement, impressions, reach)

        Returns:
            dict with media insights
        """
        if metrics is None:
            metrics = ['engagement', 'impressions', 'reach', 'saved']

        url = f"{self.graph_api_url}/{media_id}/insights"

        params = {
            'metric': ','.join(metrics),
            'access_token': access_token,
        }

        data = self._make_request('GET', url, params=params)

        # Transform data
        insights = {}
        for item in data.get('data', []):
            metric_name = item.get('name')
            values = item.get('values', [])
            if values:
                insights[metric_name] = values[0].get('value', 0)

        return insights

    def get_recent_media(self, instagram_user_id, access_token, limit=25):
        """
        Fetch recent media posts.

        Args:
            instagram_user_id: Instagram user ID
            access_token: Valid access token
            limit: Number of posts to fetch (max 100)

        Returns:
            list of media objects
        """
        url = f"{self.graph_api_url}/{instagram_user_id}/media"

        fields = [
            'id',
            'caption',
            'media_type',
            'media_url',
            'permalink',
            'timestamp',
            'like_count',
            'comments_count',
        ]

        params = {
            'fields': ','.join(fields),
            'limit': min(limit, 100),
            'access_token': access_token,
        }

        data = self._make_request('GET', url, params=params)
        return data.get('data', [])

    def get_best_posting_times(self, instagram_user_id, access_token):
        """
        Analyze posting times and engagement to suggest best times to post.
        This is a custom analysis based on historical media data.

        Args:
            instagram_user_id: Instagram user ID
            access_token: Valid access token

        Returns:
            dict with best posting hours and days
        """
        # Get recent media
        media_list = self.get_recent_media(
            instagram_user_id, access_token, limit=50)

        # Analyze engagement by hour and day
        hour_engagement = {}
        day_engagement = {}

        for media in media_list:
            timestamp = media.get('timestamp')
            if not timestamp:
                continue

            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            day = dt.strftime('%A')

            # Calculate engagement (likes + comments)
            engagement = media.get('like_count', 0) + \
                (media.get('comments_count', 0) * 2)

            # Aggregate by hour
            if hour not in hour_engagement:
                hour_engagement[hour] = {'total': 0, 'count': 0}
            hour_engagement[hour]['total'] += engagement
            hour_engagement[hour]['count'] += 1

            # Aggregate by day
            if day not in day_engagement:
                day_engagement[day] = {'total': 0, 'count': 0}
            day_engagement[day]['total'] += engagement
            day_engagement[day]['count'] += 1

        # Calculate averages
        best_hours = []
        for hour, data in hour_engagement.items():
            avg = data['total'] / data['count'] if data['count'] > 0 else 0
            best_hours.append({'hour': hour, 'avg_engagement': avg})

        best_hours.sort(key=lambda x: x['avg_engagement'], reverse=True)

        best_days = []
        for day, data in day_engagement.items():
            avg = data['total'] / data['count'] if data['count'] > 0 else 0
            best_days.append({'day': day, 'avg_engagement': avg})

        best_days.sort(key=lambda x: x['avg_engagement'], reverse=True)

        return {
            'best_hours': best_hours[:3],  # Top 3 hours
            'best_days': best_days[:3],    # Top 3 days
        }

    def _make_request(self, method, url, params=None, data=None, retry_count=0):
        """
        Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            data: Request body data
            retry_count: Current retry attempt

        Returns:
            Response JSON data

        Raises:
            ValueError: If request fails after all retries
        """
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=15
            )

            # Check for rate limiting
            if response.status_code == 429:
                if retry_count < self.max_retries:
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** retry_count)
                    time.sleep(wait_time)
                    return self._make_request(method, url, params, data, retry_count + 1)
                else:
                    raise ValueError(
                        "Muitas requisições ao Instagram. Por favor, aguarde alguns minutos e tente novamente."
                    )

            response.raise_for_status()
            response_data = response.json()

            # Check for API errors
            if 'error' in response_data:
                error = response_data['error']
                error_message = error.get('message', 'Erro desconhecido')
                error_code = error.get('code', 'unknown')

                # Handle specific error codes
                if error_code == 190:  # Invalid token
                    raise ValueError(
                        "Token do Instagram inválido. Reconecte sua conta.")
                elif error_code == 10:  # Permission error
                    raise ValueError(
                        "Permissões insuficientes. Verifique se sua conta é Business.")
                else:
                    raise ValueError(
                        f"Erro da API do Instagram: {error_message}")

            return response_data

        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self._make_request(method, url, params, data, retry_count + 1)
            else:
                raise ValueError(
                    "Timeout ao conectar com Instagram. Tente novamente.")

        except requests.exceptions.RequestException as e:
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self._make_request(method, url, params, data, retry_count + 1)
            else:
                raise ValueError(f"Erro ao conectar com Instagram: {str(e)}")
