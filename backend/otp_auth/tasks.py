import logging
from email.mime.image import MIMEImage
from pathlib import Path
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

LOGO_PATH = Path(settings.BASE_DIR) / "otp_auth" / "static" / "otp_auth" / "images" / "dburst-logo.png"


def send_otp_email(email, code, purpose="login"):
    """Sends the branded OTP email synchronously (no Celery/Redis broker —
    that background worker was OOM-killing the Render instance it shared
    with gunicorn). Caller is responsible for turning a raised exception
    into an HTTP error response.
    """
    try:
        context = {
            "code": code,
            "expiry_minutes": settings.OTP_TTL_MINUTES,
            "purpose": purpose,
        }
        html_body = render_to_string("otp_auth/otp_email.html", context)
    except (TemplateDoesNotExist, TemplateSyntaxError):
        logger.exception(f"OTP email template failed to render for {email} (purpose={purpose})")
        raise

    text_body = strip_tags(html_body)

    message = EmailMultiAlternatives(
        subject=f"Your DBurst verification code: {code}",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    message.attach_alternative(html_body, "text/html")
    message.mixed_subtype = "related"

    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as f:
            logo = MIMEImage(f.read())
        logo.add_header("Content-ID", "<dburst-logo>")
        logo.add_header("Content-Disposition", "inline", filename="dburst-logo.png")
        message.attach(logo)
    else:
        logger.warning(f"OTP email logo missing at {LOGO_PATH}, sending without it")

    try:
        message.send(fail_silently=False)
        logger.info(f"OTP email sent to {email} (purpose={purpose})")
    except (SMTPException, OSError) as exc:
        logger.error(f"OTP email send failed for {email} (purpose={purpose}): {exc}")
        raise
