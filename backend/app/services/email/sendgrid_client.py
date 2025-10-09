"""
SendGrid email client
"""

from typing import Optional, Dict, Any
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class DisabledEmailClient:
    """Mock email client when SendGrid is not configured"""

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log email attempt but don't send (SendGrid not configured)

        Returns success=False to indicate email not sent
        """
        logger.warning(
            f"Email not sent (SendGrid not configured): to={to_email}, subject={subject}"
        )
        return {
            "success": False,
            "error": "SendGrid not configured"
        }


class EmailClient:
    """SendGrid email client"""

    def __init__(self):
        # Import SendGrid only if credentials are configured
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        self.Mail = Mail
        self.Email = Email
        self.To = To
        self.Content = Content

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
            message = self.Mail(
                from_email=self.from_email,
                to_emails=self.To(to_email),
                subject=subject,
                html_content=self.Content("text/html", html_content)
            )

            if plain_content:
                message.plain_text_content = self.Content("text/plain", plain_content)

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


# Global instance - use disabled client if SendGrid not configured
if settings.sendgrid_api_key and settings.sendgrid_from_email:
    email_client = EmailClient()
    logger.info("SendGrid email client initialized")
else:
    email_client = DisabledEmailClient()
    logger.warning("SendGrid not configured - email notifications disabled")
