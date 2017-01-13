from django.shortcuts import render
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required


@login_required(login_url='/admin/login/?next=/multivers/')
def index(request):
    return HttpResponse('BOE')
