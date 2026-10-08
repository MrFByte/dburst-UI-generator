import logging
from email.mime.image import MIMEImage
from pathlib import Path
from smtplib import SMTPException

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

LOGO_PATH = Path(settings.BASE_DIR) / "otp_auth" / "static" / "otp_auth" / "images" / "dburst-logo.png"


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_otp_email(self, email, code, purpose="login"):
    """Sends the branded OTP email.

    Error boundary: a broken template is a programming error — retrying it
    would just fail the same way again, so it's logged and dropped. A send
    failure (SMTP/network) is transient, so it's retried; once retries are
    exhausted, that's logged clearly too instead of surfacing as a bare
    Celery task failure with no operational signal.
    """
    try:
        print("At send_otp_email 1")
        context = {
            "code": code,
            "expiry_minutes": settings.OTP_TTL_MINUTES,
            "purpose": purpose,
        }
        print("At send_otp_email 2")
        html_body = render_to_string("otp_auth/otp_email.html", context)
        print("At send_otp_email 3")
    except (TemplateDoesNotExist, TemplateSyntaxError):
        logger.exception(f"OTP email template failed to render for {email} (purpose={purpose})")
        return

    text_body = strip_tags(html_body)
    print("At send_otp_email 4")

    try:
        message = EmailMultiAlternatives(
            subject=f"Your DBurst verification code: {code}",
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        message.attach_alternative(html_body, "text/html")
        message.mixed_subtype = "related"
        print("At send_otp_email 5")

        if LOGO_PATH.exists():
            with open(LOGO_PATH, "rb") as f:
                logo = MIMEImage(f.read())
            logo.add_header("Content-ID", "<dburst-logo>")
            logo.add_header("Content-Disposition", "inline", filename="dburst-logo.png")
            message.attach(logo)
            print("At send_otp_email 6")
        else:
            logger.warning(f"OTP email logo missing at {LOGO_PATH}, sending without it")

        message.send(fail_silently=False)
        print("At send_otp_email 7")
        logger.info(f"OTP email sent to {email} (purpose={purpose})")
        print("At send_otp_email 8")

    except (SMTPException, OSError) as exc:
        logger.warning(
            f"OTP email send failed for {email} "
            f"(attempt {self.request.retries + 1}/{self.max_retries + 1}): {exc}"
        )
        try:
            print("At send_otp_email 9")
            # No exc= here on purpose: passing it makes Celery re-raise that
            # exact exception once retries are exhausted instead of
            # MaxRetriesExceededError, which would skip the except clause
            # below entirely and defeat this whole error boundary.
            raise self.retry()
            print("At send_otp_email 10")
        except MaxRetriesExceededError:
            logger.error(
                f"OTP email permanently failed for {email} (purpose={purpose}) after exhausting retries: {exc}"
            )

    except Exception as exc:
        # Anything else is unexpected — log it with a full traceback, but
        # don't retry something we don't understand the shape of.
        logger.exception(f"Unexpected error sending OTP email to {email}: {exc}")
