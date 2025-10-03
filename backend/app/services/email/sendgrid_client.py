"""
SendGrid email client
"""

from typing import Optional, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings


class EmailClient:
    """SendGrid email client"""

    def __init__(self):
        self.client = SendGridAPIClient(settings.sendgrid_api_key)
        self.from_email = Email(settings.sendgrid_from_email, settings.sendgrid_from_name)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via SendGrid

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            plain_content: Plain text content (optional)

        Returns:
            Response dictionary with success status
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            if plain_content:
                message.plain_text_content = Content("text/plain", plain_content)

            response = self.client.send(message)

            return {
                "success": True,
                "status_code": response.status_code,
                "message_id": response.headers.get("X-Message-Id")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
email_client = EmailClient()
