import time
from datetime import datetime, timedelta, timezone
from json import JSONDecodeError

import requests
from django.shortcuts import redirect
from django.urls import reverse

import settings

# TODO: Rewrite file to moneybird

class MoneybirdOrderLine:
    def __init__(self,
                 date,
                 description,
                 discount,
                 product_id,
                 quantity,
                 revenue_account=None):
        self.date = date
        self.description = description
        self.discount = discount
        self.product_id = product_id
        self.quantity = quantity
        self.revenue_account = revenue_account

    def as_dict(self):
        result = {
            "autoCalculatePrice": True,
            "autoUnmatchToPurchase": False,
            "canChange": True,
            "costCentreId": "",
            "costUnitId": "",
            "deliveryDate": self.date.strftime("%d-%m-%Y 0:00:00"),
            "description": self.description,
            "discount": self.discount,
            "matchedToPurchase": False,
            "messages": [],
            "orderLineAmount": self.quantity,
            "orderLineType": 0,
            "pickListText": False,
            "productId": self.product_id,
            "quantityBackorder": 0,
            "quantityDelivered": self.quantity,
            "quantityOrdered": self.quantity,
            "quantityScale": 0,
            "quantityToDeliver": 0,
            "warehouseId": "",
        }

        if self.revenue_account:
            result["accountId"] = self.revenue_account
            result["discountAccountId"] = self.revenue_account

        return result


class MoneybirdOrder:
    def __init__(self,
                 date,
                 reference,
                 payment_condition_id,
                 customer_id,
                 customer_vat_type,
                 processor_id,
                 processor_name,
                 lines=None):
        self.date = date
        self.reference = reference
        self.payment_condition_id = payment_condition_id
        self.customer_id = customer_id
        self.customer_vat_type = customer_vat_type
        self.processor_id = processor_id
        self.processor_name = processor_name

        self.lines = lines or []

    def add_line(self, line):
        self.lines.append(line)

    def as_dict(self):
        lines = [line.as_dict() for line in self.lines]

        return {
            "accountManager": "",
            "accountManagerId": "",
            "messages": [],
            "applyOrderSurcharge": False,
            "approved": True,
            "approvedBy": "",
            "autoUnmatchToPurchase": False,
            "blocked": False,
            "canChange": True,
            "chargeVatType": self.customer_vat_type,
            "collectiveInvoiceSystemId": "",
            "contactPerson": "",
            "contactPersonId": "",
            "costCentreId": "",
            "costUnitId": "",
            "creditSqueezePerc": 0.0,
            "currencyId": "",
            "customerCountryId": "",
            "customerId": self.customer_id,
            "deliveryConditionId": "",
            "discountPercentage": 0.0,
            "mainOrderId": "",
            "mandateId": "",
            "matchedToPurchase": False,
            "orderDate": self.date.strftime("%d-%m-%Y"),
            "orderLines": lines,
            "orderState": 1,
            "orderSurcharge": 0.0,
            "orderSurchargeVatCodeId": 0,
            "orderType": 0,
            "paymentConditionId": self.payment_condition_id,
            "processedBy": self.processor_name,
            "processedById": self.processor_id,
            "projectId": "",
            "reference": self.reference,
            "totalCreditSqueezeAmount": 0.0,
            "totalDiscountAmount": 0.0,
            "vatScenarioId": 6, # Verkoop Binnenland
        }


