from odoo import models, fields


class SasOnay(models.Model):
    _name = 'sas.onay'
    _description = "Satınalma Sipariş Onayı"
    _order ="sequence_no"

    baslik_id = fields.Many2one("sas.baslik","Sipariş", required=True)
    change_order_no = fields.Char("Değ. Emri No")
    sequence_no = fields.Integer("Sıra No")
    route = fields.Integer("Adım No", required=True)
    approval_rule = fields.Char("Onay Kuralı")
    approver_sign = fields.Char("Onaylayan")
    date_approved = fields.Datetime("Onay Tarihi")
    revoked_sign = fields.Char("Reddeden")
    date_revoked = fields.Datetime("Red Tarihi")
    authorize_id = fields.Char("Onayı Beklenen Id")
    authorize_name = fields.Char("Onayı Beklenen Adı")
