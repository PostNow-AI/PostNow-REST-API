import logging
import os

from allauth.account.adapter import DefaultAccountAdapter
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        Override to use frontend URL for email confirmation
        """
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        return f"{frontend_url}/verify-email?key={emailconfirmation.key}"

    def get_password_reset_url(self, request, uidb36, token):
        """
        Override to use frontend URL for password reset
        """
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        return f"{frontend_url}/reset-password?uidb36={uidb36}&key={token}"

    def send_mail(self, template_prefix, email, context):
        """
        Completely override send_mail to force HTML emails with proper error handling
        """
        try:
            context['frontend_url'] = os.getenv(
                'FRONTEND_URL', 'http://localhost:5173')

            # Get the subject
            subject = render_to_string(
                f'{template_prefix}_subject.txt', context)
            subject = ' '.join(subject.splitlines()).strip()

            # Get HTML content only
            html_content = render_to_string(
                f'{template_prefix}_message.html', context)

            # Create HTML email message
            from_email = self.get_from_email()
            msg = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=from_email,
                to=[email]
            )

            # Force content type to HTML
            msg.content_subtype = "html"

            # Send the email
            result = msg.send()
            logger.info(
                f"Email sent successfully to {email} with subject '{subject}' (result: {result})")
            return result

        except Exception as e:
            logger.error(
                f"Failed to send email to {email}: {str(e)}", exc_info=True)
            # Don't raise the exception - log it and return 0 to indicate failure
            # This prevents allauth from breaking if email sending fails
            return 0

    def render_mail(self, template_prefix, email, context, headers=None):
        """
        This method should not be used, but just in case, force HTML
        """
        # Call our custom send_mail method instead
        return self.send_mail(template_prefix, email, context)
