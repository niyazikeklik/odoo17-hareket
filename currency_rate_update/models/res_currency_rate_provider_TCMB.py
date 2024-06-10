# Copyright 2023 Tarık CÖRÜT

import xml.sax
from collections import defaultdict
from datetime import datetime
from urllib.request import urlopen
from xml.sax import make_parser

from odoo import fields, models


class ResCurrencyRateProviderTCMB(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("TCMB", "Turkish Republic Central Bank")],
        ondelete={"TCMB": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "TCMB":
            return super()._get_supported_currencies()  # pragma: no cover

        return [
            "AED",
            "USD",
            "JPY",
            "BGN",
            "CYP",
            "CZK",
            "DKK",
            "EEK",
            "GBP",
            "HUF",
            "LTL",
            "LVL",
            "MTL",
            "PLN",
            "ROL",
            "RON",
            "SEK",
            "SIT",
            "SKK",
            "CHF",
            "ISK",
            "NOK",
            "HRK",
            "RUB",
            "TRL",
            "TRY",
            "AUD",
            "BRL",
            "CAD",
            "CNY",
            "HKD",
            "IDR",
            "ILS",
            "INR",
            "KRW",
            "MXN",
            "MYR",
            "NZD",
            "PHP",
            "SGD",
            "THB",
            "ZAR",
            "EUR",
            "SAR"
        ]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "TCMB":
            return super()._obtain_rates(
                base_currency, currencies, date_from, date_to
            )  # pragma: no cover
        invert_calculation = False
        if base_currency != "TRY":
            invert_calculation = True
            if base_currency not in currencies:
                currencies.append(base_currency)
        # Depending on the date range, different URLs are used
        url = "https://evds2.tcmb.gov.tr/service/evds/startDate="+date_from.strftime("%d-%m-%Y")+"&endDate="+date_to.strftime("%d-%m-%Y")+"&type=xml&key=KCwftEga4C&series="
        i = 0
        for currency in currencies:
            if i == 0:
                url = url+"TP.DK."+currency+".A"
            else:
                url = url+"-TP.DK."+currency+".A"
            i = i + 1

        handler = TcmbRatesHandler(currencies, date_from, date_to)
        with urlopen(url, timeout=10) as response:
            parser = make_parser()
            parser.setContentHandler(handler)
            parser.parse(response)
        content = handler.content
        if invert_calculation:
            for k in content.keys():
                base_rate = float(content[k][base_currency])
                for rate in content[k].keys():
                    content[k][rate] = content[k][rate] / base_rate
                content[k]["TRY"] = 1.0 / base_rate
        return content


class TcmbRatesHandler(xml.sax.ContentHandler):
    def __init__(self, currencies, date_from, date_to):
        self.currencies = currencies
        self.date_from = date_from
        self.date_to = date_to
        self.date = None
        self.content = defaultdict(dict)
        self.current_data = ""

    def startElement(self, name, attrs):
        self.current_data = name

    def characters(self, content):
        if self.current_data == "Tarih":
            self.date = datetime.strptime(content, "%d-%m-%Y").date()
        elif self.current_data[:6] == "TP_DK_":
            currency = self.current_data[6:9]
            rate = content
            if (
                    (self.date_from is None or self.date >= self.date_from)
                    and (self.date_to is None or self.date <= self.date_to)
                    and currency in self.currencies
            ):
                self.content[self.date.isoformat()][currency] = 1/float(rate)
