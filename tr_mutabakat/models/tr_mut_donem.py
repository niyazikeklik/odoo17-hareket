from odoo import models, fields
from odoo.exceptions import UserError


class TrMutDonem(models.Model):
    _name = 'tr.mut.donem'
    _description = "E-Mutabakat Dönemi"
    _order = "name desc"

    name = fields.Char("Dönem Adı")

    def write(self, vals):
        raise UserError("Dönem adı değiştirilemez")

