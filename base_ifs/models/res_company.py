from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    ifs_link = fields.Char("IFS Link")
    ifs_sirket_kodu = fields.Char("IFS Şirket Kodu")
