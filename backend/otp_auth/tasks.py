import logging

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


def send_otp_email(email, code, purpose="login"):
    """Sends an OTP email via Resend API synchronously. Caller is responsible for
    turning a raised exception into an HTTP error response.
    """
    if not settings.RESEND_API_KEY:
        logger.error("RESEND_API_KEY is not configured")
        raise ValueError("Email service is not configured")

    subject = f"Your DBurst verification code: {code}"

    if purpose == "signup":
        heading = "Verify your email to create your account"
        description = "Welcome to DBurst! To complete your signup, please use this verification code:"
    else:
        heading = "Your sign-in code"
        description = "To sign in to your DBurst account, please use this verification code:"

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Your DBurst verification code</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #18181b;
      font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
      color: #f4f4f5;
    }}
    .container {{
      max-width: 480px;
      margin: 40px auto;
      padding: 0 16px;
    }}
    .card {{
      background-color: #09090b;
      border: 1px solid #27272a;
      border-radius: 16px;
      padding: 32px 24px;
      overflow: hidden;
    }}
    .header {{
      text-align: center;
      margin-bottom: 32px;
    }}
    .logo {{
      display: inline-block;
      margin-bottom: 16px;
    }}
    .headline {{
      font-size: 12px;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: #71717a;
      margin: 0;
      margin-bottom: 20px;
    }}
    .code-box {{
      text-align: center;
      padding: 20px 32px;
      margin-bottom: 16px;
    }}
    .code {{
      display: inline-block;
      padding: 16px 28px;
      background-color: #18181b;
      border: 1px solid #3f3f46;
      border-radius: 12px;
      font-size: 36px;
      font-weight: 700;
      letter-spacing: 10px;
      color: #f4f4f5;
      font-family: 'Courier New', monospace;
    }}
    .description {{
      font-size: 14px;
      color: #a1a1aa;
      line-height: 1.5;
      margin: 0;
      text-align: center;
      padding: 0 32px;
    }}
    .expiry {{
      font-size: 14px;
      color: #a1a1aa;
      line-height: 1.5;
      margin: 16px 0 0 0;
      text-align: center;
      padding: 0 32px;
    }}
    .divider {{
      border-top: 1px solid #27272a;
      margin: 28px 32px 0;
    }}
    .footer {{
      text-align: center;
      padding: 20px 32px 0;
      font-size: 12px;
      color: #52525b;
      margin-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="header">
        <p class="headline">{heading}</p>
      </div>

      <p class="description">{description}</p>

      <div class="code-box">
        <div class="code">{code}</div>
      </div>

      <p class="expiry">
        This code expires in <strong>{settings.OTP_TTL_MINUTES} minutes</strong>.<br>
        If you didn't request this, you can safely ignore this email.
      </p>

      <div class="divider"></div>

      <div class="footer">
        <p>DBurst · AI-powered UI builder · A product of MindBurst</p>
      </div>
    </div>
  </div>
</body>
</html>"""

    try:
        params = {
            "from": settings.RESEND_DEFAULT_EMAIL,
            "to": [email],
            "subject": subject,
            "html": html_body,
        }

        email_response = resend.Emails.send(params)

        if "error" in email_response:
            raise Exception(f"Resend API error: {email_response['error']}")

        logger.info(f"OTP email sent to {email} (purpose={purpose})")
    except Exception as exc:
        logger.error(f"OTP email send failed for {email} (purpose={purpose}): {exc}")
        raise
