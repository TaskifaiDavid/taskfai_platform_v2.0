"""
Email notification service
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from app.services.email.sendgrid_client import email_client
from app.db import get_supabase


class EmailNotifier:
    """Send email notifications for uploads"""

    def __init__(self):
        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def send_upload_notification(
        self,
        user_id: str,
        batch_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Send upload notification email

        Args:
            user_id: User identifier
            batch_id: Batch identifier
            status: "success" or "failure"

        Returns:
            Email sending result
        """
        supabase = get_supabase()

        try:
            # Get user details
            user_result = supabase.table("users").select("email, username").eq("id", user_id).execute()

            if not user_result.data:
                return {"success": False, "error": "User not found"}

            user = user_result.data[0]
            user_email = user.get("email")

            if not user_email:
                return {"success": False, "error": "User email not found"}

            # Get batch details
            batch_result = supabase.table("upload_batches").select("*").eq("batch_id", batch_id).execute()

            if not batch_result.data:
                return {"success": False, "error": "Batch not found"}

            batch = batch_result.data[0]

            # Prepare template context
            context = {
                "filename": batch.get("filename"),
                "upload_mode": batch.get("upload_mode", "").capitalize(),
                "processed_at": self._format_datetime(batch.get("processed_at")),
                "dashboard_url": "http://localhost:5173/dashboard"  # TODO: Use actual dashboard URL
            }

            # Send appropriate email based on status
            if status == "success":
                subject = "✅ File Upload Successful"
                template = self.env.get_template("upload_success.html")

                context.update({
                    "vendor": batch.get("detected_vendor", "Unknown").capitalize(),
                    "total_rows": batch.get("total_rows", 0),
                    "successful_rows": batch.get("successful_rows", 0),
                    "failed_rows": batch.get("failed_rows", 0)
                })

            else:  # failure
                subject = "❌ File Upload Failed"
                template = self.env.get_template("upload_failure.html")

                context.update({
                    "error_message": batch.get("error_message", "Unknown error occurred")
                })

            # Render template
            html_content = template.render(**context)

            # Send email
            result = email_client.send_email(
                to_email=user_email,
                subject=subject,
                html_content=html_content
            )

            # Log email
            self._log_email(
                user_id=user_id,
                to_email=user_email,
                subject=subject,
                status="sent" if result.get("success") else "failed",
                batch_id=batch_id
            )

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _format_datetime(self, dt_string: Optional[str]) -> str:
        """Format datetime string"""
        if not dt_string:
            return "N/A"

        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %I:%M %p UTC")
        except:
            return dt_string

    def _log_email(
        self,
        user_id: str,
        to_email: str,
        subject: str,
        status: str,
        batch_id: Optional[str] = None
    ) -> None:
        """Log email in database"""
        try:
            supabase = get_supabase()

            log_data = {
                "user_id": user_id,
                "to_email": to_email,
                "subject": subject,
                "status": status,
                "sent_at": datetime.utcnow().isoformat()
            }

            if batch_id:
                log_data["batch_id"] = batch_id

            supabase.table("email_logs").insert(log_data).execute()

        except Exception as e:
            print(f"Failed to log email: {e}")


# Global instance
email_notifier = EmailNotifier()
