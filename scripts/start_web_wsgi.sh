#!/bin/sh

uwsgi --module=settings.wsgi:application --http 0.0.0.0:8080 --workers 4 --threads 4 --master --vacuum --enable-threads --log-x-forwarded-for
