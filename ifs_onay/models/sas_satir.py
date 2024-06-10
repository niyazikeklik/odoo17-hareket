from odoo import models, fields


class SasSatir(models.Model):
    _name = 'sas.satir'
    _description = "Satınalma Sipariş Satırı"

    baslik_id = fields.Many2one("sas.baslik","Sipariş", required=True)
    line_no = fields.Char("Satır No", required=True)
    release_no = fields.Char("Yayın No")
    part_no = fields.Char("Malzeme No")
    description = fields.Char("Malzeme Açıklaması")
    quantity = fields.Float("Miktar")
    buy_unit_meas = fields.Char("Ölçü Birimi")
    unit_price = fields.Float("Birim Fiyat")
    total_price = fields.Float("Toplam Fiyat")
    gross_total_price = fields.Float("Toplam Fiyat Kdv Dahil")
    alt_proje_no = fields.Char("Alt Proje No")
    alt_proje_adi = fields.Char("Alt Proje Adı")
    aktivite_no = fields.Char("Aktivite No")
    aktivite_adi = fields.Char("Aktivite Adı")
    notlar = fields.Char("Notlar")
