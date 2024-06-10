from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktMasrafLine(models.Model):
    _name = 'harkt.masraf.line'
    _description = "Hareket Masraf Satırı"

    masraf_id = fields.Many2one("harkt.masraf","Masraf")
    satir_no =fields.Integer("Satır No")
    tr_company_id = fields.Many2one("tr.company", string="Grup Şirket", related="masraf_id.tr_company_id")
    bolge_id = fields.Many2one("harkt.muhasebe.kodu", string="Bölge",
                               domain="[('tr_company_id', '=', tr_company_id), ('kod_yapisi','=','J')]")
    currency_id = fields.Many2one("res.currency", store=True, related="masraf_id.currency_id")
    para_talep_id = fields.Many2one("harkt.para.talep", "İlgili Para Talep No",
                                    domain="[('talep_satir_ids.talep_edilen_id','=',kisi_id),('state','in',['ODENDI','ODENECEK']),('currency_id','=',currency_id)]")
    fis_tarihi = fields.Date(string="Fiş Tarihi")
    kisi_id = fields.Many2one("res.users", "Kişi")
    bolum_id = fields.Many2one("harkt.muhasebe.kodu", string="Bölüm", related="masraf_id.bolum_id")
    project_id = fields.Many2one("harkt.proje", "Proje",
                                 domain="[('tr_company_id', '=', tr_company_id)]", index=True)
    activity_id = fields.Many2one("harkt.aktivite", "Aktivite", domain="[('project_id', '=', project_id)]")
    iade_hesap_id = fields.Many2one("harkt.nakit.hesap", string="İade Hesap Kodu", domain="[('tr_company_id','=',tr_company_id)]")
    personel_virmani = fields.Boolean("Personel Virmanı", default=False)
    virman_calisan_id = fields.Many2one("hr.employee.public", string="Virman Yapılacak Çalışan")
    maas_kesintisi = fields.Boolean("Maaş Kesintisi", default=False)
    harici_arac_plaka = fields.Char("Harici Araç Plaka")
    ongrup_id = fields.Many2one("harkt.masraf.ongrup", "Ön Grup", required=True)
    masraf_turu_id = fields.Many2one("harkt.masraf.turu", string="Masraf Türü", required=True, domain="[('tr_company_id', '=', tr_company_id), ('masraf_ongrup_id', '=', ongrup_id)]")
    gider_yeri_id = fields.Many2one("harkt.muhasebe.kodu", string="Gider Yeri", domain="[('tr_company_id', '=', tr_company_id), ('kod_yapisi','=','B')]")
    miktar = fields.Float("Miktar", required=True, default=1)
    currency_id = fields.Many2one("res.currency", related="masraf_id.currency_id", string = "Para Birimi")
    tutar = fields.Float("Tutar", required=True)
    tutar_try = fields.Float("TL Tutar", required=True, compute="_compute_tutar_try", readonly=False, store=True)
    tutar_kdv_haric = fields.Float("Tutar KDV Hariç", compute="_compute_tutar_kdv_haric", store=True)
    tutar_try_kdv_haric= fields.Float("Tutar TRY KDV Hariç", compute="_compute_tutar_try_kdv_haric", store=True)
    tedarikci_belge_no = fields.Char("Tedarikçi/Belge No")
    kdv_orani = fields.Float("Kdv Oranı")
    kiralik = fields.Boolean("Kiralık", default=False)
    firma_araci_plaka_id = fields.Many2one("harkt.muhasebe.kodu", string="Firma Aracı Plaka",
                                           domain="[('tr_company_id','=',tr_company_id),('detay_secenek_id.name','=','ARAC')]")
    ev_kodu_id = fields.Many2one("harkt.muhasebe.kodu", string="Ev Kodu",
                                           domain="[('tr_company_id','=',tr_company_id),('detay_secenek_id.name','=','KONUT')]")
    is_emri_no = fields.Char("İş Emri No")
    mixed_payment_no = fields.Integer("Ödeme No")
    odeme_durum =fields.Selection([("Ödendi","Ödendi"), ("Ödenmedi","Ödenmedi")], string="Tedarikçiye Ödeme Durum", required=True)
    aciklama = fields.Text("Açıklama")
    para_talebi_durum = fields.Selection([("Para Talebi Oluştur", "Para Talebi Oluştur"), ("Para Talebi Var", "Para Talebi Var")], string="Para Talebi?",
                                         required=True)
    belge_durum = fields.Selection([("Belgeli", "Belgeli"), ("Belgesiz", "Belgesiz")], string="Belge Durum", required=True)
    belge_sonradan = fields.Boolean("Belge Sonradan Gelecek(Satınalma siparişi)", default=False)
    avans_iadesi = fields.Boolean("Avans İadesi", default=False)
    detay = fields.Char("Detay", related="masraf_turu_id.detay_id.name", store=True)
    detay_zorunlu = fields.Boolean("Detay Zorunlu", related="masraf_turu_id.detay_zorunlu", store=True)
    proje_zorunlu = fields.Boolean("Proje Zorunlu", related="masraf_turu_id.proje_zorunlu", store=True)
    bolge_zorunlu = fields.Boolean("Bölge Zorunlu", related="masraf_turu_id.bolge_zorunlu", store=True)
    supercall = fields.Boolean(string="Supercall")


    @api.depends("tutar","fis_tarihi")
    def _compute_tutar_try(self):
        for rec in self:
            currency_rate = 1
            if rec.masraf_id.currency_id.name == "TRY":
                currency_rate = 1
            elif rec.masraf_id.currency_id and rec.fis_tarihi:

                date = rec.fis_tarihi
                company_id = self.env.user.company_id.id
                query = """SELECT c.id, (SELECT r.rate FROM res_currency_rate r
                                                                      WHERE r.currency_id = c.id and r.name <= %s
                                                                        AND (r.company_id IS NULL OR r.company_id = """ + str(
                    company_id) + """)
                                                                   ORDER BY r.company_id, r.name DESC
                                                                      LIMIT 1) AS rate
                                                       FROM res_currency c
                                                       WHERE c.id = """ + str(rec.masraf_id.currency_id.id)
                self._cr.execute(query, (date,))
                result = self._cr.fetchall()
                if result[0][1] != 0:
                    currency_rate = 1 / result[0][1]
                else:
                    currency_rate = 1
            rec.tutar_try = currency_rate * rec.tutar

    @api.onchange("avans_iadesi")
    def on_avans_iadesi_change(self):
        if self.avans_iadesi ==True:
            self.personel_virmani = False
            self.maas_kesintisi = False

    @api.onchange("personel_virmani")
    def on_personel_virmani_change(self):
        if self.personel_virmani == True:
            self.avans_iadesi = False
            self.maas_kesintisi = False

    @api.onchange("maas_kesintisi")
    def on_maas_kesintisi_change(self):
        if self.maas_kesintisi == True:
            self.personel_virmani = False
            self.avans_iadesi = False

    @api.onchange("masraf_turu_id")
    def on_masraf_turu_change(self):
        self.firma_araci_plaka_id = False
        self.ev_kodu_id =False

    @api.onchange("belge_durum")
    def on_change_belgesiz(self):
        if self.belge_durum == "Belgeli":
            self.kdv_orani = 0
            self.tedarikci_belge_no = False
        elif self.belge_durum == "Belgesiz":
            self.belge_sonradan = False

    @api.onchange("project_id")
    def on_change_project_id(self):
        self.activity_id = False

    @api.onchange("ongrup_id")
    def on_change_ongrup_id(self):
        self.masraf_turu_id = False

    @api.depends("tutar","kdv_orani")
    def _compute_tutar_kdv_haric(self):
        for rec in self:
           rec.tutar_kdv_haric = rec.tutar*100/(100+rec.kdv_orani)

    @api.depends("tutar", "kdv_orani")
    def _compute_tutar_try_kdv_haric(self):
        for rec in self:
           rec.tutar_try_kdv_haric = rec.tutar_try*100/(100+rec.kdv_orani)


    @api.onchange("tutar")
    def on_change_tutar(self):
        if self.currency_id.name=="TRY":
            self.tutar_try = self.tutar

    @api.model
    def remove_func(self, vals):
        masraf = self.env["harkt.masraf"].search([("masraf_no", "=", vals.get("masraf_no"))])
        self.env.cr.execute("""delete from harkt_masraf_line where masraf_id=%s and satir_no=%s""",(masraf.id, vals.get("satir_no"),))
        return True

    @api.model
    def write_or_create(self, vals):
        try:
            tr_company_id = self.env["tr.company"].search([("code", "=", vals.get("company_id"))]).id
            masraf = self.env["harkt.masraf"].search([("masraf_no", "=", vals.get("masraf_no")),
                                                          ("tr_company_id", "=", tr_company_id)])
            print("test2")
            rec = self.env["harkt.masraf.line"].search(
                [("masraf_id", "=", masraf.id),
                 ("tr_company_id", "=", tr_company_id),
                 ("satir_no", "=", vals.get("satir_no"))
                 ])


            kisi_id = None
            if vals.get("kisi_id"):
                emp = self.env["hr.employee"].sudo().search([("emp_no", "=", vals.get("kisi_id"))])
                if len(emp) > 0 and vals.get("kisi_id"):
                    emp = emp[0]
                    if emp.user_id:
                        kisi_id = emp.user_id.id

            virman_calisan_id = None
            if vals.get("virman_calisan_id"):
                virman_emp = self.env["hr.employee"].sudo().search([("emp_no", "=", vals.get("virman_yapilacak_kisi"))])
                if len(virman_emp) > 0 and vals.get("virman_calisan_id"):
                    virman_emp = virman_emp[0]
                    if virman_emp.user_id:
                        virman_calisan_id = virman_emp.user_id.id

            ongrup_id = None
            ongrup = self.env["harkt.masraf.ongrup"].search([("ongrup_kodu", "=", vals.get("ongrup_no"))])
            if len(ongrup) > 0:
                ongrup_id = ongrup[0].id

            print("test5")
            masraf_turu_id = None
            masraf_turu = self.env["harkt.masraf.turu"].search([("masraf_turu_kodu", "=", vals.get("masraf_turu")),
                                                                ("tr_company_id", "=", tr_company_id)])
            print(masraf_turu)
            if len(masraf_turu) > 0:
                masraf_turu_id = masraf_turu[0].id

            bolge_id = None
            bolge = self.env["harkt.muhasebe.kodu"].search([("code", "=", vals.get("bolge")),
                                                            ('tr_company_id', '=', tr_company_id),
                                                            ('kod_yapisi', '=', 'J')])
            if len(bolge) > 0:
                bolge_id = bolge[0].id

            print("test7")
            gider_yeri_id = None
            gider_yeri = self.env["harkt.muhasebe.kodu"].search([("name", "=", vals.get("gider_yeri")),
                                                                ('tr_company_id', '=', tr_company_id),
                                                                 ("kod_yapisi","=","B")])

            if len(gider_yeri) > 0:
                gider_yeri_id = gider_yeri[0].id

            currency_id = None
            currency = self.env["res.currency"].search([("name", "=", vals.get("currency_code"))])
            if len(currency) > 0:
                currency_id = currency[0].id

            project_id = None
            project = self.env["harkt.proje"].search([("code", "=", vals.get("proje"))])
            if len(project) > 0:
                project_id = project[0].id

            activity_id = None
            activity = self.env["harkt.aktivite"].search([("activity_seq", "=", vals.get("activity_seq"))])
            if len(activity) > 0:
                activity_id = activity[0].id

            para_talep_id = None
            para_talep = self.env["harkt.para.talep"].search([("talep_no", "=", vals.get("ilgili_talep_no"))])
            if len(para_talep) > 0:
                para_talep_id = para_talep[0].id

            bolum_id = None
            bolum = self.env["harkt.muhasebe.kodu"].search([("tr_company_id", "=", tr_company_id),
                                                            ("kod_yapisi", "=", "B"),
                                                            ("name", "=", vals.get("bolum"))])
            if len(bolum) > 0:
                bolum_id = bolum[0].id

            iade_hesap_id = None
            iade_hesap = self.env["harkt.nakit.hesap"].search([("tr_company_id", "=", tr_company_id),
                                                            ("name", "=", vals.get("iade_hesap_id"))])
            if len(iade_hesap) > 0:
                iade_hesap_id = iade_hesap[0].id

            plaka_id = None
            plaka = self.env["harkt.muhasebe.kodu"].search([("code", "=", vals.get("plaka")),
                                                             ('tr_company_id', '=', tr_company_id)])
            if len(plaka) > 0:
                plaka_id = plaka[0].id

            ev_kodu_id = None
            ev_kodu = self.env["harkt.muhasebe.kodu"].search([("code", "=", vals.get("ev_kodu")),
                                                            ('tr_company_id', '=', tr_company_id)])
            if len(ev_kodu) > 0:
                ev_kodu_id = ev_kodu[0].id

            data = {
                "tr_company_id": tr_company_id,
                "masraf_id": masraf.id,
                "satir_no": vals.get("satir_no"),
                "bolge_id": bolge_id,
                "para_talep_id": para_talep_id,
                "fis_tarihi": vals.get("fis_tarihi"),
                "kisi_id": kisi_id,
                "bolum_id": bolum_id,
                "project_id": project_id,
                "activity_id": activity_id,
                "iade_hesap_id": iade_hesap_id,
                "personel_virmani": True if vals.get("personel_virmani")=="TRUE" else False,
                "virman_calisan_id": virman_calisan_id,
                "maas_kesintisi": True if vals.get("maas_kesintisi")=="TRUE" else False,
                "harici_arac_plaka":  vals.get("kiralik_plaka"),
                "ongrup_id": ongrup_id,
                "masraf_turu_id": masraf_turu_id,
                "gider_yeri_id": gider_yeri_id,
                "miktar": vals.get("miktar"),
                "currency_id": currency_id,
                "tutar": vals.get("toplam_tutar"),
                "tutar_try": vals.get("try_toplam_tutar"),
                "tedarikci_belge_no": vals.get("tedarikci"),
                "kdv_orani": vals.get("kdv_orani"),
                "kiralik": True if vals.get("kiralik") == "TRUE" else False,
                "firma_araci_plaka_id": plaka_id,
                "ev_kodu_id": ev_kodu_id,
                "is_emri_no": vals.get("is_emri_no"),
                "odeme_durum": "Ödendi" if vals.get("belgeli") == "TRUE" else "Ödenmedi",
                "aciklama": vals.get("aciklama"),
                "para_talebi_durum": "Para Talebi Oluştur" if vals.get("talep_yok") == "TRUE" else "Para Talebi Var",
                "belge_durum": "Belgeli" if vals.get("belgeli") == "TRUE" else "Belgesiz",
                "belge_sonradan": True if vals.get("belge_sonradan") == "TRUE" else False,
                "avans_iadesi": True if vals.get("avans_iadesi") == "TRUE" else False,
                "supercall": True
            }
            print(data)
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
            #ret = super(HarktMasrafLine, self).unlink()

            c.execute("""
            BEGIN
                ODOO_PORTAL_API.masraf_satir_sil_odoo2_ifs(:MASRAF_NO,:LINE_NO);
            END;
            """,
                      MASRAF_NO=self.masraf_id.masraf_no,
                      LINE_NO=self.satir_no)
            ret = self.env.cr.execute("""delete from harkt_masraf_line where masraf_id=%s and satir_no=%s""",
                                      (self.masraf_id.id, self.satir_no,))
            conn.commit()
        except Exception as ex:
            conn.rollback()
            print(ex)
            raise UserError(self.env["oracle.conn"].simplify_error_message(ex))

        return ret

    def action_para_talep(self):
        action = self.env.ref('harkt_masraf.harkt_para_talebi_action')
        return {
            'name': action.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': action.res_model,
            'res_id': self.para_talep_id.id,
            #'target': 'current',
            'context': {},
        }


