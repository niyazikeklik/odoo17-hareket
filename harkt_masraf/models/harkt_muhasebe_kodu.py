from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktMuhasebeKodu(models.Model):
    _name = 'harkt.muhasebe.kodu'
    _description = "Hareket Muhasebe Kodu"

    tr_company_id = fields.Many2one("tr.company","Şirket", required=True)
    code = fields.Char("Kodu", required=True)
    name = fields.Char("Adı", required=True)
    valid_from = fields.Date("Geçerlilik Başlangıcı", required=True)
    valid_to = fields.Date("Geçerlilik Bitiş", required=True)
    kod_yapisi = fields.Selection([("A","HESAP"),
                                 ("B","GY"),
                                 ("C","GC"),
                                 ("D","CH"),
                                 ("E","SK"),
                                 ("F","PRJ"),
                                 ("G","MG"),
                                 ("H","DTY"),
                                 ("I","DOVIZ"),
                                 ("J","BOLGE")], string="Kod Parça Yapısı")
    detay_secenek_id = fields.Many2one("harkt.detay", "Detay Seçeneği")
    state = fields.Char("Durum")

    def delete(self, company, kod_yapisi, code):
        tr_company_id = self.env["tr.company"].search([("code", "=", company)]).id
        self.env.cr.execute("delete from harkt_muhasebe_kodu where tr_company_id = "+str(tr_company_id)+" and code='"+code+"' and kod_yapisi ='"+kod_yapisi+"'")
        return True

    @api.model
    def write_or_create(self, vals):
        tr_company_id = self.env["tr.company"].search([("code", "=", vals.get("company"))]).id
        detay_secenek_id = self.env["harkt.detay"].search([("name", "=", vals.get("detay_secenek"))]).id
        rec = self.env["harkt.muhasebe.kodu"].search(
            [("code", "=", vals.get("code")),
             ("tr_company_id","=",tr_company_id),
             ("kod_yapisi", "=", vals.get("kod_yapisi")),
             ])
        result = False

        data = {
                "tr_company_id": tr_company_id,
                "code": vals.get("code"),
                "name": vals.get("name"),
                "detay_secenek_id": detay_secenek_id,
                "kod_yapisi": vals.get("kod_yapisi"),
                "valid_from": vals.get("valid_from"),
                "valid_to": vals.get("valid_to")
            }
        if len(rec) == 0:
            ret = self.env["harkt.muhasebe.kodu"].create(data)
            result = True
        else:
            ret = rec.write(data)
            result = True
        return result

