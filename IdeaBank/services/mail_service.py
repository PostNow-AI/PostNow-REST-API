"""
Mail Service for handling email operations.
"""

import base64
import logging
import os
from typing import Dict, List, Optional, Tuple

import requests
from IdeaBank.utils.mail_templates.logo_base64 import logo
from mailjet_rest import Client

logger = logging.getLogger(__name__)


class MailService:
    """Service for handling email operations using Mailjet."""

    def __init__(self):
        self.api_key = os.getenv("MJ_APIKEY_PUBLIC")
        self.secret_key = os.getenv("MJ_APIKEY_PRIVATE")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_name = os.getenv("SENDER_NAME")
        self.base_url = "https://api.mailjet.com/v3.1/send"
        self.mailjet_client = Client(
            auth=(self.api_key, self.secret_key), version='v3.1')

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate that all required configuration is present."""
        required_configs = [
            ('MJ_APIKEY_PUBLIC', self.api_key),
            ('MJ_APIKEY_PRIVATE', self.secret_key),
            ('SENDER_EMAIL', self.sender_email),
            ('SENDER_NAME', self.sender_name)
        ]

        missing_configs = [name for name,
                           value in required_configs if not value]
        if missing_configs:
            raise ValueError(
                f"Missing required Mailjet configuration: {', '.join(missing_configs)}")

    def send_email(self, recipient_email: str, subject: str, html_content: str,
                   attachments: Optional[List[Dict]] = None) -> Tuple[Optional[int], Dict]:
        """
        Send email with optional attachments.

        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            html_content: HTML content of the email
            attachments: List of dict with 'url', 'filename', 'content_type', 'content_id' keys

        Returns:
            Tuple of (status_code, response_dict)
        """
        try:
            # Prepare message data
            message_data = self._prepare_message_data(
                recipient_email, subject, html_content)

            # Process attachments if provided
            if attachments:
                attachments_with_logo = attachments + \
                    [self._get_logo_attachment()]
                inline_attachments = self._process_attachments(
                    attachments_with_logo)
                if inline_attachments:
                    message_data["InlinedAttachments"] = inline_attachments

            # Send email
            data = {'Messages': [message_data]}
            result = self.mailjet_client.send.create(data=data)

            # Log result
            self._log_email_result(result, recipient_email, attachments)

            return result.status_code, result.json()

        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {str(e)}")
            return None, {'error': str(e)}

    def _prepare_message_data(self, recipient_email: str, subject: str, html_content: str) -> Dict:
        """Prepare the basic message data structure."""
        return {
            "From": {
                "Email": self.sender_email,
                "Name": self.sender_name
            },
            "To": [
                {
                    "Email": recipient_email,
                    "Name": recipient_email
                }
            ],
            "Subject": subject,
            "HTMLPart": html_content
        }

    def _get_logo_attachment(self) -> Dict:
        """Get the PostNow logo attachment data."""
        return {
            'url': logo,
            'filename': 'postnow_logo.svg',
            'content_type': 'image/png',
            'content_id': 'postnow_logo'
        }

    def _process_attachments(self, attachments: List[Dict]) -> List[Dict]:
        """Process all attachments and return inline attachment data."""
        inline_attachments = []

        for i, attachment in enumerate(attachments):
            attachment_data = self._process_single_attachment(attachment, i)
            if attachment_data:
                inline_attachment = {
                    "ContentType": attachment_data['content_type'],
                    "Filename": attachment_data['filename'],
                    "ContentID": attachment_data['content_id'],
                    "Base64Content": attachment_data['base64_content']
                }
                inline_attachments.append(inline_attachment)
            else:
                logger.error(
                    f"Failed to process attachment {i+1}: {attachment.get('url', 'unknown')}")

        return inline_attachments

    def _process_single_attachment(self, attachment: Dict, index: int = 0) -> Optional[Dict]:
        """
        Process a single attachment by downloading and converting to base64.

        Args:
            attachment: Dict with 'url', 'filename', 'content_type', 'content_id' keys
            index: Index for generating unique content ID

        Returns:
            Dict with processed attachment data or None if failed
        """
        try:
            image_url = attachment['url']

            # Handle data URLs (base64 encoded images)
            if image_url.startswith('data:image/'):
                return self._process_data_url_attachment(attachment, index)

            # Handle regular HTTP/HTTPS URLs
            elif image_url.startswith(('http://', 'https://')):
                return self._process_http_attachment(attachment, index)

            else:
                logger.error(
                    f"Unsupported image URL format: {image_url[:100]}")
                return None

        except Exception as e:
            logger.error(
                f"Error processing attachment {attachment.get('url', 'unknown')}: {str(e)}")
            return None

    def _process_data_url_attachment(self, attachment: Dict, index: int) -> Optional[Dict]:
        """Process a data URL attachment (base64 encoded)."""
        try:
            image_url = attachment['url']
            logger.info(
                f"Processing data URL for attachment: {attachment.get('filename', 'unknown')}")

            # Parse data URL: data:image/png;base64,iVBORw0KGgo...
            header, base64_data = image_url.split(',', 1)
            content_type = header.split(';')[0].replace('data:', '')

            # Validate base64 content
            decoded_content = base64.b64decode(base64_data)
            logger.info(
                f"Successfully decoded base64 content, length: {len(decoded_content)}")

            # Generate content ID
            content_id = attachment.get(
                'content_id') or self._generate_content_id(attachment, index)

            return {
                'base64_content': base64_data,
                'content_type': content_type,
                'filename': attachment['filename'],
                'content_id': content_id
            }

        except Exception as e:
            logger.error(f"Failed to parse data URL: {str(e)}")
            return None

    def _process_http_attachment(self, attachment: Dict, index: int) -> Optional[Dict]:
        """Process an HTTP/HTTPS URL attachment."""
        try:
            image_url = attachment['url']

            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(image_url, timeout=30, headers=headers)

            if response.status_code != 200:
                logger.error(
                    f"Failed to download image: {image_url} - Status: {response.status_code}")
                return None

            # Validate content type
            actual_content_type = response.headers.get(
                'content-type', attachment['content_type'])
            if not actual_content_type.startswith('image/'):
                logger.error(
                    f"Invalid content type for image: {actual_content_type}")
                return None

            # Convert to base64
            base64_content = base64.b64encode(response.content).decode('utf-8')

            # Generate content ID
            content_id = attachment.get(
                'content_id') or self._generate_content_id(attachment, index)

            return {
                'base64_content': base64_content,
                'content_type': actual_content_type,
                'filename': attachment['filename'],
                'content_id': content_id
            }

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Network error downloading image {attachment['url']}: {str(e)}")
            return None

    def _generate_content_id(self, attachment: Dict, index: int) -> str:
        """Generate a unique content ID for an attachment."""
        filename = attachment.get('filename', f'image_{index}')

        # Try to extract post ID from filename
        if 'post_image_' in filename:
            post_id = filename.replace('post_image_', '').replace(
                '.jpg', '').replace('.png', '')
            return f"image_post_{post_id}"
        else:
            # Use hash of URL for uniqueness
            return f"image_{index}_{hash(attachment['url']) % 10000}"

    def _log_email_result(self, result, recipient_email: str, attachments: Optional[List[Dict]]) -> None:
        """Log the result of email sending."""
        if result.status_code == 200:
            logger.info(f"Email sent successfully to {recipient_email}")
            if attachments:
                logger.info(f"Email included {len(attachments)} attachments")
        else:
            logger.error(
                f"Mailjet API error: Status {result.status_code}, Response: {result.json()}")
