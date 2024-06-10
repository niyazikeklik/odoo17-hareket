from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktKdv(models.Model):
    _name = 'harkt.kdv'
    _description = "Hareket KDV Kodları"
    _rec_name ="kdv_kodu"

    tr_company_id =fields.Many2one("tr.company","Şirket", required=True)
    kdv_kodu = fields.Char("Kdv Kodu", required=True)
    kdv_orani = fields.Float("Kdv Oranı")
    vergi_kodu = fields.Char("Vergi Kodu")

    @api.model
    def write_or_create(self, vals):
        tr_company_id = self.env["tr.company"].search([("code","=",vals.get("company"))]).id
        vals["tr_company_id"] = tr_company_id
        del vals['company']
        rec = self.env["harkt.kdv"].search([("tr_company_id", "=", tr_company_id), ("kdv_orani","=",vals.get("kdv_orani"))])
        result = False
        if len(rec) == 0:
            ret = self.env["harkt.kdv"].create(vals)
            result = True
        else:
            ret = rec.write({
                "kdv_kodu": vals.get("kdv_kodu"),
                "vergi_kodu": vals.get("vergi_kodu")
            })
            result = True
        return result

    def delete(self, company, kdv_orani):
        tr_company_id = self.env["tr.company"].search([("code", "=", company)]).id
        self.env.cr.execute("delete from harkt_kdv where tr_company_id = "+str(tr_company_id)+" and kdv_orani="+str(kdv_orani))
        return True
