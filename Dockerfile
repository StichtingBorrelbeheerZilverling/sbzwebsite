FROM python:3.12-alpine

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add --no-cache mariadb-dev \
    && apk add linux-headers pcre-dev gettext

# Create directory for SBZ app
RUN mkdir -p /app

# Copy over codebase
COPY . /app

WORKDIR /app

# Install pip packages
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install uwsgi

USER 1000:1000


EXPOSE 8080/tcp
CMD ["/bin/sh", "./scripts/start_web_wsgi.sh"]
