from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktParaTalepOnay(models.Model):
    _name = 'harkt.para.talep.onay'
    _inherit = ['mail.thread']
    _description = "Hareket Para Talep Onay"

    para_talep_id = fields.Many2one("harkt.para.talep", "Para Talebi", required=True, ondelete="cascade")
    sequence_no = fields.Integer("Sıra No")
    route = fields.Integer("Adım No", required=True)
    approver_sign = fields.Char("Onaylayan")
    sign_date = fields.Datetime("Onay/Red Tarihi")
    #approval_status = fields.Char("Onay Durumu")
    approval_status = fields.Selection([("REJ","Reddedildi"),("APP","Onaylandı")], "Onay Durumu")
    emp_no = fields.Char("Onayı Beklenen")
    authorize_id = fields.Many2one("res.users", compute="_compute_authorize_id", store=True)
    reject_reason = fields.Char("Red Sebebi")

    @api.depends("emp_no")
    def _compute_authorize_id(self):
        for rec in self:
            rec.authorize_id = self.env["hr.employee"].sudo().search([("emp_no", "=", rec.emp_no)]).user_id.id
