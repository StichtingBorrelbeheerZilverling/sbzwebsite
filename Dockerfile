FROM python:3.12-alpine

# Copy over codebase
COPY . /app

WORKDIR /app

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add --no-cache mariadb-dev \
    && apk add linux-headers pcre-dev gettext \
    && mkdir -p /app \
    && pip3 install -r requirements.txt

USER 1000:1000

EXPOSE 8080/tcp

CMD ["/bin/sh", "./scripts/start_web_wsgi.sh"]
