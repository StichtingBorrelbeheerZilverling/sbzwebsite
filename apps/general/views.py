from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.contrib.auth import logout as django_logout, authenticate, login as django_login


def index(request):
    return render(request, 'general/frontpage.html', {'active_id': 'home'})


def construction(request):
    return render(request, 'general/construction.html', {'active_id': 'construction'})


def contact(request):
    return render(request, 'general/contact.html', {'active_id': 'contact'})


@require_POST
def login(request):
    post = request.POST

    if "username" not in post or "password" not in post:
        messages.add_message(request, messages.ERROR, _("Please provide a username and password"))
        return redirect('general:index')

    user = authenticate(username=post['username'], password=post['password'])

    if user is None:
        messages.add_message(request, messages.ERROR, _("Incorrect username or password"))
        return redirect('general:index')

    django_login(request, user)

    return redirect('general:index')


@require_POST
def logout(request):
    django_logout(request)
    return redirect('general:index')
