from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktDetay(models.Model):
    _name = 'harkt.detay'
    _description = "Hareket Detay Seçenek"

    name = fields.Char("Hareket Detay Türü", required=True)

    def delete(self, name):
        self.env.cr.execute("delete from harkt_detay where name ='"+name+"'")
        return True