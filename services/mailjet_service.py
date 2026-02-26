import base64
import logging
import os

from asgiref.sync import sync_to_async
from AuditSystem.services import AuditService
from mailjet_rest import Client

from .s3_sevice import S3Service

logger = logging.getLogger(__name__)


class MailjetService:
    def __init__(self):
        self.api_key = os.getenv("MJ_APIKEY_PUBLIC")
        self.secret_key = os.getenv("MJ_APIKEY_PRIVATE")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_name = os.getenv("SENDER_NAME")
        self.base_url = "https://api.mailjet.com/v3.1/send"
        self.mailjet_client = Client(
            auth=(self.api_key, self.secret_key), version='v3.1')
        self.message_data = {
            "From": {
                "Email": self.sender_email,
                "Name": self.sender_name
            }
        }

    async def send_email(self, to_email: str, subject: str, body: str, attachments: list[str] = None, bcc: list[str] = None) -> tuple:
        """ Send an email using Mailjet with optional attachments and BCC support """
        audit_service = AuditService()
        try:
            message_data = self.message_data.copy()
            message_data["To"] = [
                {
                    "Email": to_email,
                    "Name": to_email
                }
            ]
            
            if bcc:
                message_data["Bcc"] = [
                    {"Email": email, "Name": email} for email in bcc if email
                ]
            
            message_data["Subject"] = subject
            message_data["HTMLPart"] = body

            if attachments:
                message_data["InlinedAttachments"] = []
                inline_attachments = self._attachment_helper(attachments)
                message_data["InlinedAttachments"].extend(inline_attachments)

            data = {"Messages": [message_data]}
            result = self.mailjet_client.send.create(data=data)

            await sync_to_async(audit_service.log_system_operation)(
                user=None,
                action='email_sent',
                status='success',
                details={'to_email': to_email, 'subject': subject}
            )

            return result.status_code == 200, result.json()
        except Exception as e:
            logger.error(f"Falhou o envio de email: {e}")
            try:
                await sync_to_async(audit_service.log_system_operation)(
                    user=None,
                    action='email_failed',
                    status='failure',
                    details={'to_email': to_email, 'subject': subject, 'error': str(e)}
                )
            except Exception as audit_error:
                # Audit logging failure should not block email error handling
                logger.warning(f"Failed to log audit for email error: {audit_error}")
            raise Exception(f"Failed to send email: {e}")

    def _attachment_helper(self, attachments: list) -> None:
        """ Helper to process attachments for Mailjet """
        inline_attachments = []
        for i, attachment in enumerate(attachments):
            attachment_data = self._process_attachment(attachment, i)
            if attachment_data:
                inline_attachment = {
                    "ContentType": attachment_data['content_type'],
                    "Filename": attachment_data['filename'],
                    "ContentID": attachment_data['content_id'],
                    "Base64Content": attachment_data['base64_content']
                }
                inline_attachments.append(inline_attachment)

        return inline_attachments

    def _process_attachment(self, attachment: dict, index: int) -> dict:
        """ Process a single attachment from S3 and prepare it for Mailjet """
        try:
            image_url = attachment.get('url')
            filename = attachment.get('filename', f'attachment_{index}')
            content_type = attachment.get(
                'content_type', 'application/octet-stream')
            s3_service = S3Service()
            image_bytes = s3_service.download_image(image_url)
            base64_content = base64.b64encode(image_bytes).decode('utf-8')

            return {
                'filename': filename,
                'content_type': content_type,
                'content_id': f'attachment_{index}',
                'base64_content': base64_content
            }

        except Exception as e:
            logger.error(f"Error processing attachment {index+1}: {e}")
            raise Exception(f"Error processing attachment {index+1}: {e}")

    async def send_fallback_email_to_admins(self, subject: str, html_content: str):
        """Send fallback email to admins in case of critical failure."""
        admin_emails = os.getenv(
            'ADMIN_EMAILS', '').split(',')
        for admin_email in admin_emails:
            await self.send_email(
                admin_email.strip(), subject, html_content, None)
