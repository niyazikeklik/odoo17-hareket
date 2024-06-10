from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktNakitHesap(models.Model):
    _name = 'harkt.nakit.hesap'
    _description = "Hareket Nakit Hesap"

    tr_company_id = fields.Many2one("tr.company","Şirket", required=True)
    name = fields.Char("Kısa Adı", required=True)
    description = fields.Char("Açıklama", required=True)
    currency_id  =fields.Many2one("res.currency","Döviz")
    account_no = fields.Char("Hesap No")
    reference = fields.Char("Hesap Referansı")
    def delete(self, company, name):
        tr_company_id = self.env["tr.company"].search([("code", "=", company)]).id
        self.env.cr.execute("delete from harkt_nakit_hesap where tr_company_id = "+str(tr_company_id)+" and name='"+name+"'")
        return True

    @api.model
    def write_or_create(self, vals):
        tr_company_id = self.env["tr.company"].search([("code", "=", vals.get("company"))]).id
        rec = self.env["harkt.nakit.hesap"].search(
            [("name", "=", vals.get("name")),
             ("tr_company_id","=",tr_company_id)
             ])
        result = False
        currency_id = self.env["res.currency"].search([("name", "=", vals.get("currency"))]).id

        data = {
                "tr_company_id": tr_company_id,
                "description": vals.get("description"),
                "name": vals.get("name"),
                "currency_id": currency_id,
                "account_no": vals.get("account_no"),
                "reference": vals.get("reference")
            }
        if len(rec) == 0:
            ret = self.env["harkt.nakit.hesap"].create(data)
            result = True
        else:
            ret = rec.write(data)
            result = True
        return result

