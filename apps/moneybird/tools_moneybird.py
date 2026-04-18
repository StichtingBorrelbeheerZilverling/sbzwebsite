from datetime import datetime, timedelta, timezone

import requests
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

import settings


class Moneybird:
    BASE_URL = "https://moneybird.com/"
    EXPIRE_MARGIN = 5*60 # seconds

    def __init__(self, request, client_id=None, client_secret=None):
        from apps.moneybird.models import Settings
        self.request = request

        self.client_id = client_id or settings.mb_client_id
        self.client_secret = client_secret or settings.mb_client_secret
        
        self.access_token = Settings.get("access_token")
        self.refresh_token = Settings.get("refresh_token")
        self.auth_code = Settings.get("auth_code")
        self.created_at = Settings.get("token_created_at")
        self.expires_in = Settings.get("token_expires_in")

        if self.created_at and self.expires_in:
            self.access_token_expiry = datetime.fromtimestamp(float(self.created_at), tz=timezone.utc) + timedelta(seconds=int(self.expires_in)-Moneybird.EXPIRE_MARGIN)
        else:
            self.access_token_expiry = None

        self._auth()

    @staticmethod
    def instantiate_or_redirect(request, *args, **kwargs):
        try:
            return Moneybird(request, *args, **kwargs), None
        except Exception:
            return None, redirect(Moneybird.BASE_URL + "oauth/authorize?client_id={}&redirect_uri={}&response_type=code&scope={}".format(
                settings.mb_client_id, 
                request.build_absolute_uri(reverse('moneybird:code')),
                "sales_invoices settings",
            ))

    def _auth(self):
        now = datetime.now(tz=timezone.utc)

        # Moneybird Access Tokens currently do not expire, but they may add this in the future.
        if self.access_token_expiry:
            if self.access_token and self.access_token_expiry > now:
                pass
            elif self.access_token and self.access_token_expiry <= now:
                self._request_token("refresh_token", self.refresh_token, "refresh_token")
            elif self.auth_code:
                self._request_token("code", self.auth_code, "authorization_code")
            else:
                raise Exception("Tokens are not present; request a new authorization code.")
        
        else:
            if self.access_token:
                pass
            elif self.auth_code:
                self._request_token("code", self.auth_code, "authorization_code")
            else:
                raise Exception("Tokens are not present; request a new authorization code.")
        
        # Test if Access token is valid
        response = self._get("administrations")
        if response.status_code != 200:
            # Remove Access token and try again
            self.access_token = None
            self._auth()

    def _request_token(self, token_type, token, grant_type):
        from apps.moneybird.models import Settings
        response = requests.post(Moneybird.BASE_URL + "oauth/token", data={
            token_type: token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.request.build_absolute_uri(reverse('moneybird:code')),
            "grant_type": grant_type,
        })

        if response.status_code != 200:
            raise Exception("Unknown response from the Moneybird API:\nStatus code: {}\n{}".format(response.status_code, response.text))

        data = response.json()

        self.refresh_token = data['refresh_token']
        self.access_token = data['access_token']
        self.access_token_expiry = None

        if 'expires_in' in data:
            self.access_token_expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=int(data['expires_in'])-Moneybird.EXPIRE_MARGIN)
            Settings.set('token_expires_in', data['expires_in'])

        Settings.set('refresh_token', self.refresh_token)
        Settings.set('access_token', self.access_token)
        Settings.set('token_created_at', data['created_at'])

    def _get(self, method):
        response = requests.get(Moneybird.BASE_URL + "api/v2/" + method, headers={
            'Authorization': 'Bearer {}'.format(self.access_token),
            'Accept': 'application/json',
        })
        if response.status_code == 429:
            # Rate limit
            messages.error(self.request, "Moneybird API rate limit exceeded. Please try again later.")
        return response

    def _post(self, method, data):
        response = requests.post(Moneybird.BASE_URL + "api/v2/" + method, headers={
            'Authorization': 'Bearer {}'.format(self.access_token),
            'Accept': 'application/json',
        }, json=data)
        if response.status_code == 429:
            # Rate limit
            messages.error(self.request, "Moneybird API rate limit exceeded. Please try again later.")
        return response

    def get_administration(self):
        return self._get("administrations").json()[0]['id']

    def create_invoice(self, administration, order):
        return self._post("{}/sales_invoices".format(administration), {'sales_invoice': order.as_dict()})
    
    def get_product(self, administration, product_id):
        return self._get("{}/products/{}".format(administration, product_id))

    def create_product(self, administration, product):
        return self._post("{}/products".format(administration), {'product': product})
    
    def get_customer(self, administration, customer_id):
        return self._get("{}/contacts/customer_id/{}".format(administration, customer_id))

    def create_customer(self, administration, customer):
        return self._post("{}/contacts".format(administration), {'contact': customer})


class MoneybirdOrderLine:
    def __init__(self,
                 product_id,
                 quantity,
                 description):
        self.description = description
        self.product_id = product_id
        self.quantity = quantity

    def as_dict(self):
        return {
            "amount": self.quantity,
            "product_id": self.product_id,
            "description": self.description,
        }


class MoneybirdOrder:
    # TODO add support for different workflows for different associations
    def __init__(self,
                 contact_id,
                 reference,
                 customer_vat_type):
        self.reference = reference
        self.contact_id = contact_id
        if customer_vat_type == '0' or customer_vat_type == 0:
            self.customer_vat_type = False
        else:
            self.customer_vat_type = True

        self.lines = []

    def add_line(self, line):
        self.lines.append(line)

    def as_dict(self):
        lines = [line.as_dict() for line in self.lines]

        return {
            "contact_id": self.contact_id,
            "reference": self.reference,
            # "prices_are_incl_tax": self.customer_vat_type,  #TODO: Fix incl/excl vat for different customers
            "details_attributes": lines,
        }