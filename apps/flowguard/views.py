import calendar
import json
import logging
from datetime import timedelta, datetime, time

from decimal import Decimal

import pytz
from socketIO_client import SocketIO, BaseNamespace
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.http import HttpResponseBadRequest, HttpResponse, Http404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def update(request):
    if request.POST.get('secret', '') != settings.UPDATE_FLOW_SECRET:
        raise PermissionDenied

    now = timezone.now()
    updates = []

    try:
        data = json.loads(request.POST.get('data', ''))
        for value in data:
            update = {}
            channel = FlowChannel.objects.get(index=int(value['index']))
            update['channel_id'] = channel.pk
            update['channel_name'] = channel.name
            last_value = FlowValue.objects.filter(channel=channel).order_by('-last_seen').first()
            last_int_value = int(last_value.value * 10) # Decimal object, so this is exact.
            last_raw_value = last_int_value % (2**16)
            last_value_wraps = last_int_value // (2**16)

            if last_raw_value == value['value']:
                value = last_value
                value.last_seen = now
            else:
                # If the flowmeter powers down, it might round down a bit, so allow 10L of backward flow.
                if value['value'] < last_raw_value - 100:
                    wraps = last_value_wraps + 1
                    raw = value['value']
                else:
                    wraps = last_value_wraps
                    raw = value['value']

                value = FlowValue(channel=channel, value=(Decimal(wraps*2**16 + raw) / Decimal(10)), first_seen=now, last_seen=now)

            value.save()
            update['value'] = float(value.value)
            update['first_seen'] = value.first_seen.isoformat()
            update['last_seen'] = value.last_seen.isoformat()
            updates.append(update)
    except (json.JSONDecodeError, ValueError, TypeError):
        return HttpResponseBadRequest()

    # new_values = FlowValue.objects.values('channel').annotate(max_date=Max('last_seen'))

    with SocketIO(settings.FULL_LIVE_URL_HOST, settings.FULL_LIVE_URL_PORT, BaseNamespace) as bare_socket:
        socket = bare_socket.define(BaseNamespace, '/sbz/flow')
        socket.emit('update_flow', {'secret': settings.UPDATE_FLOW_SECRET, 'data': updates})

    return HttpResponse()


from apps.flowguard.models import FlowChannel, FlowValue


def monitor(request):
    socketio_url = settings.FULL_LIVE_URL_PREFIX
    channels = FlowChannel.objects.all()
    for channel in channels:
        channel.value = FlowValue.objects.filter(channel=channel).order_by("-last_seen").first()
    return render(request, 'flow/monitor.html', locals())


def stats(request):
    return None


def lookup(request):
    return None


def history(request, year=None, month=None):
    class data: pass
    now = timezone.now()

    year = now.year if year is None else int(year)
    month = now.month if month is None else int(month)

    if not (2000 <= year < 2100) or not (1 <= month <= 12):
        raise Http404

    prev_month = (month - 2) % 12 + 1
    next_month = month % 12 + 1
    prev_year = year - (month == 1)
    next_year = year + (month == 12)

    sbz_location = pytz.timezone('Europe/Amsterdam')
    start_date = sbz_location.localize(datetime(year, month, 1))

    cal = calendar.Calendar(calendar.MONDAY)
    dates = list(cal.itermonthdates(year, month))
    assert len(dates) % 7 == 0

    channels = FlowChannel.objects.all()
    channel_values = []

    for channel in channels:
        start = sbz_location.localize(datetime.combine(dates[0], time()))
        end = sbz_location.localize(datetime.combine(dates[-1], time())) + timedelta(days=1)
        flow_values = FlowValue.objects.filter(channel=channel, last_seen__gte=start, first_seen__lt=end).order_by("first_seen").all()

        week_flows = []

        for week in range(len(dates)//7):
            week_flows.append([])
            for day in range(7):
                week_flows[week].append(data())
                week_flows[week][day].date = sbz_location.localize(datetime.combine(dates[week*7+day], time()))
                week_flows[week][day].hours = []
                for hour in range(24):
                    week_flows[week][day].hours.append(0.0)

        for fr, to in zip(flow_values, flow_values[1:]):
            midpoint = fr.last_seen + (to.first_seen - fr.last_seen) / 2
            midpoint = midpoint.astimezone(sbz_location)
            flow = float(to.value - fr.value)

            if midpoint.date() in dates:
                index = dates.index(midpoint.date())
                week_flows[index // 7][index % 7].hours[midpoint.hour] += flow

        datum = data()
        datum.flows = week_flows
        datum.channel = channel
        channel_values.append(datum)

    return render(request, 'flow/history.html', locals())
