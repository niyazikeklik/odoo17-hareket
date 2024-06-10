from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktMasrafOngrup(models.Model):
    _name = 'harkt.masraf.ongrup'
    _description = "Hareket Masraf Öngrup"
    _rec_name = "display_name"

    ongrup_kodu =fields.Char("Öngrup Kodu", required=True)
    ongrup_adi = fields.Char("Öngrup adı", required=True)

    display_name = fields.Char("Adı", compute="_compute_display_name", store=True)

    @api.depends("ongrup_kodu", "ongrup_adi")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.ongrup_kodu +"-"+rec.ongrup_adi

    def delete(self, ongrup_kodu):
        self.env.cr.execute("delete from harkt_masraf_ongrup where ongrup_kodu = '"+ongrup_kodu+"'")
        return True

    @api.model
    def write_or_create(self, vals):
        rec = self.env["harkt.masraf.ongrup"].search(
            [("ongrup_kodu", "=", vals.get("ongrup_kodu"))])
        result = False
        if len(rec) == 0:
            ret = self.env["harkt.masraf.ongrup"].create(vals)
            result = True
        else:
            ret = rec.write({
                "ongrup_kodu": vals.get("ongrup_kodu"),
                "ongrup_adi": vals.get("ongrup_adi")
            })
            result = True
        return result

