from django.shortcuts import render


def index(request):
    return render(request, 'general/frontpage.html', {'active_id': 'home'})


def construction(request):
    return render(request, 'general/construction.html', {'active_id': 'construction'})


def contact(request):
    return render(request, 'general/contact.html', {'active_id': 'contact'})
