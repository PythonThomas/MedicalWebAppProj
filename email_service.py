import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph


def _generate_pdf() -> bytes:
    """Return a PDF containing only the JeffCare certificate header."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    doc.build([Paragraph("JeffCare Medical Certificate", styles["Title"])])
    return buffer.getvalue()


def send_certificate_email(to_email: str, user_data: dict) -> None:
    """Generate a certificate PDF and email it to to_email.

    Reads SMTP credentials from environment variables:
      SMTP_SERVER   — defaults to smtp.gmail.com
      SMTP_PORT     — defaults to 587
      SMTP_EMAIL    — sender address (your admin/system email)
      SMTP_PASSWORD — sender password / app password
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    from_email = os.getenv("SMTP_EMAIL", "dummy@gmail.com")
    password = os.getenv("SMTP_PASSWORD", "")

    given_name = user_data.get("given_name", "")
    surname = user_data.get("surname", "")

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = "Your JeffCare Medical Certificate"

    body = (
        f"Dear {given_name} {surname},\n\n"
        "Please find your medical certificate attached.\n\n"
        "Regards,\nJeffCare"
    )
    msg.attach(MIMEText(body, "plain"))

    pdf_bytes = _generate_pdf()
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(pdf_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        'attachment; filename="medical_certificate.pdf"',
    )
    msg.attach(attachment)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
