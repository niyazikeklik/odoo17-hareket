from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktMasrafTuru(models.Model):
    _name = 'harkt.masraf.turu'
    _description = "Hareket Masraf Turu"

    tr_company_id = fields.Many2one("tr.company", "Şirket")
    masraf_ongrup_id = fields.Many2one("harkt.masraf.ongrup", "Öngrup", required=True)
    masraf_turu_kodu = fields.Char("Masraf Türü Kodu", required=True)
    name = fields.Char("Masraf Türü Adı", required=True)
    satinalma_grup_kodu = fields.Char("Satınalma Grup Kodu")
    satinalma_grup_adi = fields.Char("Satınalma Grup Adı")
    proje_zorunlu = fields.Boolean("Proje Zorunlu", default=False)
    detay_zorunlu = fields.Boolean("Detay Zorunlu", default=False)
    site_zorunlu = fields.Boolean("Site Zorunlu", default = False)
    bolge_zorunlu = fields.Boolean("Bölge Zorunlu", default = False)
    gider_cesidi_kodu = fields.Char("Gider Çeşidi Kodu")
    gider_cesidi_adi = fields.Char("Gider Çeşidi Adı")
    detay_id = fields.Many2one("harkt.detay", string="Detay")
    #detay = fields.Selection([("ARAC","ARAC"), ("KONUT","KONUT"),("YOK","YOK")], string="Detay")
    harcama_toleransi = fields.Float("Harcama Toleransı")

    def delete(self, masraf_turu_kodu):
        self.env.cr.execute("delete from harkt_masraf_turu where masraf_turu_kodu = '"+masraf_turu_kodu+"'")
        return True

    @api.model
    def write_or_create(self, vals):
        print(vals)
        rec = self.env["harkt.masraf.turu"].search(
            [("masraf_turu_kodu", "=", vals.get("masraf_turu_kodu"))])
        tr_company_id = self.env["tr.company"].search([("code", "=", vals.get("company"))]).id
        detay_id = self.env["harkt.detay"].search([("name", "=", vals.get("detay_kodu"))]).id
        ongrup_id = self.env["harkt.masraf.ongrup"].search([("ongrup_kodu", "=", vals.get("ongrup_kodu"))]).id
        result = False

        data = {
                "masraf_turu_kodu": vals.get("masraf_turu_kodu"),
                "tr_company_id": tr_company_id,
                "masraf_ongrup_id": vals.get("masraf_ongrup_id"),
                "name": vals.get("name"),
                "satinalma_grup_kodu": vals.get("satinalma_grup_kodu"),
                "satinalma_grup_adi": vals.get("satinalma_grup_adi"),
                "proje_zorunlu": vals.get("proje_zorunlu"),
                "detay_zorunlu": vals.get("detay_zorunlu"),
                "site_zorunlu": vals.get("site_zorunlu"),
                "bolge_zorunlu": vals.get("bolge_zorunlu"),
                "gider_cesidi_kodu": vals.get("gider_cesidi_kodu"),
                "gider_cesidi_adi": vals.get("gider_cesidi_adi"),
                "detay_id": detay_id,
                "masraf_ongrup_id": ongrup_id,
                "harcama_toleransi": vals.get("harcama_toleransi")
            }
        if len(rec) == 0:
            ret = self.env["harkt.masraf.turu"].create(data)
            result = True
        else:
            ret = rec.write(data)
            result = True
        return result
