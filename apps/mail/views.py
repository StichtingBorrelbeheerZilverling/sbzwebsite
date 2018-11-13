from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.mail import snt
from apps.mail.forms import GroupForm
from apps.mail.models import Group


def index(request):
    groups = Group.objects

    people = groups.filter(type="P").all()
    functions = groups.filter(type="F").all()
    organizations = groups.filter(type="O").all()

    for group_list in (people, functions, organizations):
        for group in group_list:
            group.form = GroupForm(instance=group)

    create_form = GroupForm()

    return render(request, 'mail/index.html', {
        'create_form': create_form,
        'people': people,
        'functions': functions,
        'organizations': organizations,
    })


def sync(request):
    if request.method == 'POST':
        commit = True
    else:
        commit = False

    log = snt.sync(commit=commit)

    return render(request, 'mail/sync.html', {
        'log': log,
        'commit': commit,
    })


def warn_sync(request):
    messages.warning(request, 'Please remember to synchronize the aliases with Hornet.')


@require_http_methods(["POST"])
def group_create(request):
    form = GroupForm(request.POST)
    if form.is_valid():
        form.save()

    warn_sync(request)

    return redirect('mail:index')


@require_http_methods(["POST"])
def group_edit(request, pk):
    group = get_object_or_404(Group, pk=pk)
    form = GroupForm(request.POST, instance=group)
    if form.is_valid():
        form.save()

    warn_sync(request)

    return redirect('mail:index')


@require_http_methods(["POST"])
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group.delete()

    warn_sync(request)

    return redirect('mail:index')
