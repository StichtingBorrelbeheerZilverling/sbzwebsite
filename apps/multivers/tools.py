import json
import time
import traceback
from datetime import datetime

import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

import settings
from apps.multivers.models import Settings

REDIRECT_URL = "http://www.sbz.utwente.nl/test.php"
token_expires = 0


def check_json_upload(data):
    try:
        for k, v in data['products'].items():
            int(k)
        for k, v in data['drinks'].items():
            for d in v:
                for pid, pprice in d['products'].items():
                    int(pid)
                    float(pprice)
                datetime.strptime(d['date'], "%d-%m-%Y")
                if 'drink_name' not in d:
                    return 'No drink_name in one of the values'

                if 'location' not in d:
                    return 'No location in one of the values'
        return
    except KeyError:
        return traceback.format_exc()
    except ValueError:
        return traceback.format_exc()


def save_setting(key, value=None):
    if key and value:
        setting, ignore = Settings.objects.get_or_create(key=key)
        setting.value = value
        setting.save()


def oauth(request):
    for x in ['mv_client_id', 'mv_client_secret']:
        if not hasattr(settings, x) or not getattr(settings, x):
            raise Exception('The variable "{}" is not set in the settings.'.format(x))

    if Settings.objects.filter(key='access_token').exists() and Settings.objects.get(key='access_token').value:
        if token_expires < time.time():
            get_access_token(token_type='refresh_token', token=Settings.objects.get(key='refresh_token').value, grant_type='refresh_token')
        return
    else:
        if Settings.objects.filter(key='auth_code').exists():
            auth_code = Settings.objects.get(key='auth_code')
            return get_access_token(token=auth_code.value)
        else:
            return render(request, 'multivers/no_oauth.html', {
                'mv_client_id': settings.mv_client_id,
                'mv_redirect_url': REDIRECT_URL,
                'mv_scope': "http://UNIT4.Multivers.API/Web/WebApi/*",
            })


def get_access_token(token_type='code', token=None, grant_type='authorization_code'):
    global token_expires
    response = requests.post(
        url="https://api.online.unit4.nl/V19/OAuth/Token",
        data='{}={}&client_id={}&client_secret={}&redirect_uri={}&grant_type={}'.format(
            token_type,
            token,
            settings.mv_client_id,
            settings.mv_client_secret,
            REDIRECT_URL,
            grant_type,
        ),
        headers={'Content-Type': 'application/x-www-form-urlencoded', 'charset': 'UTF-8'},
    )

    if response.status_code == 200:
        content = json.loads(response.content.decode("utf-8", "strict"))

        save_setting('refresh_token', content['refresh_token'])
        save_setting('token_type', content['token_type'])
        save_setting('expires_in', content['expires_in'])
        save_setting('access_token', content['access_token'])
        save_setting('access_token_acquired', str(time.time()))
        token_expires = time.time() + int(content['expires_in']) - 2
        return redirect(reverse('multivers:index'))
    else:
        Settings.objects.filter(key='auth_code').delete()
        Settings.objects.filter(key='access_token').delete()
        return HttpResponse('ERROROROROROR: ' + str(response.status_code) + ' ' + str(response.content) + '\n auth_token and access_token deleted')


def get_administrations():
    response = requests.get(
        url="https://api.online.unit4.nl/V19/api/AdministrationNVL",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(Settings.objects.get(key='access_token').value),
        })
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8", "strict"))
    else:
        raise Exception('Error connecting to the api: {}'.format(response.content))


def send_to_multivers(order: dict):
    response = requests.post(
        url="https://api.online.unit4.nl/V19/api/{}/Order".format(Settings.objects.get(key='db').value),
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(Settings.objects.get(key='access_token').value),
            'content-type': 'application/json',
        },
        json=order,
    )
    return response.status_code == 200, response
