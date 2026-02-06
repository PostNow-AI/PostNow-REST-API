"""
Mailjet Email Service - Handles email sending via Mailjet API.
Refactored to follow SOLID principles.
"""
import base64
import logging
import os
from typing import Optional

from asgiref.sync import sync_to_async
from mailjet_rest import Client

from AuditSystem.services import AuditService
from .s3_sevice import S3Service

logger = logging.getLogger(__name__)


class MailjetService:
    """
    Service for sending emails using Mailjet API.

    Supports HTML emails, inline attachments, and BCC recipients.
    Automatically logs all email operations via AuditService.
    """

    def __init__(
        self,
        audit_service: Optional[AuditService] = None,
        s3_service: Optional[S3Service] = None
    ):
        """
        Initialize MailjetService with optional dependency injection.

        Args:
            audit_service: Optional AuditService instance (DIP)
            s3_service: Optional S3Service instance (DIP)
        """
        # Configuration from environment
        self.api_key = os.getenv("MJ_APIKEY_PUBLIC")
        self.secret_key = os.getenv("MJ_APIKEY_PRIVATE")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_name = os.getenv("SENDER_NAME")

        # Mailjet client
        self.mailjet_client = Client(
            auth=(self.api_key, self.secret_key),
            version='v3.1'
        )

        # Injected dependencies (with defaults for backward compatibility)
        self._audit_service = audit_service
        self._s3_service = s3_service

        # Base message template
        self._base_message = {
            "From": {
                "Email": self.sender_email,
                "Name": self.sender_name
            }
        }

    @property
    def audit_service(self) -> AuditService:
        """Lazy-load AuditService if not injected."""
        if self._audit_service is None:
            self._audit_service = AuditService()
        return self._audit_service

    @property
    def s3_service(self) -> S3Service:
        """Lazy-load S3Service if not injected."""
        if self._s3_service is None:
            self._s3_service = S3Service()
        return self._s3_service

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[list[dict]] = None,
        bcc: Optional[list[str]] = None
    ) -> tuple[bool, dict]:
        """
        Send an email using Mailjet with optional attachments and BCC support.

        Args:
            to_email: Primary recipient email address
            subject: Email subject line
            body: HTML email body
            attachments: Optional list of attachment dicts with 'url', 'filename', 'content_type'
            bcc: Optional list of BCC email addresses

        Returns:
            Tuple of (success: bool, response: dict)

        Raises:
            Exception: If email sending fails
        """
        try:
            message_data = self._build_message(to_email, subject, body, bcc)

            if attachments:
                message_data["InlinedAttachments"] = self._process_attachments(
                    attachments
                )

            result = self.mailjet_client.send.create(
                data={"Messages": [message_data]}
            )

            await self._log_success(to_email, subject)
            return result.status_code == 200, result.json()

        except Exception as e:
            logger.error(f"Falhou o envio de email: {e}")
            await self._log_failure(to_email, subject, e)
            raise Exception(f"Failed to send email: {e}")

    async def send_fallback_email_to_admins(
        self,
        subject: str,
        html_content: str
    ):
        """Send fallback email to admins in case of critical failure."""
        admin_emails = self._get_admin_emails()
        for admin_email in admin_emails:
            await self.send_email(admin_email, subject, html_content)

    # Private helper methods (DRY)

    def _build_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        bcc: Optional[list[str]] = None
    ) -> dict:
        """Build the message data structure."""
        message = self._base_message.copy()
        message["To"] = [self._build_recipient(to_email)]
        message["Subject"] = subject
        message["HTMLPart"] = body

        if bcc:
            message["Bcc"] = [
                self._build_recipient(email)
                for email in bcc if email
            ]

        return message

    def _build_recipient(self, email: str) -> dict:
        """Build a recipient dict (DRY helper)."""
        return {"Email": email, "Name": email}

    def _process_attachments(self, attachments: list[dict]) -> list[dict]:
        """Process all attachments for Mailjet."""
        inline_attachments = []
        for index, attachment in enumerate(attachments):
            attachment_data = self._process_single_attachment(attachment, index)
            if attachment_data:
                inline_attachments.append(attachment_data)
        return inline_attachments

    def _process_single_attachment(
        self,
        attachment: dict,
        index: int
    ) -> Optional[dict]:
        """Process a single attachment from S3 and prepare for Mailjet."""
        try:
            image_url = attachment.get('url')
            filename = attachment.get('filename', f'attachment_{index}')
            content_type = attachment.get('content_type', 'application/octet-stream')

            # Download from S3 and encode
            image_bytes = self.s3_service.download_image(image_url)
            base64_content = base64.b64encode(image_bytes).decode('utf-8')

            return {
                "ContentType": content_type,
                "Filename": filename,
                "ContentID": f'attachment_{index}',
                "Base64Content": base64_content
            }

        except Exception as e:
            logger.error(f"Error processing attachment {index + 1}: {e}")
            raise Exception(f"Error processing attachment {index + 1}: {e}")

    def _get_admin_emails(self) -> list[str]:
        """Get admin email addresses from environment."""
        emails_str = os.getenv('ADMIN_EMAILS', '')
        return [email.strip() for email in emails_str.split(',') if email.strip()]

    async def _log_success(self, to_email: str, subject: str):
        """Log successful email send."""
        await sync_to_async(self.audit_service.log_system_operation)(
            user=None,
            action='email_sent',
            status='success',
            details={'to_email': to_email, 'subject': subject}
        )

    async def _log_failure(self, to_email: str, subject: str, error: Exception):
        """Log failed email send."""
        try:
            await sync_to_async(self.audit_service.log_system_operation)(
                user=None,
                action='email_failed',
                status='failure',
                details={
                    'to_email': to_email,
                    'subject': subject,
                    'error': str(error)
                }
            )
        except Exception:
            # Silently fail audit logging to avoid masking original error
            pass
