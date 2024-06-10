from datetime import datetime
import json

from odoo import fields, models
from odoo.exceptions import UserError


class TrMutIfsVeriCekWizard(models.TransientModel):
    _name = 'tr.mut.ifs.veri.cek.wizard'
    _description = 'TR Mutabakat IFS Veri Çekme Sihirbazı'

    mut_tarih = fields.Date("Mutabakat Tarihi")
    mut_vkn_tckn = fields.Char("Mutabakat Vkn/Tckn", help="Tümü için % giriniz", default="%")
    mut_hareket_goren = fields.Boolean("Sadece Hareket Görenler",
                                       help="Cari mutabakat çalıştırırken işaretlenirse sadece o tarihe ait hareket gören cariler gelir, eğer işaretlenmezse tüm cariler gelir",
                                       default=False)

    def action_mutabakat(self):
        company = self.env["res.company"].sudo().search([("id", "in", self._context.get('allowed_company_ids'))], limit=1)
        self.env["tr.mut"]._ifs_cari_mutabakat_getir(company.ifs_sirket_kodu, self.mut_tarih.strftime("%d.%m.%Y")  if self.mut_tarih else False,
                                                     self.mut_vkn_tckn, 1 if self.mut_hareket_goren else 0)

    def action_kur_farki(self):
        company = self.env["res.company"].sudo().search([("id", "in", self._context.get('allowed_company_ids'))],
                                                        limit=1)
        self.env["tr.mut.kf"]._ifs_kur_farki_getir(company.ifs_sirket_kodu, self.mut_tarih.strftime("%d.%m.%Y") if self.mut_tarih else False,
                                                     self.mut_vkn_tckn)

    def action_kdv2(self):
        company = self.env["res.company"].sudo().search([("id", "in", self._context.get('allowed_company_ids'))],
                                                        limit=1)
        self.env["tr.mut.kdv2"]._ifs_kdv2_getir(company.ifs_sirket_kodu, self.mut_tarih.strftime("%d.%m.%Y") if self.mut_tarih else False,
                                                     self.mut_vkn_tckn)

