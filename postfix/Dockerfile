FROM alpine:3.20

RUN apk add --no-cache \
    bash \
    ca-certificates \
    coreutils \
    postfix \
    postfix-sasl \
    rsyslog \
    tzdata \
    busybox-extras

COPY main.cf /etc/postfix/main.cf
COPY rsyslog.conf /etc/rsyslog.conf
COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && mkdir -p /var/spool/postfix /var/log/postfix /run/rsyslog \
    && chmod 755 /var/spool/postfix /var/log/postfix

EXPOSE 25

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD nc -z 127.0.0.1 25 || exit 1

ENTRYPOINT ["/entrypoint.sh"]