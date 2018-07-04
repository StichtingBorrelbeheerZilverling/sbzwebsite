from datetime import datetime

from .models import Product, Customer, Settings

months = [
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
]


class OrderLine(dict):
    def __init__(self, line_date, drink_name, **kwargs):
        self.date = datetime.strptime(line_date, "%d-%m-%Y")
        self.drink_name = drink_name

        super(OrderLine, self).__init__(**kwargs)

    def __eq__(self, other):
        return self.date.__eq__(other.date) and self['productId'] == other['productId'] and self.drink_name == other.drink_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if not self.date.__eq__(other.date):
            return self.date.__lt__(other.date)
        elif not self.drink_name.__eq__(other.drink_name):
            return self.drink_name.__lt__(other.drink_name)
        else:
            return self['productId'].__lt__(other['productId'])

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)


def make_order(costumer_name: str, orderlines: list):
    orderlines = sorted(orderlines)
    for i in range(len(orderlines)):
        orderlines[i]['orderLineId'] = str(i + 1)
    costumer = Customer.objects.get(alexia_name=costumer_name)

    month = months[orderlines[0].date.month - 1]

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
        "chargeVatType": costumer.vat_type,
        "collectiveInvoiceSystemId": "",
        "contactPerson": "",
        "contactPersonId": "",
        "costCentreId": "",
        "costUnitId": "",
        "creditSqueezePerc": 0.0,
        "currencyId": "",
        "customerCountryId": "",
        "customerId": costumer.multivers_id,
        "deliveryConditionId": "",
        "discountPercentage": 0.0,
        "mainOrderId": "",
        "mandateId": "",
        "matchedToPurchase": False,
        "orderDate": datetime.now().strftime("%d-%m-%Y"),
        "orderLines": orderlines,
        "orderState": 1,
        "orderSurcharge": 0.0,
        "orderSurchargeVatCodeId": 0,
        "orderType": 0,
        "paymentConditionId": "14",
        "processedBy": "Ronald Kremer",  # TODO
        "processedById": "2",  # TODO
        "projectId": "",
        "reference": "Borrels {}".format(month),
        "totalCreditSqueezeAmount": 0.0,
        "totalDiscountAmount": 0.0,
        "vatScenarioId": 6,
    }


def make_orderline(product_id: int, amount: float, drink_name: str, date_drink: str, discount: bool):
    product = Product.objects.get(alexia_id=product_id)
    from apps.multivers import views
    return OrderLine(date_drink, drink_name,
                     # accountId=product.multivers_id,
                     autoCalculatePrice=True,
                     autoUnmatchToPurchase=False,
                     canChange=True,
                     costCentreId="",
                     costUnitId="",
                     deliveryDate="{} 0:00:00".format(date_drink),
                     description="{} - {}".format(product.multivers_name, drink_name[:30]),
                     discount=float(Settings.objects.get(key=views.DISCOUNT).value) / 100 if discount and product.margin == Product.HAS_MARGIN else 0.0,
                     matchedToPurchase=False,
                     messages=[],
                     orderLineAmount=amount,
                     orderLineType=0,
                     pickListText=False,
                     # pricePer=1,
                     productId=product.multivers_id,
                     quantityBackorder=0,
                     quantityDelivered=amount,
                     quantityOrdered=amount,
                     quantityScale=0,
                     quantityToDeliver=0,
                     warehouseId="",
                     # unit="euro",
                     )


# {
#       "discount": 0,
#       "vatCodeId": 0,
#     }

