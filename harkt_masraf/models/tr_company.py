from odoo import models, fields


class TrCompany(models.Model):
    _inherit = 'tr.company'

    para_talebi =fields.Boolean("Para Talebi", default=False)
 