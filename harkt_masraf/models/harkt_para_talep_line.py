from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktParaTalepLine(models.Model):
    _name = 'harkt.para.talep.line'
    _description = "Hareket Para Talep Satırı"
    para_talep_id = fields.Many2one("harkt.para.talep","Para Talebi", ondelete="cascade")
    satir_no = fields.Integer("Satır No")
    ongrup_id = fields.Many2one("harkt.masraf.ongrup","Ön Grup", required=True)

    masraf_turu_id = fields.Many2one("harkt.masraf.turu", string="Masraf Türü", required=True,
                                     domain="[('tr_company_id', '=', tr_company_id), ('masraf_ongrup_id', '=', ongrup_id)]")
    tr_company_id = fields.Many2one("tr.company", string="Grup Şirket", related="para_talep_id.tr_company_id")
    project_id =fields.Many2one("harkt.proje", related="para_talep_id.project_id", string="Proje")
    bolge_id = fields.Many2one("harkt.muhasebe.kodu", string="Bölge", domain="[('tr_company_id', '=', tr_company_id), ('kod_yapisi','=','J')]")

    harici = fields.Boolean("Harici", default=False)
    talep_edilen_id = fields.Many2one("res.users", "Talep Edilen Kişi")
    varlik_id = fields.Many2one("harkt.muhasebe.kodu", string="Varlık",
                                           domain="[('tr_company_id','=',tr_company_id),('detay_secenek_id.name','=',detay)]")
    miktar = fields.Float("Miktar")
    tutar = fields.Float("Tutar")
    toplam_tutar = fields.Float("Toplam Tutar", compute="_compute_toplam_tutar")
    country_id = fields.Many2one("res.country", "Ülke")
    kiralik_plaka = fields.Char("Harici Araç Plaka")
    aciklama = fields.Char("Açıklama")
    harici_kimlik_no = fields.Char("Harici Kişi Kimlik No")
    harici_adres= fields.Char("Harici Kişi Adres")
    harici_telefon = fields.Char("Harici Kişi Telefon")
    harici_iban = fields.Char("Harici Kişi IBAN")
    harici_ad_soyad = fields.Char("Harici Kişi Ad Soyad")
    kiralik = fields.Boolean("Kiralık", default=False)
    is_takip_no = fields.Char("İş Takip No", readonly = True)
    masraf_id = fields.Many2one("harkt.masraf", "Masraf")
    notlar = fields.Char("Notlar")
    odeme_tarihi = fields.Date("Ödeme Tarihi")
    talep_bakiye_tutari = fields.Float("Talep Bakiye Tutarı")
    detay = fields.Char("Konut/Araç", related="masraf_turu_id.detay_id.name", store=True)
    detay_zorunlu = fields.Boolean("Detay Zorunlu", related="masraf_turu_id.detay_zorunlu", store=True)
    bolge_zorunlu = fields.Boolean("Bölge Zorunlu", related="masraf_turu_id.bolge_zorunlu", store=True)
    supercall = fields.Boolean(string="Supercall")

    currency_rate =fields.Float("Kur", compute="_compute_currency_rate", store=True, readonly=False, digits=(12,6))

    def _compute_toplam_tutar(self):
        for rec in self:
            rec.toplam_tutar = rec.miktar * rec.tutar

    @api.depends("para_talep_id")
    def _compute_currency_rate(self):
        for rec in self:
            if rec.para_talep_id.currency_id and rec.para_talep_id.currency_id.name == "TRY":
                rec.currency_rate = 1
            elif rec.para_talep_id.currency_id:
                date = rec.para_talep_id.talep_tarihi
                company_id = self.env.user.company_id.id
                # the subquery selects the last rate before 'date' for the given currency/company
                query = """SELECT c.id, (SELECT r.rate FROM res_currency_rate r
                                                  WHERE r.currency_id = c.id and r.name <= %s
                                                    AND (r.company_id IS NULL OR r.company_id = """+str(company_id)+""")
                                               ORDER BY r.company_id, r.name DESC
                                                  LIMIT 1) AS rate
                                   FROM res_currency c
                                   WHERE c.id = """+str(rec.para_talep_id.currency_id.id)
                self._cr.execute(query,(date,))
                result = self._cr.fetchall()
                if result[0][1] != 0:
                    rec.currency_rate = 1/result[0][1]
                else:
                    rec.currency_rate = 1
            else:
                rec.currency_rate = 1


    @api.onchange("ongrup_id")
    def on_change_ongrup_id(self):
        self.masraf_turu_id = False


    @api.onchange("masraf_turu_id")
    def on_change_masraf_turu_id(self):
        self.varlik_id = False

    @api.model
    def remove_func(self, vals):
        talep = self.env["harkt.para.talep"].search([("talep_no", "=", vals.get("talep_no"))])
        self.env.cr.execute("""delete from harkt_para_talep_line where para_talep_id=%s and satir_no=%s""",
                            (talep.id, vals.get("satir_no"),))
        return True

    @api.model
    def write_or_create(self, vals):
        try:
            tr_company_id = self.env["tr.company"].search([("code", "=", vals.get("company_id"))]).id
            para_talep = self.env["harkt.para.talep"].search([("talep_no","=",vals.get("para_talep_no")),
                                                              ("tr_company_id", "=", tr_company_id)])
            rec = self.env["harkt.para.talep.line"].search(
                [("para_talep_id", "=", para_talep.id),
                 ("tr_company_id", "=", tr_company_id),
                 ("satir_no","=", vals.get("satir_no"))
                 ])
            print(vals)
            emp = self.env["hr.employee"].sudo().search([("emp_no", "=", vals.get("talep_edilen_id"))])
            print(emp)
            talep_eden_id = None
            if len(emp) >0 and vals.get("talep_edilen_id"):
                emp = emp[0]
                if emp.user_id:
                    talep_eden_id = emp.user_id.id
            ongrup_id = None
            ongrup = self.env["harkt.masraf.ongrup"].search([("ongrup_kodu", "=", vals.get("ongrup_no"))])
            if len(ongrup) > 0:
                ongrup_id = ongrup[0].id
            masraf_turu_id = None
            masraf_turu = self.env["harkt.masraf.turu"].search([("masraf_turu_kodu", "=", vals.get("masraf_turu")),
                                                                 ("tr_company_id", "=", tr_company_id)])
            print(masraf_turu)
            if len(masraf_turu) > 0:
                masraf_turu_id = masraf_turu[0].id
            country_id = None
            country = self.env["res.country"].search([("code", "=", vals.get("country"))])
            if len(country) > 0:
                country_id = country[0].id
            varlik_id = None
            varlik = self.env["harkt.muhasebe.kodu"].search([("code", "=", vals.get("varlik")),
                                                             ('tr_company_id', '=', tr_company_id)])
            if len(varlik) > 0:
                varlik_id = varlik[0].id
            bolge_id = None
            bolge = self.env["harkt.muhasebe.kodu"].search([("code", "=", vals.get("bolge")),
                                                             ('tr_company_id', '=', tr_company_id),
                                                            ('kod_yapisi', '=', 'J')])
            if len(bolge) > 0:
                bolge_id = bolge[0].id
            data = {
                "tr_company_id": tr_company_id,
                "para_talep_id": para_talep.id,
                "satir_no": vals.get("satir_no"),
                "talep_edilen_id": talep_eden_id,
                "ongrup_id":ongrup_id,
                "masraf_turu_id":masraf_turu_id,
                "miktar": vals.get("miktar"),
                "tutar": vals.get("tutar"),
                "aciklama": vals.get("aciklama"),
                "country_id": country_id,
                "varlik_id":varlik_id,
                "bolge_id":bolge_id,
                "harici": True if vals.get("harici")=="TRUE" else False,
                "harici_ad_soyad": vals.get("harici_ad_soyad"),
                "harici_kimlik_no": vals.get("harici_kimlik_no"),
                "harici_adres": vals.get("harici_adres"),
                "harici_telefon": vals.get("harici_telefon"),
                "harici_iban": vals.get("harici_iban"),
                "kiralik": vals.get("kiralik"),
                "kiralik_plaka": vals.get("kiralik_plaka"),
                "currency_rate": vals.get("doviz_kuru"),
                "supercall": True
            }
            if len(rec) == 0:
                ret = self.create(data)
                result = True
            else:
                ret = rec.write(data)
                result = True
        except Exception as ex:
            result = ex
        return result


    def unlink(self):
        conn = self.env["oracle.conn"].connect(1, False)
        ret = {}
        try:
            c = conn.cursor()
            # ret = super(HarktMasrafLine, self).unlink()

            c.execute("""
            BEGIN
                ODOO_PORTAL_API.masraf_satir_sil_odoo2_ifs(:TALEP_ID,:LINE_NO);
            END;
            """,
                      TALEP_ID=self.para_talep_id.talep_no,
                      LINE_NO=self.satir_no)
            ret = self.env.cr.execute("""delete from harkt_para_talep_line where para_talep_id=%s and satir_no=%s""",
                                      (self.para_talep_id.id, self.satir_no,))
            conn.commit()
        except Exception as ex:
            conn.rollback()
            print(ex)
            raise UserError(self.env["oracle.conn"].simplify_error_message(ex))

        return ret



