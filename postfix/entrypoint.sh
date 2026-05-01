#!/usr/bin/env sh
set -eu

umask 077

POSTFIX_MYHOSTNAME="${POSTFIX_MYHOSTNAME:-postfix.local}"
POSTFIX_MYNETWORKS="${POSTFIX_MYNETWORKS:-127.0.0.0/8 [::1]/128 172.16.0.0/12}"
POSTFIX_RELAY_HOST="${POSTFIX_RELAY_HOST:-[smtp.gmail.com]:587}"
GMAIL_USER="${GMAIL_USER:-}"
GMAIL_APP_PASSWORD="${GMAIL_APP_PASSWORD:-}"

if [ -z "$GMAIL_USER" ] || [ -z "$GMAIL_APP_PASSWORD" ]; then
  echo "GMAIL_USER and GMAIL_APP_PASSWORD are required." >&2
  exit 1
fi

cat > /etc/postfix/sasl_passwd <<EOF
${POSTFIX_RELAY_HOST} ${GMAIL_USER}:${GMAIL_APP_PASSWORD}
EOF

postmap hash:/etc/postfix/sasl_passwd
chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db

postconf -e "myhostname = ${POSTFIX_MYHOSTNAME}"
postconf -e "myorigin = ${POSTFIX_MYHOSTNAME}"
postconf -e "mydestination = localhost"
postconf -e "inet_interfaces = all"
postconf -e "inet_protocols = ipv4"
postconf -e "mynetworks = ${POSTFIX_MYNETWORKS}"
postconf -e "relayhost = ${POSTFIX_RELAY_HOST}"
postconf -e "smtp_sasl_auth_enable = yes"
postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"
postconf -e "smtp_sasl_security_options = noanonymous"
postconf -e "smtp_sasl_tls_security_options = noanonymous"
postconf -e "smtp_tls_security_level = encrypt"
postconf -e "smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"
postconf -e "smtp_tls_mandatory_protocols = TLSv1.2 TLSv1.3"
postconf -e "smtp_tls_note_starttls_offer = yes"
postconf -e "disable_dns_lookups = no"
postconf -e "smtpd_relay_restrictions = permit_mynetworks,reject_unauth_destination"
postconf -e "smtpd_recipient_restrictions = permit_mynetworks,reject_unauth_destination"
postconf -e "message_size_limit = 26214400"

mkdir -p /var/log/postfix
touch /var/log/postfix/maillog

rsyslogd
postfix check

exec postfix start-fg