costumer_IA = {
    "accountManagerId": "",
    "addresses": [],
    "messages": [],
    "applyOrderSurcharge": False,
    "businessNumber": "",
    "canChange": True,
    "chargeVatTypeId": 1,
    "city": "ENSCHEDE",
    "cocCity": "",
    "cocDate": "",
    "cocRegistration": "",
    "collectiveInvoiceSystemId": "",
    "combineInvoicesForElectronicBanking": False,
    "countryId": "",
    "creditLimit": 0.0,
    "creditSqueezeId": "0",
    "currencyId": "",
    "customerGroupId": 0,
    "customerId": "2008001",
    "customerStateId": "A",
    "database": "",
    "dateChanged": "24-2-2012",
    "dateCreated": "28-5-2008",
    "deliveryConditionId": "",
    "discountPercentage": 0.0,
    "email": "",
    "fax": "",
    "fullAddress": "Inter-Actief\r\nT.a.v. penningmeester\r\nPostbus 217\r\n7500 AE   ENSCHEDE",
    "fullDeliveryAddress": "Inter-Actief\r\nT.a.v. penningmeester\r\nPostbus 217\r\n7500 AE   ENSCHEDE",
    "googleMapsDirectionsUrl": "http://maps.google.nl/maps?daddr=Postbus+217\r\n+7500+AE\r\n+ENSCHEDE\r\n&t=m&f=d&layer=t&saddr=",
    "googleMapsUrl": "http://maps.google.nl/maps?q=Postbus+217\r\n+7500+AE\r\n+ENSCHEDE\r\n&t=h&z=15&iwloc=r0&f=d",
    "hasOutstandingBalance": False,
    "homepage": "",
    "intrastatGoodsCodeId": None,
    "intrastatGoodsDistributionId": None,
    "intrastatStatSystemId": None,
    "intrastatTrafficRegionId": None,
    "intrastatTransactionTypeId": "",
    "intrastatTransportTypeId": None,
    "invoiceOnBehalfOfMembers": False,
    "isDunForPayment": True,
    "isInFactoring": False,
    "isPaymentRefRequired": False,
    "isPurchaseOrganization": False,
    "languageId": "",
    "mobilePhone": "",
    "name": "Inter-Actief",
    "organizationId": 12,
    "paymentConditionId": "",
    "person": "",
    "pricelistId": "",
    "printPurchaseDetails": False,
    "purchaseOrganizationId": "",
    "purchaseOrganizationMemberId": "",
    "revenueAccountId": "",
    "shortName": "IA",
    "street1": "T.a.v. penningmeester",
    "street2": "Postbus 217",
    "supplierId": "",
    "telephone": "",
    "usesUBLInvoice": True,
    "vatNumber": "",
    "vatScenarioId": None,
    "vatVerificationDate": "",
    "zipCode": "7500 AE",
}

customer_STRESS = {
    "accountManagerId": "",
    "addresses": [],
    "messages": [],
    "applyOrderSurcharge": False,
    "businessNumber": "",
    "canChange": True,
    "chargeVatTypeId": 1,
    "city": "ENSCHEDE",
    "cocCity": "",
    "cocDate": "",
    "cocRegistration": "",
    "collectiveInvoiceSystemId": "",
    "combineInvoicesForElectronicBanking": False,
    "countryId": "",
    "creditLimit": 0.0,
    "creditSqueezeId": "0",
    "currencyId": "",
    "customerGroupId": 0,
    "customerId": "2008005",
    "customerStateId": "A",
    "database": "",
    "dateChanged": "28-5-2009",
    "dateCreated": "29-5-2008",
    "deliveryConditionId": "",
    "discountPercentage": 0.0,
    "email": "",
    "fax": "",
    "fullAddress": "Stress\r\nT.a.v. penningmeester\r\nPostbus 217\r\n7500 AE   ENSCHEDE",
    "fullDeliveryAddress": "Stress\r\nT.a.v. penningmeester\r\nPostbus 217\r\n7500 AE   ENSCHEDE",
    "googleMapsDirectionsUrl": "http://maps.google.nl/maps?daddr=Postbus+217\r\n+7500+AE\r\n+ENSCHEDE\r\n&t=m&f=d&layer=t&saddr=",
    "googleMapsUrl": "http://maps.google.nl/maps?q=Postbus+217\r\n+7500+AE\r\n+ENSCHEDE\r\n&t=h&z=15&iwloc=r0&f=d",
    "hasOutstandingBalance": True,
    "homepage": "",
    "intrastatGoodsCodeId": None,
    "intrastatGoodsDistributionId": None,
    "intrastatStatSystemId": None,
    "intrastatTrafficRegionId": None,
    "intrastatTransactionTypeId": "",
    "intrastatTransportTypeId": None,
    "invoiceOnBehalfOfMembers": False,
    "isDunForPayment": True,
    "isInFactoring": False,
    "isPaymentRefRequired": False,
    "isPurchaseOrganization": False,
    "languageId": "",
    "mobilePhone": "",
    "name": "Stress",
    "organizationId": 16,
    "paymentConditionId": "",
    "person": "",
    "pricelistId": "",
    "printPurchaseDetails": False,
    "purchaseOrganizationId": "",
    "purchaseOrganizationMemberId": "",
    "revenueAccountId": "",
    "shortName": "STRESS",
    "street1": "T.a.v. penningmeester",
    "street2": "Postbus 217",
    "supplierId": "",
    "telephone": "",
    "usesUBLInvoice": True,
    "vatNumber": "",
    "vatScenarioId": None,
    "vatVerificationDate": "",
    "zipCode": "7500 AE",
}
