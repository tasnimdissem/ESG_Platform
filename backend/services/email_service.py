from __future__ import annotations

import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode

from flask import current_app


def _is_smtp_configured() -> bool:
    return bool(current_app.config.get('SMTP_HOST'))


def _sender_address() -> str:
    sender_name = str(current_app.config.get('EMAIL_FROM_NAME', 'ESG Platform')).strip()
    sender_email = str(current_app.config.get('EMAIL_FROM', 'no-reply@esg-platform.local')).strip()
    return f'{sender_name} <{sender_email}>' if sender_name else sender_email


def send_email(to_email: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    if not _is_smtp_configured():
        current_app.logger.info('SMTP not configured, skipping email send to %s', to_email)
        return False

    host = str(current_app.config.get('SMTP_HOST'))
    port = int(current_app.config.get('SMTP_PORT', 587))
    username = str(current_app.config.get('SMTP_USERNAME', '')).strip()
    password = str(current_app.config.get('SMTP_PASSWORD', '')).strip()
    use_tls = bool(current_app.config.get('SMTP_USE_TLS', True))
    use_ssl = bool(current_app.config.get('SMTP_USE_SSL', False))

    message = EmailMessage()
    message['From'] = _sender_address()
    message['To'] = to_email
    message['Subject'] = subject
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype='html')

    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(host, port, timeout=30) as smtp:
        if use_tls and not use_ssl:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)

    return True


def send_password_reset_email(to_email: str, token: str) -> bool:
    reset_base_url = str(current_app.config.get('EMAIL_RESET_LINK_BASE_URL', 'http://localhost:5173/reset-password')).strip()
    query = urlencode({'token': token})
    reset_link = f'{reset_base_url}?{query}'

    subject = 'ESG Platform - Password reset'
    text_body = (
        'You requested a password reset for your ESG Platform account.\n\n'
        f'Use this link to reset your password:\n{reset_link}\n\n'
        'If you did not request this, you can ignore this email.'
    )
    html_body = f'''
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #0f172a;">
            <h2>Password reset</h2>
            <p>You requested a password reset for your ESG Platform account.</p>
            <p><a href="{reset_link}" style="display:inline-block;padding:12px 18px;background:#059669;color:#ffffff;text-decoration:none;border-radius:8px;">Reset password</a></p>
            <p>If the button does not work, copy this link:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>If you did not request this, ignore this email.</p>
          </body>
        </html>
    '''

    return send_email(to_email=to_email, subject=subject, text_body=text_body, html_body=html_body)