class Moneybird:
    BASE_URL = "https://api.moneybird.nl/v23/"
    EXPIRE_MARGIN = 5*60 # seconds

    def __init__(self, request, client_id=None, client_secret=None):
        from apps.moneybird.models import Settings
        self.request = request
        self.client_id = client_id or settings.mv_client_id
        self.client_secret = client_secret or settings.mv_client_secret

        self.access_token = Settings.get("access_token")
        self.refresh_token = Settings.get("refresh_token")

        # TODO: just save the expire datetime
        acquired = Settings.get("access_token_acquired")
        expires_in = Settings.get("expires_in")

        if acquired and expires_in:
            self.access_token_expiry = datetime.fromtimestamp(float(acquired), tz=timezone.utc) \
                                       + timedelta(seconds=int(expires_in)-Moneybird.EXPIRE_MARGIN)
        else:
            self.access_token_expiry = None

        self.auth_code = Settings.get("auth_code")

        self._auth()

    @staticmethod
    def instantiate_or_redirect(request, *args, **kwargs):
        try:
            return Moneybird(request, *args, **kwargs), None
        except Exception:
            return None, redirect(Moneybird.BASE_URL + "OAuth/Authorize?client_id={}&redirect_uri={}&scope={}&response_type=code".format(
                settings.mv_client_id,
                request.build_absolute_uri(reverse('moneybird:code')),
                "http://UNIT4.Moneybird.API/Web/WebApi/*",
            ))

    def _request_token(self, token_type, token, grant_type):
        from apps.moneybird.models import Settings
        response = requests.post(Moneybird.BASE_URL + "OAuth/Token", data={
            token_type: token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            # TODO: replace with actual host
            "redirect_uri": "https://www.sbz.utwente.nl/" + (reverse("moneybird:code")),
            "grant_type": grant_type,
        })

        if response.status_code != 200:
            raise Exception("Unknown response from the moneybird API:\nStatus code: {}\n{}".format(response.status_code, response.text))

        data = response.json()

        self.refresh_token = data['refresh_token']
        self.access_token = data['access_token']
        self.access_token_expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=int(data['expires_in'])-Moneybird.EXPIRE_MARGIN)

        Settings.set('refresh_token', self.refresh_token)
        Settings.set('access_token', self.access_token)
        Settings.set('expires_in', data['expires_in'])
        Settings.set('access_token_acquired', str(time.time()))

    def _auth(self):
        now = datetime.now(tz=timezone.utc)

        if self.access_token and self.access_token_expiry > now:
            pass
        elif self.access_token and self.access_token_expiry <= now:
            self._request_token("refresh_token", self.refresh_token, "refresh_token")
        elif self.auth_code:
            self._request_token("code", self.auth_code, "authorization_code")
        else:
            raise Exception("Tokens are not present; request a new authorization code.")

    def _get(self, method):
        response = requests.get(Moneybird.BASE_URL + "api/" + method, headers={
            'Authorization': 'Bearer {}'.format(self.access_token),
            'Accept': 'application/json',
        })

        return response.json()

    def _post(self, method, data):
        response = requests.post(Moneybird.BASE_URL + "api/" + method, headers={
            'Authorization': 'Bearer {}'.format(self.access_token),
            'Accept': 'application/json',
        }, json=data)

        try:
            return response.json()
        except JSONDecodeError:
            raise Exception(response.text)

    def get_administrations(self):
        return self._get("AdministrationNVL")

    def get_order_info(self, administration, order_id):
        return self._get("{}/OrderInfo/{}".format(administration, order_id))

    def create_order(self, administration, order):
        return self._post("{}/Order".format(administration), order.as_dict())


# class MoneybirdOrderLine:
#     def __init__(self,
#                  product_id,
#                  quantity,
#                  description):
#         self.description = description
#         self.product_id = product_id
#         self.quantity = quantity


#     def as_dict(self):
#         return {
#             "amount": self.quantity,
#             "product_id": self.product_id,
#             "description": self.description,
#         }


# class MoneybirdOrder:
#     def __init__(self,
#                  contact_id,
#                  reference,
#                  customer_vat_type):
#         self.reference = reference
#         self.contact_id = contact_id
#         if customer_vat_type == '0' or customer_vat_type == 0:
#             self.customer_vat_type = False
#         else:
#             self.customer_vat_type = True

#         self.lines = []

#     def add_line(self, line):
#         self.lines.append(line)

#     def as_dict(self):
#         lines = [line.as_dict() for line in self.lines]

#         return {
#             "contact_id": self.contact_id,
#             "reference": self.reference,
#             # "prices_are_incl_tax": self.customer_vat_type,  # Currently not supported
#             "details_attributes": lines,
#         }

