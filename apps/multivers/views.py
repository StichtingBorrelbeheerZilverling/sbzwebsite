import json
import time
from urllib.parse import unquote

import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

import settings
from apps.multivers.models import Settings

REDIRECT_URL = "http://www.sbz.utwente.nl/test.php"
token_expires = 0


@login_required(login_url='/admin/login/?next=/multivers/')
def index(request):
    if request.POST:
        return HttpResponse('Not implemented')
    result = _oauth(request)
    if result:
        return result
    else:
        if Settings.objects.filter(key='db').exists():
            return HttpResponse('asdfasd')
        else:
            return render(request, 'db.html', {'dbs': _get_administrations()})


def save_code(request, code=None):
    if code:
        _save_setting(key='auth_code', value=unquote(code))
    elif 'code' in request.GET:
        _save_setting(key='auth_code', value=unquote(request.GET['code']))
    return redirect('/multivers/')


def reset(request):
    Settings.objects.all().delete()
    return redirect('/multivers/')


def _save_setting(key, value=None):
    if key and value:
        setting, ignore = Settings.objects.get_or_create(key=key)
        setting.value = value
        setting.save()


def _oauth(request):
    for x in ['mv_client_id', 'mv_client_secret']:
        if not hasattr(settings, x) or not getattr(settings, x):
            raise Exception('The variable "{}" is not set in the settings.'.format(x))

    if Settings.objects.filter(key='access_token').exists() and Settings.objects.get(key='access_token').value:
        if token_expires < time.time():
            _get_access_token(token_type='refresh_token', token=Settings.objects.get(key='refresh_token').value, grant_type='refresh_token')
        return
    else:
        if Settings.objects.filter(key='auth_code').exists():
            auth_code = Settings.objects.get(key='auth_code')
            return _get_access_token(token=auth_code.value)
        else:
            return render(request, 'no_oauth.html', {
                'mv_client_id': settings.mv_client_id,
                'mv_redirect_url': REDIRECT_URL,
                'mv_scope': "http://UNIT4.Multivers.API/Web/WebApi/*",
            })


def _get_access_token(token_type='code', token=None, grant_type='authorization_code'):
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

        _save_setting('refresh_token', content['refresh_token'])
        _save_setting('token_type', content['token_type'])
        _save_setting('expires_in', content['expires_in'])
        _save_setting('access_token', content['access_token'])
        _save_setting('access_token_acquired', str(time.time()))
        token_expires = time.time() + int(content['expires_in']) - 2
        return redirect('/multivers/')
    else:
        Settings.objects.filter(key='auth_code').delete()
        Settings.objects.filter(key='access_token').delete()
        return HttpResponse('ERROROROROROR: ' + str(response.status_code) + ' ' + str(response.content) + '\n auth_token and access_token deleted')


def _get_administrations():
    response = requests.get(url="https://api.online.unit4.nl/V19/api/AdministrationNVL",
                            headers={
                                'Accept': 'application/json',
                                'Authorization': 'Bearer {}'.format(Settings.objects.get(key='access_token').value),
                            })
    if response.status_code == 200:
        return json.loads(response.content.decode("utf-8", "strict"))
    else:
        raise Exception('Error connecting to the api: {}'.format(response.content))


def select_db(request, name):
    _save_setting('db', name)
    return redirect('/multivers/')