import calendar

import datetime
from django.shortcuts import render, redirect
from django.utils import timezone

from apps.hygiene.forms import CheckDayForm, CheckDayItemForm
from apps.hygiene.models import CheckDay, CheckItem, CheckDayItem, CheckLocation


def check(request, pk=None):
    obj = CheckDay.objects.filter(date=datetime.date.today()).first() if pk is None else CheckDay.objects.filter(pk=pk).first()
    check_date = obj.date if obj is not None else datetime.date.today()

    if obj is None:
        items = {}
    else:
        items = CheckDayItem.objects.filter(day=obj)
        items = {item.item.pk: item for item in items}

    all_good = True

    locations = CheckLocation.objects.all()

    for location in locations:
        location.items = CheckItem.objects.filter(location=location).all()
        for item in location.items:
            instance = items.get(item.pk, None)
            data = request.POST if request.method == 'POST' else None
            initial_result = data.get(str(item.pk) + '-result', None) if data else None
            if instance and initial_result is None: initial_result = instance.result
            initial = {'result': initial_result}
            item.form = CheckDayItemForm(prefix=item.pk, instance=instance, data=data, initial=initial)

            if request.method == 'POST':
                if obj is None:
                    obj = CheckDay(date=check_date, checker=request.user)
                    obj.save()
                elif obj.checker != request.user:
                    obj.checker = request.user
                    obj.save()

                if item.form.is_valid():
                    checked_item = item.form.save(commit=False)
                    checked_item.day = obj
                    checked_item.item = item
                    checked_item.save()
                else:
                    all_good = False

    if request.method == 'POST' and all_good:
        return redirect('hygiene:check_day', obj.pk)

    return render(request, 'hygiene/check.html', locals())


def plan(request, year=None, month=None):
    now = timezone.now()
    year = now.year if year is None else int(year)
    month = now.month if month is None else int(month)
    start_date = datetime.date(year, month, 1)

    prev_month = (month - 2) % 12 + 1
    next_month = month % 12 + 1
    prev_year = year - (month == 1)
    next_year = year + (month == 12)

    cal = calendar.Calendar(calendar.MONDAY)
    dates = list(cal.itermonthdates(year, month))
    weeks_dates = [dates[i*7:(i+1)*7] for i in range(len(dates) // 7)]

    check_days = CheckDay.objects.filter(date__gte=dates[0], date__lte=dates[-1])
    check_days = {check_day.date: check_day for check_day in check_days}

    weeks = []

    for week_dates in weeks_dates:
        week = []

        for date in week_dates:
            instance = check_days.get(date, None)
            data = request.POST if request.method == 'POST' else None
            form = CheckDayForm(prefix=date.strftime("%Y%m%d"), instance=instance, data=data, initial={'date': date, 'checker': instance.checker.pk if instance else None})

            if request.method == 'POST' and form.is_valid():
                if form.cleaned_data['checker'] is None:
                    if instance is not None:
                        instance.delete()
                else:
                    form.save()

            week.append(form)

        weeks.append(week)

    if request.method == 'POST':
        return redirect('hygiene:plan')

    return render(request, 'hygiene/plan.html', locals())
