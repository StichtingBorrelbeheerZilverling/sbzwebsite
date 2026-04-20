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
        except MoneybirdTokensNotPresentException:
            return None, redirect(Moneybird.BASE_URL + "oauth/authorize?client_id={}&redirect_uri={}&response_type=code&scope={}".format(
                settings.mb_client_id, 
                request.build_absolute_uri(reverse('moneybird:code')),
                "sales_invoices settings",
            ))
        except MoneybirdRateLimitExceededException as e:
            messages.error(request, "Rate limit exceeded, try again after {} seconds.".format(e.response.headers['RateLimit-Remaining']))
            return None, redirect('moneybird:index')
        except Exception as e:
            messages.error(request, "An error occurred while connecting to the Moneybird API: {}".format(e.response.text))
            return None, redirect('moneybird:index')

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
                raise MoneybirdTokensNotPresentException()
        
        else:
            if self.access_token:
                pass
            elif self.auth_code:
                self._request_token("code", self.auth_code, "authorization_code")
            else:
                raise MoneybirdTokensNotPresentException()
        
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
        # print("Get Request Headers: {}".format(response.request.headers))
        # print("Get Request Body: {}".format(response.request.body))
        # print("Get Response: {}".format(response.json()))
        # print()

        return self._response_handling(response)

    def _post(self, method, data):
        response = requests.post(Moneybird.BASE_URL + "api/v2/" + method, headers={
            'Authorization': 'Bearer {}'.format(self.access_token),
            'Accept': 'application/json',
        }, json=data)
        
        # print("Post Request Headers: {}".format(response.request.headers))
        # print("Post Request Body: {}".format(response.request.body))
        # print("Post Response: {}".format(response.json()))
        # print()

        return self._response_handling(response)
    
    def _response_handling(self, response):
        if response.status_code == 404:
            raise MoneybirdNotFoundException("Requested resource not found in Moneybird API", response=response)

        elif response.status_code == 402:
            raise MoneybirdAccountLimitReachedException("Moneybird account limit reached.", response=response)
        
        elif response.status_code == 429:
            raise MoneybirdRateLimitExceededException("Moneybird API rate limit exceeded.", response=response)

        elif response.status_code in [400, 401, 403, 405, 406, 422]:
            raise MoneybirdBadRequestException("Bad request to Moneybird API", response=response)
        
        elif response.status_code == 500:
            raise MoneybirdInternalServerErrorException("Moneybird API returned an internal server error.", response=response)
        
        return response
    
    def create_missing_customers(self, request, orders):
        from apps.moneybird.models import Customer
        administration = self.get_administration()

        for customer in Customer.objects.filter(pk__in=orders.values_list('customer_id', flat=True).distinct()):
            if customer.moneybird_id:
                try:
                    response = self.get_customer(administration, customer.moneybird_id)
                    moneybird_customer = response.json()

                    # TODO: remove, different name is inevitable (KvK name vs Alexia name). Do check for vat_type/invoice_workflow when implemented
                    if moneybird_customer['company_name'] != customer.alexia_name:
                        messages.warning(request, "Customer {} has a different name in Moneybird ({}). Consider updating it.".format(customer.alexia_name, moneybird_customer['company_name']))

                except MoneybirdNotFoundException:
                    messages.error(request, "Moneybird customer does not exist. Removing Moneybird ID for customer {}.".format(customer.alexia_name))
                    customer.moneybird_id = ""
                    customer.save()
        
            if not customer.moneybird_id:
                response = self.create_customer(administration, customer.as_moneybird_dict())
                customer.moneybird_id = response.json()['id']
                customer.save()
                messages.success(request, "Customer {} created successfully in Moneybird.".format(customer.alexia_name))


    def create_missing_products(self, request, orders):
        from apps.moneybird.models import Product
        administration = self.get_administration()
        
        for product in Product.objects.filter(pk__in=orders.values_list('conceptorderdrink__conceptorderdrinkline__product', flat=True).distinct()):
            if product.moneybird_id:
                try:
                    response = self.get_product(administration, product.moneybird_id)
                    moneybird_product = response.json()
                    if moneybird_product['title'] != product.alexia_name:
                        messages.warning(request, "Product {} has a different name in Moneybird ({}). Consider updating it.".format(product.alexia_name, moneybird_product['title']))
                
                except MoneybirdNotFoundException:        
                    messages.error(request, "Moneybird Product does not exist. Removing Moneybird ID for product {}.".format(product.alexia_name))
                    product.moneybird_id = ""
                    product.save()
        
            if not product.moneybird_id:
                response = self.create_product(administration, product.as_moneybird_dict())
                product.moneybird_id = response.json()['id']
                product.save()
                messages.success(request, "Product {} created successfully in Moneybird.".format(product.alexia_name))


    def get_administration(self):
        return self._get("administrations").json()[0]['id']

    def create_invoice(self, administration, order):
        return self._post("{}/sales_invoices".format(administration), {'sales_invoice': order.as_dict()})
    
    def get_product(self, administration, product_id):
        return self._get("{}/products/{}".format(administration, product_id))

    def create_product(self, administration, product):
        return self._post("{}/products".format(administration), {'product': product})
    
    def get_customer(self, administration, customer_id):
        return self._get("{}/contacts/{}".format(administration, customer_id))

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
    # TODO add support for different workflows for different associations (for incl/excl vat)
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
    

class MoneybirdNotFoundException(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response
    
    def __str__(self):
        return "MoneybirdNotFoundException: {}".format(super().__str__())

class MoneybirdBadRequestException(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response

    def __str__(self):
        return "MoneybirdBadRequestException: {}".format(super().__str__())

class MoneybirdAccountLimitReachedException(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response

    def __str__(self):
        return "MoneybirdAccountLimitReachedException: {}".format(super().__str__())

class MoneybirdTokensNotPresentException(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response

    def __str__(self):
        return "MoneybirdTokensNotPresentException: {}".format(super().__str__())

class MoneybirdRateLimitExceededException(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response

    def __str__(self):
        return "MoneybirdRateLimitExceededException: {}".format(super().__str__())

class MoneybirdInternalServerErrorException(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response

    def __str__(self):
        return "MoneybirdInternalServerErrorException: {}".format(super().__str__())