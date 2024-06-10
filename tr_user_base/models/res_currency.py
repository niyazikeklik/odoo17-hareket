from odoo import models, fields, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'
    _order =  "active,sequence asc"

    sequence = fields.Integer("Sequence")