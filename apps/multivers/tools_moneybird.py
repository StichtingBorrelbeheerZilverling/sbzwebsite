import json
import time
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from json import JSONDecodeError
from urllib import parse

import django
import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

import settings
from apps.multivers.models import Settings


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
            # "prices_are_incl_tax": self.customer_vat_type,  # Currently not supported
            "details_attributes": lines,
        }

