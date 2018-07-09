import json
import django

import requests
from bs4 import BeautifulSoup

from settings import DE_KLOK_EMAIL, DE_KLOK_PASSWORD


class DeKlok:
    LOGIN_FORM_URL = "https://www.deklokdranken.nl/"
    PRICES_URL = "https://www.deklokdranken.nl/erpprice/index/list"

    def __init__(self):
        self.session = requests.Session()

        form_response = self.session.get(DeKlok.LOGIN_FORM_URL)
        form_soup = BeautifulSoup(form_response.text, "html.parser")

        login_url = form_soup.find(id="login-form-modal")['action']
        csrf_token = form_soup.find(id="login-form-modal").find(attrs={'name': 'form_key'})['value']

        email = DE_KLOK_EMAIL
        password = DE_KLOK_PASSWORD

        self.session.post(login_url, data={
            'form_key': csrf_token,
            'login[username]': email,
            'login[password]': password,
            'send': ''
        })

    def get_pid_by_url(self, product_url):
        response = self.session.get(product_url)
        soup = BeautifulSoup(response.text, "html.parser")
        cart_form = soup.find(attrs={'class': 'product-view'}).find(id='product_addtocart_form')
        pid = cart_form.find(attrs={'name': 'product'})['value']
        return pid

    def get_article_no_by_url(self, product_url):
        response = self.session.get(product_url)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find(id='product-attribute-specs-table')
        return table.find('th', text='Artikelnummer').find_next('td').get_text().strip()

    def get_article_name_by_url(self, product_url):
        response = self.session.get(product_url)
        soup = BeautifulSoup(response.text, "html.parser")
        header = soup.find(attrs={'class': 'page-title product-name'}).find('h1')
        return header.get_text()

    def get_product_prices(self, pids):
        response = self.session.post(DeKlok.PRICES_URL, data={
            'pids': json.dumps(pids),
        })

        return response.json()


if __name__ == "__main__":
    django.setup()
    from apps.grolsch.models import *
    product = Product.create_from_url("https://www.deklokdranken.nl/grolsch-pils-fust-50l.html", track_price=True)
    print(product.last_price)
