import json
import django

import requests
from bs4 import BeautifulSoup

from settings import DE_KLOK_EMAIL, DE_KLOK_PASSWORD


class DeKlok:
    LOGIN_FORM_URL = "https://www.deklokdranken.nl/account/login"
    PRICES_URL = "https://www.deklokdranken.nl/storefrontapi/de_klok/price_and_stock"

    def __init__(self):
        self.session = requests.Session()

        form_response = self.session.get(DeKlok.LOGIN_FORM_URL)
        form_soup = BeautifulSoup(form_response.text, "html.parser")

        login_url = form_soup.find(id="customer_login")['action']
        csrf_token = form_soup.find(id="customer_login").find(attrs={'name': '__RequestVerificationToken'})['value']

        email = DE_KLOK_EMAIL
        password = DE_KLOK_PASSWORD

        self.session.post(login_url, data={
            '__RequestVerificationToken': csrf_token,
            'customer[user_name]': email,
            'customer[password]': password,
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

    def get_product_prices(self, skus):
        response = self.session.post(DeKlok.PRICES_URL, json=[
            {'measureUnit': 'KR', 'sku': sku, 'quantity': 1} for sku in skus
        ])

        return response.json()
