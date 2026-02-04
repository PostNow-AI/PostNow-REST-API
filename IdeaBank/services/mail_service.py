import base64
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import requests
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
        # Create v3 client for statistics API
        self.mailjet_client_v3 = Client(
            auth=(self.api_key, self.secret_key), version='v3')

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

                for i, attachment in enumerate(attachments):

                    attachment_data = self._process_attachment(attachment, i)
                    if attachment_data:
                        inline_attachment = {
                            "ContentType": attachment_data['content_type'],
                            "Filename": attachment_data['filename'],
                            "ContentID": attachment_data['content_id'],
                            "Base64Content": attachment_data['base64_content']
                        }
                        logger.info(
                            f"Adding inline attachment: {attachment_data['filename']} with ContentID: {attachment_data['content_id']}")
                        message_data["InlinedAttachments"].append(
                            inline_attachment)
                    else:
                        logger.error(
                            f"Failed to process attachment {i+1}: {attachment['url']}")

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

    def get_messages_statistics(self, start_date: datetime, end_date: datetime, exclude_emails: List[str] = None) -> Dict[str, Any]:
        """
        Get message statistics from Mailjet API for a date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            exclude_emails: List of email addresses to exclude (e.g., admin emails)
            
        Returns:
            Dict with sent_messages and opened_messages lists, each containing message data
        """
        try:
            exclude_emails = exclude_emails or []
            exclude_emails_lower = [email.lower().strip() for email in exclude_emails]
            
            # Convert datetime to Unix timestamp (Mailjet expects this)
            from_ts = int(start_date.timestamp())
            to_ts = int(end_date.timestamp())
            
            sent_messages = []
            opened_messages = []
            
            # Fetch messages in batches (Mailjet API limit is 1000 per request)
            limit = 1000
            offset = 0
            
            while True:
                # Query parameters for sent messages
                filters = {
                    'FromTS': from_ts,
                    'ToTS': to_ts,
                    'Limit': limit,
                    'Offset': offset,
                }
                
                result = self.mailjet_client_v3.message.get(filters=filters)
                
                if result.status_code != 200:
                    logger.error(f"Mailjet API error fetching messages: Status {result.status_code}")
                    break
                
                data = result.json()
                messages = data.get('Data', [])
                
                if not messages:
                    break
                
                for msg in messages:
                    recipient_email = msg.get('ContactAlt', '').lower().strip()
                    
                    # Skip if email is in exclude list
                    if recipient_email in exclude_emails_lower:
                        continue
                    
                    # Add to sent messages
                    sent_messages.append({
                        'MessageID': msg.get('ID'),
                        'Email': recipient_email,
                        'ArrivedAt': msg.get('ArrivedAt'),
                        'Status': msg.get('Status'),
                    })
                    
                    # Check if message was opened (OpenedCount > 0)
                    if msg.get('OpenedCount', 0) > 0:
                        opened_messages.append({
                            'MessageID': msg.get('ID'),
                            'Email': recipient_email,
                            'ArrivedAt': msg.get('ArrivedAt'),
                            'OpenedAt': msg.get('OpenedAt'),
                        })
                
                # Check if we've fetched all messages
                if len(messages) < limit:
                    break
                
                offset += limit
            
            return {
                'sent_messages': sent_messages,
                'opened_messages': opened_messages,
                'total_sent': len(sent_messages),
                'total_opened': len(opened_messages),
            }
            
        except Exception as e:
            logger.error(f"Error fetching message statistics from Mailjet: {str(e)}")
            return {
                'sent_messages': [],
                'opened_messages': [],
                'total_sent': 0,
                'total_opened': 0,
                'error': str(e)
            }

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
            # Check if it's already a data URL (base64 encoded image)
            if image_url.startswith('data:image/'):
                logger.info(
                    f"Processing data URL for attachment: {attachment.get('filename', 'unknown')} (length: {len(image_url)})")
                try:
                    # Parse data URL: data:image/png;base64,iVBORw0KGgo...
                    header, base64_data = image_url.split(',', 1)
                    content_type = header.split(';')[0].replace('data:', '')
                    logger.info(
                        f"Extracted content_type: {content_type}, base64 length: {len(base64_data)}")

                    # Validate base64 content
                    # This will raise exception if invalid
                    decoded_content = base64.b64decode(base64_data)
                    logger.info(
                        f"Successfully decoded base64 content, decoded length: {len(decoded_content)}")

                    # Use provided content_id or generate one
                    content_id = attachment.get('content_id')
                    if not content_id:
                        # Extract post ID from filename to create proper content ID
                        filename = attachment.get('filename', f'image_{index}')
                        if 'post_image_' in filename:
                            post_id = filename.replace(
                                'post_image_', '').replace('.jpg', '')
                            content_id = f"image_post_{post_id}"
                        else:
                            content_id = f"image_{index}_{hash(image_url) % 10000}"

                    logger.info(
                        f"Successfully processed attachment: filename={attachment['filename']}, content_id={content_id}, content_type={content_type}")
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

                # Add headers to mimic a browser request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                response = requests.get(image_url, timeout=30, headers=headers)

                if response.status_code == 200:
                    # Get actual content type from response headers
                    actual_content_type = response.headers.get(
                        'content-type', attachment['content_type'])

                    # Validate that we got image content
                    if not actual_content_type.startswith('image/'):
                        return None

                    # Convert image to base64
                    base64_content = base64.b64encode(
                        response.content).decode('utf-8')

                    # Use provided content_id or generate one
                    content_id = attachment.get('content_id')
                    if not content_id:
                        # Extract post ID from filename to create proper content ID
                        filename = attachment.get('filename', f'image_{index}')
                        if 'post_image_' in filename:
                            post_id = filename.replace(
                                'post_image_', '').replace('.jpg', '')
                            content_id = f"image_post_{post_id}"
                        else:
                            content_id = f"image_{index}_{hash(attachment['url']) % 10000}"

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
