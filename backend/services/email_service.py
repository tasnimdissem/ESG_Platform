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
        current_app.logger.info('SMTP non configuré, envoi du mail ignoré pour %s', to_email)
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


def send_password_reset_email(to_email: str, token: str, expiry_minutes: int = 15) -> bool:
    reset_base_url = str(current_app.config.get('EMAIL_RESET_LINK_BASE_URL', 'http://localhost:5173/reset-password')).strip()
    query = urlencode({'token': token})
    reset_link = f'{reset_base_url}?{query}'

    subject = 'Plateforme ESG - Réinitialisation du mot de passe'
    text_body = (
        'Vous avez demandé une réinitialisation du mot de passe pour votre compte ESG Platform.\n\n'
        f'Utilisez ce lien pour réinitialiser votre mot de passe :\n{reset_link}\n\n'
        f'Ce lien expire dans {expiry_minutes} minutes.\n\n'
        'Si vous n’êtes pas à l’origine de cette demande, vous pouvez ignorer cet e-mail.'
    )
    html_body = f'''
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #0f172a;">
            <h2>Réinitialisation du mot de passe</h2>
            <p>Vous avez demandé une réinitialisation du mot de passe pour votre compte ESG Platform.</p>
            <p><a href="{reset_link}" style="display:inline-block;padding:12px 18px;background:#059669;color:#ffffff;text-decoration:none;border-radius:8px;">Réinitialiser le mot de passe</a></p>
            <p><strong>Ce lien expire dans {expiry_minutes} minutes.</strong></p>
            <p>Si le bouton ne fonctionne pas, copiez ce lien :</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>Si vous n’êtes pas à l’origine de cette demande, ignorez cet e-mail.</p>
          </body>
        </html>
    '''

    return send_email(to_email=to_email, subject=subject, text_body=text_body, html_body=html_body)
