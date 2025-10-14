import logging
import os
import requests
import base64
from urllib.parse import urlparse

from mailjet_rest import Client

logger = logging.getLogger(__name__)


class MailService():
    def __init__(self):
        self.api_key = os.getenv("MJ_APIKEY_PUBLIC")
        self.secret_key = os.getenv("MJ_APIKEY_PRIVATE")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_name = os.getenv("SENDER_NAME")
        self.base_url = "https://api.mailjet.com/v3.1/send"
        self.mailjet_client = Client(
            auth=(self.api_key, self.secret_key), version='v3.1')

    def send_email(self, recipient_email, subject, html_content, attachments=None) -> tuple:
        """
        Send email with optional attachments.

        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            html_content: HTML content of the email
            attachments: List of dict with 'url', 'filename', and 'content_type' keys
        """
        try:
            message_data = {
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

            # Add attachments if provided
            if attachments:
                message_data["InlinedAttachments"] = []
                logger.info(
                    f"Processing {len(attachments)} attachments for email")

                for i, attachment in enumerate(attachments):
                    logger.info(
                        f"Processing attachment {i+1}: {attachment['url']}")
                    attachment_data = self._process_attachment(attachment, i)
                    if attachment_data:
                        inline_attachment = {
                            "ContentType": attachment_data['content_type'],
                            "Filename": attachment_data['filename'],
                            "ContentID": attachment_data['content_id'],
                            "Base64Content": attachment_data['base64_content']
                        }
                        message_data["InlinedAttachments"].append(
                            inline_attachment)
                        logger.info(
                            f"Successfully added inline attachment with ContentID: {attachment_data['content_id']}")
                    else:
                        logger.error(
                            f"Failed to process attachment {i+1}: {attachment['url']}")

                logger.info(
                    f"Total inline attachments added: {len(message_data['InlinedAttachments'])}")

            data = {
                'Messages': [message_data]
            }

            result = self.mailjet_client.send.create(data=data)

            if result.status_code == 200:
                logger.info(
                    f"Email enviado com sucesso para {recipient_email}")
                if attachments:
                    logger.info(
                        f"Email incluiu {len(attachments)} imagens anexadas")
            else:
                logger.error(
                    f"Mailjet API error: Status {result.status_code}, Response: {result.json()}")

            return result.status_code, result.json()
        except Exception as e:
            logger.error(
                f"Erro ao enviar email para {recipient_email}: {str(e)}")
            return None, {'error': str(e)}

    def _process_attachment(self, attachment, index=0):
        """
        Process attachment by downloading image and converting to base64.

        Args:
            attachment: Dict with 'url', 'filename', 'content_type' keys
            index: Index for generating unique content ID

        Returns:
            Dict with processed attachment data or None if failed
        """
        try:
            image_url = attachment['url']
            logger.info(f"Processing attachment: {image_url[:100]}...")

            # Check if it's already a data URL (base64 encoded image)
            if image_url.startswith('data:image/'):
                logger.info(
                    "Image is already a data URL, extracting base64 content")
                try:
                    # Parse data URL: data:image/png;base64,iVBORw0KGgo...
                    header, base64_data = image_url.split(',', 1)
                    content_type = header.split(';')[0].replace('data:', '')

                    # Validate base64 content
                    # This will raise exception if invalid
                    base64.b64decode(base64_data)

                    logger.info(
                        f"Data URL parsed successfully: {content_type}, base64 length: {len(base64_data)}")

                    # Extract post ID from filename to create proper content ID
                    filename = attachment.get('filename', f'image_{index}')
                    if 'post_image_' in filename:
                        post_id = filename.replace(
                            'post_image_', '').replace('.jpg', '')
                        content_id = f"image_post_{post_id}"
                    else:
                        content_id = f"image_{index}_{hash(image_url) % 10000}"

                    logger.info(f"Generated content ID: {content_id}")

                    return {
                        'base64_content': base64_data,
                        'content_type': content_type,
                        'filename': attachment['filename'],
                        'content_id': content_id
                    }
                except Exception as e:
                    logger.error(f"Failed to parse data URL: {str(e)}")
                    return None

            # Handle regular HTTP/HTTPS URLs
            elif image_url.startswith(('http://', 'https://')):
                logger.info("Image is a regular URL, downloading...")

                # Add headers to mimic a browser request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                response = requests.get(image_url, timeout=30, headers=headers)
                logger.info(
                    f"Image download response: {response.status_code} for {image_url[:100]}")

                if response.status_code == 200:
                    # Get actual content type from response headers
                    actual_content_type = response.headers.get(
                        'content-type', attachment['content_type'])
                    logger.info(
                        f"Image content type: {actual_content_type}, size: {len(response.content)} bytes")

                    # Validate that we got image content
                    if not actual_content_type.startswith('image/'):
                        logger.error(
                            f"URL did not return an image: {actual_content_type}")
                        return None

                    # Convert image to base64
                    base64_content = base64.b64encode(
                        response.content).decode('utf-8')
                    logger.info(
                        f"Base64 content length: {len(base64_content)} characters")

                    # Extract post ID from filename to create proper content ID
                    filename = attachment.get('filename', f'image_{index}')
                    if 'post_image_' in filename:
                        post_id = filename.replace(
                            'post_image_', '').replace('.jpg', '')
                        content_id = f"image_post_{post_id}"
                    else:
                        content_id = f"image_{index}_{hash(attachment['url']) % 10000}"

                    logger.info(f"Generated content ID: {content_id}")

                    return {
                        'base64_content': base64_content,
                        'content_type': actual_content_type,
                        'filename': attachment['filename'],
                        'content_id': content_id
                    }
                else:
                    logger.error(
                        f"Failed to download image: {image_url} - Status: {response.status_code}, Response: {response.text[:200]}")
                    return None
            else:
                logger.error(
                    f"Unsupported image URL format: {image_url[:100]}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Network error downloading image {attachment['url']}: {str(e)}")
            return None
        except Exception as e:
            logger.error(
                f"Error processing attachment {attachment['url']}: {str(e)}")
            return None
