from pprint import pprint

import django
from fractions import Fraction as frac

if __name__ == "__main__":
    django.setup()
    from apps.multivers.tools import Multivers

    products = [
        (12, frac(123348, 100), 2),
        (4, frac(29000, 100), 2),
        (5, frac(36470, 100), 2),
        (7, frac(6496, 100), 1),
        (1, frac(899, 100), 1),
        (1, frac(928, 100), 1),
        (1, frac(899, 100), 1),
        (1, frac(1199, 100), 1),
        (2, frac(3994, 100), 1),
        (1, frac(1831, 100), 1),
        (1, frac(1445, 100), 1),
        (4, frac(724, 100), 2),
        (6, frac(2370, 100), 2),
        (1, -frac(30, 100), 2),
    ]

    btw_tot = [frac(0), frac(0)]
    btw_per = [frac(6, 100), frac(21, 100)]

    for qnt, amount, cat in products:
        amount /= qnt
        btw_tot[cat-1] += qnt * round(amount * btw_per[cat-1], 2)

    print(btw_tot)


    # multivers = Multivers(None)
    # response = multivers._post("MVL48759/SupplierInvoice", data={
    #     "canChange": True,
    #     "fiscalYear": 2018,
    #     "invoiceDate": "01-01-2018",
    #     "invoiceId": "18100063",
    #     "journalId": "IC",
    #     "journalSection": "1",
    #     "journalTransaction": 25,
    #     "paymentConditionId": "14",
    #     "paymentReference": "0123456789012345",
    #     "periodNumber": 1,
    #     "processedBy": "Pieter Bos",
    #     "processedById": "38",
    #     "reference": "example description",
    #     "supplierId": "2008008",
    #     "supplierInvoiceLines": [{
    #         "accountId": "0",
    #         "canChange": True,
    #         "creditAmount": 0.0,
    #         "creditAmountCur": 0.0,
    #         "debitAmount": 7.24,
    #         "debitAmountCur": 7.24,
    #         "description": "Schoonmaakmiddelen",
    #         "journalSection": 0,
    #         "transactionDate": "01-01-2018",
    #         "vatCodeId": 2,
    #         "vatType": 0
    #     }],
    #     "vatOnInvoice": True,
    #     "vatScenarioId": 1,
    #     "vatTransactionLines": [{
    #         "amountTurnoverCur": 176.91,
    #         "canChange": True,
    #         "currencyId": "",
    #         "fiscalYear": 2018,
    #         "vatAmountCur": 10.61,
    #         "vatCodeId": 1,
    #         "vatScenarioId": 1,
    #         "vatType": 0
    #     }, {
    #         "amountTurnoverCur": 1918.82,
    #         "canChange": True,
    #         "currencyId": "",
    #         "fiscalYear": 2018,
    #         "vatAmountCur": 402.96,
    #         "vatCodeId": 2,
    #         "vatScenarioId": 1,
    #         "vatType": 0
    #     }]
    # })
    #
    # pprint(response)
