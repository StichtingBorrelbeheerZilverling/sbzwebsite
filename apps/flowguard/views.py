import json
import logging

from decimal import Decimal

from socketIO_client import SocketIO, BaseNamespace
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.http import HttpResponseBadRequest, HttpResponse
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
