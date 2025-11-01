import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import os
import time
from typing import Type
import smtplib
import os
import markdown2  # pip install markdown2


class SendEmailToolInput(BaseModel):
    recipient: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Subject of the email.")
    body: str = Field(None, description="Body of the email message.")  # optional

class SendEmailTool(BaseTool):
    name: str = "send_email"
    description: str = (
        "Sends an email containing the provided subject and body to the specified recipient. "
        "Useful for delivering final summaries or reports to a user."
    )
    args_schema: Type[BaseModel] = SendEmailToolInput

    def _run(self, recipient: str, subject: str, body: str = None) -> str:
        try:
            sender_email = os.getenv("SENDER_EMAIL")
            sender_password = os.getenv("EMAIL_PASSWORD")

            if not sender_email or not sender_password:
                raise ValueError("Missing SENDER_EMAIL or EMAIL_PASSWORD environment variables.")

            # Wait for the summary file to appear
            summary_path = "contract_summary.md"
            wait_time = 0
            while not os.path.exists(summary_path) and wait_time < 10:
                time.sleep(1)
                wait_time += 1

            if os.path.exists(summary_path):
                with open(summary_path, "r", encoding="utf-8") as f:
                    summary_text = f.read()
            else:
                summary_text = "Summary file not found."

            # Remove code fences at the start and end
            summary_text = summary_text.strip()
            if summary_text.startswith("```"):
                summary_text = summary_text[summary_text.find("\n")+1:]  # Remove first ``` line
            if summary_text.endswith("```"):
                summary_text = summary_text[:summary_text.rfind("\n")]  # Remove last ``` line 


            # Build final message
            msg = MIMEMultipart("alternative")
            msg["From"] = sender_email
            msg["To"] = recipient
            msg["Subject"] = subject

            full_body = (
                f"{summary_text}\n\n"
            )

            # Convert Markdown to HTML
            html_body = markdown2.markdown(full_body)

            plain_part = MIMEText(full_body, "plain")
            html_part = MIMEText(html_body, "html")

            msg.attach(plain_part)
            msg.attach(html_part)


            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)

            return f"✅ Email successfully sent to {recipient}"

        except Exception as e:
            return f"❌ Failed to send email: {str(e)}"
