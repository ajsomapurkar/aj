import os
import smtplib
from email.message import EmailMessage


def send_email(to_email, subject, body):
    """Send email using SendGrid if configured, otherwise SMTP.
    Returns True on success, False on failure.
    """
    sendgrid_key = os.getenv('SENDGRID_API_KEY')
    from_addr = os.getenv('SMTP_FROM') or os.getenv('SENDGRID_FROM')

    if sendgrid_key:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            message = Mail(
                from_email=from_addr or os.getenv(
                    'SUPER_ADMIN_EMAIL') or 'no-reply@example.com',
                to_emails=to_email,
                subject=subject,
                plain_text_content=body,
            )
            sg = SendGridAPIClient(sendgrid_key)
            resp = sg.send(message)
            return resp.status_code in (200, 202)
        except Exception:
            pass

    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

    if not smtp_host or not smtp_user or not smtp_pass:
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception:
        return False
