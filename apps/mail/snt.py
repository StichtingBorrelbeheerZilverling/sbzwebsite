import uuid

import requests

import settings
from apps.mail.models import Group


class Log:
    def __init__(self):
        self._log = ""

    @property
    def as_str(self):
        return self._log

    def log(self, line, *args, **kwargs):
        self._log += line.format(*args, **kwargs) + "\n"


HORNET_API_BASE = "https://hornet.snt.utwente.nl/api/"

def get_api_headers():
    return {'X-API-AUTH': '{}:{}'.format(settings.HORNET_CLIENT_ID, settings.HORNET_CLIENT_SECRET)}


def hornet_response(resp):
    if resp.status_code != 200:
        raise Exception(resp.json())

    return resp.json()


def hornet_get(url):
    url = HORNET_API_BASE + url
    return hornet_response(requests.get(url, headers=get_api_headers()))


def hornet_post(url, **form):
    url = HORNET_API_BASE + url
    return hornet_response(requests.post(url, headers=get_api_headers(), json=form))


def hornet_delete(url):
    url = HORNET_API_BASE + url
    return hornet_response(requests.delete(url, headers=get_api_headers()))


def hornet_get_association_members():
    return hornet_get('association/members')


def hornet_add_association_member(email):
    return hornet_post('association/members', admin=False, internal_username=uuid.uuid4().hex, username=email)


def hornet_delete_association_member(membership_id):
    return hornet_delete('association/members/{}'.format(membership_id))


def hornet_get_committees():
    return hornet_get('committee')


def hornet_add_committee(name):
    return hornet_post('committee', name=name)


def hornet_delete_committee(committee_id):
    return hornet_delete('committee/{}'.format(committee_id))


def hornet_get_committee_members(committee_id):
    return hornet_get('committee/{}/members'.format(committee_id))


def hornet_add_committee_member(committee_id, email):
    return hornet_post('committee/{}/members'.format(committee_id), username=email)


def hornet_delete_committee_member(committee_id, committee_membership_id):
    return hornet_delete('committee/{}/members/{}'.format(committee_id, committee_membership_id))


def sync(commit=False):
    log = Log()

    groups = Group.objects.prefetch_related('group_destinations').all()

    log.log("== Start synchronization == ")
    log.log("  Commit = {}", commit)

    inbound = set()
    outbound = set()

    for group in groups:
        inbound |= set(group.incoming_aliases_list)
        if group.outgoing_email:
            outbound.add(group.outgoing_email)

    log.log("  There are {} inbound aliases and {} outbound email addresses", len(inbound), len(outbound))

    log.log("== Comparing to SNT values ==")

    hornet_members = hornet_get_association_members()
    hornet_committees = hornet_get_committees()

    log.log("  Changes to association members:")

    for member in hornet_members:
        if member['user']['email_address'] not in outbound and member['user']['email_address'] not in settings.HORNET_FORBID_REMOVAL:
            log.log("    - {}", member['internal_email'])
            if commit: hornet_delete_association_member(member['id'])

    for email in outbound:
        if not any(member['user']['email_address'] == email for member in hornet_members):
            log.log("    + {}", email)
            if commit: hornet_members.append(hornet_add_association_member(email))

    log.log("  Changes to committees:")

    for committee in hornet_committees:
        if committee['name'] not in inbound:
            log.log("    - {}", committee['name'])
            if commit: hornet_delete_committee(committee['id'])

    for alias in inbound:
        if not any(committee['name'] == alias for committee in hornet_committees):
            log.log("    + {}", alias)
            if commit: hornet_committees.append(hornet_add_committee(alias))

    for alias in inbound:
        group_set = set(group for group in groups if alias in group.incoming_aliases_list)
        group_set_old_len = -1

        while len(group_set) != group_set_old_len:
            group_set_old_len = len(group_set)

            for group in list(group_set):
                group_set |= set(group.group_destinations.all())

        destinations = {group.outgoing_email for group in group_set if group.outgoing_email}

        log.log("  Changes to {}", alias)

        alias_committee = None

        for committee in hornet_committees:
            if committee['name'] == alias:
                alias_committee = committee
                break

        if alias_committee is None:
            if commit:
                raise Exception('Committee for alias {} was not actually added'.format(alias))

            for dest in destinations:
                log.log("    + {}", dest)
        else:
            hornet_committee_members = hornet_get_committee_members(alias_committee['id'])

            for member in hornet_committee_members:
                if member['user']['email_address'] not in destinations:
                    log.log("    - {}", member['user']['email_address'])
                    if commit: hornet_delete_committee_member(alias_committee['id'], member['id'])

            for dest in destinations:
                if not any(member['user']['email_address'] == dest for member in hornet_committee_members):
                    log.log("    + {}", dest)
                    if commit: hornet_add_committee_member(alias_committee['id'], dest)

    return log
