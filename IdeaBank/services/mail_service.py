import logging
import os

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

    def send_email(self, recipient_email, subject, html_content) -> tuple:
        if 'msallesblanco' in recipient_email:
            try:
                data = {
                    'Messages': [
                        {
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
                    ]
                }
                result = self.mailjet_client.send.create(data=data)
                logger.info(
                    f"Email enviado para {recipient_email}: {result.status_code}")
                return result.status_code, result.json()
            except Exception as e:
                print(f"Erro ao enviar email: {str(e)}")
                return None, {'error': str(e)}
        else:
            logger.info(
                f"Email para {recipient_email} bloqueado para evitar auto-envio.")
            return None, {'error': 'Auto-email sending blocked.'}
