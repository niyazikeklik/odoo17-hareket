from odoo import models, fields


class SasRedKodu(models.Model):
    _name = 'sas.red.kodu'
    _description = "Satınalma Sipariş Red Kodları"

    reject_code = fields.Char("Red Kodu")
    name = fields.Char("Red Açıklaması")