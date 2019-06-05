import json
from datetime import datetime

from decimal import Decimal
from django.core.management import BaseCommand
from pytz import UTC, timezone

from apps.flowguard.models import FlowChannel, FlowValue


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help="JSON format export from the old flowmeter database")

    def handle(self, *args, **options):
        data = open(options['json_file']).read()
        while data[0] != "[":
            data = data[data.index("\n")+1:]
        dump = json.loads(data)

        values_abscint_first = {}
        values_abscint_last = {}
        values_mbasement_first = {}
        values_mbasement_last = {}

        sbz_location = timezone('Europe/Amsterdam')

        for record in dump:
            time = datetime.strptime(record['timestamp'], "%Y-%m-%d %H:%M:%S")
            time = sbz_location.localize(time).astimezone(UTC)

            abscint = Decimal(record['abscint'])
            mbasement = Decimal(record['mbasement'])

            if abscint in values_abscint_first:
                values_abscint_first[abscint] = min(values_abscint_first[abscint], time)
                values_abscint_last[abscint] = max(values_abscint_last[abscint], time)
            else:
                values_abscint_first[abscint] = time
                values_abscint_last[abscint] = time

            if mbasement in values_mbasement_first:
                values_mbasement_first[mbasement] = min(values_mbasement_first[mbasement], time)
                values_mbasement_last[mbasement] = max(values_mbasement_last[mbasement], time)
            else:
                values_mbasement_first[mbasement] = time
                values_mbasement_last[mbasement] = time

        abscint_channel = FlowChannel.objects.get(index=0)
        mbasement_channel = FlowChannel.objects.get(index=1)

        for value in sorted(values_abscint_first.keys()):
            FlowValue(channel=abscint_channel, value=value, first_seen=values_abscint_first[value], last_seen=values_abscint_last[value]).save()

        for value in sorted(values_mbasement_first.keys()):
            FlowValue(channel=mbasement_channel, value=value, first_seen=values_mbasement_first[value], last_seen=values_mbasement_last[value]).save()
