from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktProje(models.Model):
    _name = 'harkt.proje'
    _description = "Hareket Proje"
    _order ="name"

    tr_company_id = fields.Many2one("tr.company","Şirket", required=True)
    code = fields.Char("Proje Kodu", required=True)
    name = fields.Char("Proje Adı", required=True)
    state = fields.Char("Durum")
    active = fields.Boolean("Aktif?", compute="_compute_active", store=True)

    @api.depends("state")
    def _compute_active(self):
        for rec in self:
            if rec.state == "Cancelled" or rec.state == "Completed":
                rec.active = False
            else:
                rec.active = True



    def delete(self, company, code):
        tr_company_id = self.env["tr.company"].search([("code", "=", company)]).id
        self.env.cr.execute("delete from harkt_proje where tr_company_id = "+str(tr_company_id)+" and code='"+code+"'")
        return True

    @api.model
    def write_or_create(self, vals):
        tr_company_id = self.env["tr.company"].search([("code", "=", vals.get("company"))]).id
        rec = self.env["harkt.proje"].search(
            [("code", "=", vals.get("code")),
             ("tr_company_id","=",tr_company_id)
             ])
        result = False

        data = {
                "tr_company_id": tr_company_id,
                "code": vals.get("code"),
                "name": vals.get("name"),
                "state": vals.get("state")
            }
        if len(rec) == 0:
            ret = self.env["harkt.proje"].create(data)
            result = True
        else:
            ret = rec.write(data)
            result = True
        return result

