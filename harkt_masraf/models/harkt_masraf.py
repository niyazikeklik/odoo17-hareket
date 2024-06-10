from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktMasraf(models.Model):
    _name = 'harkt.masraf'
    _inherit = ['mail.thread']
    _description = "Hareket Masraf"
    _rec_name = "display_name"
    _order = "masraf_no desc"

    def _get_allowed_company_ids(self):
        if self.env.user.has_group('harkt_masraf.group_masraf_admin'):
            return self.env["tr.company"].search([]).ids
        else:
            if self.env.user.employee_id.tr_company_id:
                return [self.env.user.employee_id.tr_company_id.id]
            else:
                return False

    def _get_default_company_id(self):
        if self.env.user.employee_id.tr_company_id:
            return self.env.user.employee_id.tr_company_id.id
        else:
            return self.env["tr.company"].search([("code","=","01")])

    allowed_company_ids = fields.One2many("tr.company", compute="_compute_allowed_company_ids",
                                          default=_get_allowed_company_ids,
                                          string="izin verilen sirketler")

    masraf_no =fields.Char("Masraf No", copy=False)
    display_name =fields.Char("Ad", compute="_compute_display_name")
    def _compute_display_name(self):
        for rec in self:
            if rec.masraf_no and rec.talep_eden_id:
                rec.display_name = rec.masraf_no + " - "+ rec.talep_eden_id.name
            elif rec.masraf_no:
                rec.display_name = rec.masraf_no
            elif rec.talep_eden_id:
                rec.display_name = rec.talep_eden_id.name
            else:
                rec.display_name = ""
    tr_company_id = fields.Many2one("tr.company", required=True, index=True, string="Grup Şirketi",
                                    domain="[('para_talebi','=',True),('id','in',allowed_company_ids)]",
                                    default=_get_default_company_id)

    talep_eden_id = fields.Many2one("res.users", string="Kişi", default=lambda self: self.env.user.id)
    #bolum = fields.Char("Bölüm", default= lambda self: self.get_bolum(self.tr_company_id.id))
    bolum_id = fields.Many2one("harkt.muhasebe.kodu",
                              domain="[('tr_company_id', '=', tr_company_id),('kod_yapisi','=','B')]")
    notlar = fields.Char("Notlar")
    currency_id = fields.Many2one("res.currency", required=True)
    state = fields.Selection([("TASLAK", "TASLAK"),
                              ("KONTROL_BEKLIYOR", "KONTROL_BEKLIYOR"),
                              ("YAYINLANDI", "YAYINLANDI"),
                              ("ONAY_BEKLIYOR", "ONAY_BEKLIYOR"),
                              ("ONAYLANDI", "ONAYLANDI"),
                              ("IPTAL", "IPTAL")
                              ], default="TASLAK")
    masraf_satir_ids = fields.One2many("harkt.masraf.line", inverse_name="masraf_id",
                                      string="Masraf Satırları")
    can_approve = fields.Boolean("Onaylayabilir", compute="_compute_can_approve")
    next_approver_ids = fields.Many2many("res.users", "harkt_masraf_approvers_rel", string="Onaylayıcılar",
                                         readonly=True)
    supercall = fields.Boolean(string="Supercall")

    toplam_try= fields.Float("Toplam TRY", compute="_compute_total")
    toplam_eur = fields.Float("Toplam EUR", compute="_compute_total")
    toplam_usd = fields.Float("Topla USD", compute="_compute_total")

    def _compute_total(self):
        for rec in self:
            if rec.currency_id.name == "TRY":
                rec.toplam_eur = 0
                rec.toplam_usd = 0
                temp_tutar = 0
                for line in rec.masraf_satir_ids:
                    temp_tutar = temp_tutar +line.tutar
                rec.toplam_try = temp_tutar
            elif rec.currency_id.name == "USD":
                rec.toplam_eur = 0
                temp_tutar = 0
                temp_tutar_try = 0
                for line in rec.masraf_satir_ids:
                    temp_tutar = temp_tutar +line.tutar
                    temp_tutar_try = temp_tutar_try + line.tutar_try
                rec.toplam_usd = temp_tutar
                rec.toplam_try = temp_tutar_try
            elif rec.currency_id.name == "EUR":
                rec.toplam_usd = 0
                temp_tutar = 0
                temp_tutar_try = 0
                for line in rec.masraf_satir_ids:
                    temp_tutar = temp_tutar +line.tutar
                    temp_tutar_try = temp_tutar_try + line.tutar_try
                rec.toplam_eur = temp_tutar
                rec.toplam_try = temp_tutar_try
            else:
                rec.toplam_usd =0
                rec.toplam_eur = 0
                rec.toplam_try = 0


    def _compute_allowed_company_ids(self):
        for rec in self:
            if self.env.user.has_group('harkt_masraf.group_masraf_admin'):
                rec.allowed_company_ids = self.env["tr.company"].search([]).ids
            else:
                if self.env.user.employee_id.tr_company_id:
                    rec.allowed_company_ids = [self.env.user.employee_id.tr_company_id.id]
                else:
                    rec.allowed_company_ids = False

    def _compute_can_approve(self):
        for rec in self:
            approve = False
            for approver in rec.next_approver_ids:
                if self.env.user.id == approver.id:
                    approve = True
            self.can_approve = approve

    @api.onchange("tr_company_id")
    def _onchange_tr_company_id(self):
        if self.tr_company_id:
            self.bolum_id = self.env["harkt.masraf"].get_bolum(self.tr_company_id.id,
                                                               self.talep_eden_id.employee_id.emp_no)

    def action_yayinla(self):
        if not self.env.user.has_group("'harkt_masraf.group_masraf_admin'"):
            raise UserError("Sadece Masraf Admini bu işlemi yapabilir")
        for rec in self:
            if rec.state == "KONTROL_BEKLIYOR":
                rec.state = "YAYINLANDI"

    def action_kontrol(self):
        for rec in self:
            if rec.state == "TASLAK":
                rec.state = "KONTROL_BEKLIYOR"
    def action_iptal(self):
        for rec in self:
            rec.state = "IPTAL"
            for line in rec.masraf_satir_ids:
                if line.para_talep_id:
                    line.para_talep_id.write({
                        "state": "IPTAL",
                        "supercall": True
                    })



    def get_bolum(self, tr_company_id, emp_no):
        """"""
        conn = self.env["oracle.conn"].connect(False, False)
        bolum = "*"

        tr_company=self.env["tr.company"].browse(tr_company_id)

        try:
            c = conn.cursor()
            c.execute("""select nvl(ifsapp.ODOO_PORTAL_API.Get_Emp_Bolum_For_Talep(:COMPANY, :EMP_NO),'*') from dual""",
                      COMPANY = tr_company.code,
                      EMP_NO=emp_no)
            result = c.fetchall()
            bolum = result[0][0]
            if self.env.user.oracle_username == "IFSAPP":
                bolum = "BILGI TEKNOLOJILERI"
            sonuc = self.env["harkt.muhasebe.kodu"].search([("tr_company_id","=",tr_company_id), ("kod_yapisi","=","B"), ("name","=", bolum)])
            if len(sonuc)>0:
                return sonuc[0].id
        except Exception as ex:
            print(ex)
        return False

    @api.model
    def create(self, vals):
        if "supercall" in vals:
            return super(HarktMasraf, self).create(vals)
        else:
            print(self.env.user.employee_id.tr_company_id.id)
            print(vals.get("tr_company_id"))
            if (self.env.user.employee_id and "tr_company_id" in vals
                    and vals.get("tr_company_id")
                    and not self.env.user.has_group("'harkt_masraf.group_masraf_admin'")
                    and vals.get("talep_eden_id") !=2):
                if vals.get("tr_company_id") != self.env.user.employee_id.tr_company_id.id:
                    raise UserError("Sadece çalıştığınız şirkete masraf girebilirsiniz")
                
            conn = self.env["oracle.conn"].connect(1, False)
            ret = {}
            try:
                c = conn.cursor()
                ret = super(HarktMasraf, self).create(vals)
                self.set_followers()
                masraf = self.env["harkt.masraf"].sudo().search([("id", "=", ret.id)])
                masraf_no = c.var(str)
                emp = self.env["hr.employee"].sudo().search([("user_id","=",masraf.talep_eden_id.id)])
                if len(emp) == 0:
                    raise UserError("Talep eden çalışan bulunamadı")
                lines = ""
                satir_no = 1
                for rec in masraf.masraf_satir_ids:
                    rec.satir_no = satir_no
                    satir_no = satir_no + 1
                    line_emp = False
                    if rec.kisi_id:
                        line_emp = self.env["hr.employee"].sudo().search(
                            [("user_id", "=", rec.kisi_id.id)])
                        if len(line_emp) > 0:
                            line_emp = line_emp[0]

                    lines = lines + """
                    <MasrafSatir>
                        <SATIR_NO>"""+str(rec.satir_no) + """</SATIR_NO>
                        <COMPANY_ID>"""+(masraf.tr_company_id.code or "")+ """</COMPANY_ID>
                        <BOLGE_ID>"""+(rec.bolge_id.code or "")+ """</BOLGE_ID>
                        <PARA_TALEP_ID>"""+(rec.para_talep_id.talep_no or "")+ """</PARA_TALEP_ID>
                        <FIS_TARIHI>""" + (rec.fis_tarihi.strftime("%Y-%m-%d") or "") + """</FIS_TARIHI>
                        <KISI_ID>"""+(("P"+line_emp.person_id) if line_emp else "")+ """</KISI_ID>
                        <BOLUM_ID>"""+(rec.bolum_id.name or "")+ """</BOLUM_ID>
                        <PROJECT_ID>"""+(rec.project_id.code or "")+ """</PROJECT_ID>
                        <ACTIVITY_ID>"""+(str(rec.activity_id.activity_seq) or "")+ """</ACTIVITY_ID>
                        <IADE_HESAP_ID>"""+(rec.iade_hesap_id.name or "")+ """</IADE_HESAP_ID>
                        <PERSONEL_VIRMANI>"""+("TRUE" if rec.personel_virmani else "FALSE")+ """</PERSONEL_VIRMANI>
                        <VIRMAN_CALISAN_ID>"""+(("P"+rec.virman_calisan_id.emp_no) if (rec.virman_calisan_id and rec.virman_calisan_id.emp_no) else "")+ """</VIRMAN_CALISAN_ID>
                        <MAAS_KESINTISI>"""+("TRUE" if rec.maas_kesintisi else "FALSE")+ """</MAAS_KESINTISI>
                        <HARICI_ARAC_PLAKA>"""+(rec.harici_arac_plaka or "")+ """</HARICI_ARAC_PLAKA>
                        <ONGRUP_ID>"""+(rec.ongrup_id.ongrup_kodu or "")+ """</ONGRUP_ID>
                        <MASRAF_TURU_ID>"""+(rec.masraf_turu_id.masraf_turu_kodu or "")+ """</MASRAF_TURU_ID>
                        <GIDER_YERI_ID>"""+(rec.gider_yeri_id.code or "")+ """</GIDER_YERI_ID>
                        <MIKTAR>"""+(str(rec.miktar) or "1")+ """</MIKTAR>
                        <CURRENCY_ID>"""+(rec.currency_id.name or "")+ """</CURRENCY_ID>
                        <TUTAR>"""+(str(rec.tutar) or "0")+ """</TUTAR>
                        <TUTAR_TRY>"""+(str(rec.tutar_try) or "0")+ """</TUTAR_TRY>
                        <TUTAR_KDV_HARIC>"""+(str(rec.tutar_kdv_haric) or "0")+ """</TUTAR_KDV_HARIC>
                        <TUTAR_TRY_KDV_HARIC>"""+(str(rec.tutar_try_kdv_haric) or "0")+ """</TUTAR_TRY_KDV_HARIC>
                        <TEDARIKCI_BELGE_NO>"""+(rec.tedarikci_belge_no or "")+ """</TEDARIKCI_BELGE_NO>
                        <KDV_ORANI>"""+(str(rec.kdv_orani) or "0")+ """</KDV_ORANI>
                        <KIRALIK>"""+(rec.kiralik  or "")+ """</KIRALIK>
                        <FIRMA_ARACI_PLAKA_ID>"""+(rec.firma_araci_plaka_id.code  or "")+ """</FIRMA_ARACI_PLAKA_ID>
                        <EV_KODU_ID>"""+(rec.ev_kodu_id.code  or "")+ """</EV_KODU_ID>
                        <IS_EMRI_NO>"""+(rec.is_emri_no or "")+ """</IS_EMRI_NO>
                        <ODENDI>"""+("TRUE" if rec.odeme_durum =="Ödendi" else "FALSE")+ """</ODENDI>
                        <ODENMEDI>"""+("TRUE" if rec.odeme_durum =="Ödenmedi" else "FALSE")+ """</ODENMEDI>
                        <ACIKLAMA>"""+(rec.aciklama or "")+ """</ACIKLAMA>
                        <PARA_TALEBI_OLUSTUR>"""+("TRUE" if rec.para_talebi_durum == "Para Talebi Oluştur" else "FALSE")+ """</PARA_TALEBI_OLUSTUR>
                        <PARA_TALEBI_VAR>"""+("TRUE" if rec.para_talebi_durum == "Para Talebi Var" else "FALSE")+ """</PARA_TALEBI_VAR>
                        <BELGELI>"""+("TRUE" if rec.belge_durum == "Belgeli" else "FALSE")+ """</BELGELI>
                        <BELGESIZ>"""+("TRUE" if rec.belge_durum == "Belgesiz" else "FALSE")+ """</BELGESIZ>
                        <BELGE_SONRADAN>"""+("TRUE" if rec.belge_sonradan else "FALSE")+ """</BELGE_SONRADAN>
                        <AVANS_IADESI>"""+("TRUE" if rec.avans_iadesi else "FALSE")+ """</AVANS_IADESI>
                    </MasrafSatir>
                    """
                details = """<?xml version="1.0" encoding="utf-16"?>
                                    <Masraf xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                                        <MasrafSatirlar>
                                            """ + lines + """
                                        </MasrafSatirlar>
                                    </Masraf>"""
                c.execute(
                    """
                    BEGIN
                        IFSAPP.odoo_portal_api.masraf_odoo2_ifs(
                              :COMPANY_ID,
                              :USER_ID,
                              :BOLUM,
                              :NOTLAR,
                              :CURRENCY,
                              :DURUM,
                              :DETAILS,
                              :MASRAF_NO);
                    END;""",
                    COMPANY_ID = masraf.tr_company_id.code,
                    USER_ID = ('P'+emp[0].emp_no) if len(emp) > 0 and emp.emp_no else "*",
                    BOLUM = masraf.bolum_id.name or None,
                    NOTLAR = masraf.notlar or None,
                    CURRENCY = masraf.currency_id.name or None,
                    DURUM = vals.get("STATE") or None,
                    DETAILS = details or None,
                    MASRAF_NO = masraf_no
                )
                masraf.masraf_no = masraf_no.getvalue()

                conn.commit()
            except Exception as ex:
                conn.rollback()
                print(ex)
                raise UserError(self.env["oracle.conn"].simplify_error_message(ex))
            return ret

    @api.model
    def write(self, vals):
        if "supercall" in vals:
            return super(HarktMasraf, self).write(vals)
        else:
            conn = self.env["oracle.conn"].connect(False, False)
            ret = {}
            try:
                c = conn.cursor()
                ret = super(HarktMasraf, self).write(vals)
                self.set_followers()
                masraf = self.env["harkt.masraf"].sudo().search([("id", "=", self.id)])
                emp = self.env["hr.employee"].sudo().search([("user_id", "=", masraf.talep_eden_id.id)])
                if len(emp) == 0:
                    raise UserError("Talep eden çalışan bulunamadı")
                lines = ""
                satir_no = 1
                for rec in masraf.masraf_satir_ids:
                    if not rec.satir_no:
                        rec.satir_no = satir_no
                        satir_no = satir_no + 1
                    else:
                        satir_no = rec.satir_no +1
                    line_emp = False
                    if rec.kisi_id:
                        line_emp = self.env["hr.employee"].sudo().search(
                            [("user_id", "=", rec.kisi_id.id)])
                        if len(line_emp) > 0:
                            line_emp = line_emp[0]

                    lines = lines + """
                        <MasrafSatir>
                            <SATIR_NO>"""+str(rec.satir_no) + """</SATIR_NO>
                            <COMPANY_ID>"""+(masraf.tr_company_id.code or "")+ """</COMPANY_ID>
                            <BOLGE_ID>"""+(rec.bolge_id.code or "")+ """</BOLGE_ID>
                            <PARA_TALEP_ID>"""+(rec.para_talep_id.talep_no or "")+ """</PARA_TALEP_ID>
                            <FIS_TARIHI>""" + (rec.fis_tarihi.strftime("%Y-%m-%d") or "") + """</FIS_TARIHI>
                            <KISI_ID>"""+(("P"+line_emp.person_id) if line_emp else "")+ """</KISI_ID>
                            <BOLUM_ID>"""+(rec.bolum_id.name or "")+ """</BOLUM_ID>
                            <PROJECT_ID>"""+(rec.project_id.code or "")+ """</PROJECT_ID>
                            <ACTIVITY_ID>"""+(str(rec.activity_id.activity_seq) or "")+ """</ACTIVITY_ID>
                            <IADE_HESAP_ID>"""+(rec.iade_hesap_id.name or "")+ """</IADE_HESAP_ID>
                            <PERSONEL_VIRMANI>"""+("TRUE" if rec.personel_virmani else "FALSE")+ """</PERSONEL_VIRMANI>
                            <VIRMAN_CALISAN_ID>"""+(("P"+rec.virman_calisan_id.emp_no) if (rec.virman_calisan_id and rec.virman_calisan_id.emp_no) else "")+ """</VIRMAN_CALISAN_ID>
                            <MAAS_KESINTISI>"""+("TRUE" if rec.maas_kesintisi else "FALSE")+ """</MAAS_KESINTISI>
                            <HARICI_ARAC_PLAKA>"""+(rec.harici_arac_plaka or "")+ """</HARICI_ARAC_PLAKA>
                            <ONGRUP_ID>"""+(rec.ongrup_id.ongrup_kodu or "")+ """</ONGRUP_ID>
                            <MASRAF_TURU_ID>"""+(rec.masraf_turu_id.masraf_turu_kodu or "")+ """</MASRAF_TURU_ID>
                            <GIDER_YERI_ID>"""+(rec.gider_yeri_id.name or "")+ """</GIDER_YERI_ID>
                            <MIKTAR>"""+(str(rec.miktar) or "1")+ """</MIKTAR>
                            <CURRENCY_ID>"""+(rec.currency_id.name or "")+ """</CURRENCY_ID>
                            <TUTAR>"""+(str(rec.tutar) or "0")+ """</TUTAR>
                            <TUTAR_TRY>"""+(str(rec.tutar_try) or "0")+ """</TUTAR_TRY>
                            <TUTAR_KDV_HARIC>"""+(str(rec.tutar_kdv_haric) or "0")+ """</TUTAR_KDV_HARIC>
                            <TUTAR_TRY_KDV_HARIC>"""+(str(rec.tutar_try_kdv_haric) or "0")+ """</TUTAR_TRY_KDV_HARIC>
                            <TEDARIKCI_BELGE_NO>"""+(rec.tedarikci_belge_no or "")+ """</TEDARIKCI_BELGE_NO>
                            <KDV_ORANI>"""+(str(rec.kdv_orani) or "0")+ """</KDV_ORANI>
                            <KIRALIK>"""+(rec.kiralik  or "")+ """</KIRALIK>
                            <FIRMA_ARACI_PLAKA_ID>"""+(rec.firma_araci_plaka_id.code  or "")+ """</FIRMA_ARACI_PLAKA_ID>
                            <EV_KODU_ID>"""+(rec.ev_kodu_id.code  or "")+ """</EV_KODU_ID>
                            <IS_EMRI_NO>"""+(rec.is_emri_no or "")+ """</IS_EMRI_NO>
                            <ODENDI>"""+("TRUE" if rec.odeme_durum =="Ödendi" else "FALSE")+ """</ODENDI>
                            <ODENMEDI>"""+("TRUE" if rec.odeme_durum =="Ödenmedi" else "FALSE")+ """</ODENMEDI>
                            <ACIKLAMA>"""+(rec.aciklama or "")+ """</ACIKLAMA>
                            <PARA_TALEBI_OLUSTUR>"""+("TRUE" if rec.para_talebi_durum == "Para Talebi Oluştur" else "FALSE")+ """</PARA_TALEBI_OLUSTUR>
                            <PARA_TALEBI_VAR>"""+("TRUE" if rec.para_talebi_durum == "Para Talebi Var" else "FALSE")+ """</PARA_TALEBI_VAR>
                            <BELGELI>"""+("TRUE" if rec.belge_durum == "Belgeli" else "FALSE")+ """</BELGELI>
                            <BELGESIZ>"""+("TRUE" if rec.belge_durum == "Belgesiz" else "FALSE")+ """</BELGESIZ>
                            <BELGE_SONRADAN>"""+("TRUE" if rec.belge_sonradan else "FALSE")+ """</BELGE_SONRADAN>
                            <AVANS_IADESI>"""+("TRUE" if rec.avans_iadesi else "FALSE")+ """</AVANS_IADESI>
                        </MasrafSatir>
                        """
                details = """<?xml version="1.0" encoding="utf-16"?>
                                        <Masraf xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                                            <MasrafSatirlar>
                                                """ + lines + """
                                            </MasrafSatirlar>
                                        </Masraf>"""
                c.execute(
                    """
                    BEGIN
                        IFSAPP.odoo_portal_api.masraf_odoo2_ifs(
                              :COMPANY_ID,
                              :USER_ID,
                              :BOLUM,
                              :NOTLAR,
                              :CURRENCY,
                              :DURUM,
                              :DETAILS,
                              :MASRAF_NO);
                    END;""",
                    COMPANY_ID=masraf.tr_company_id.code,
                    USER_ID=('P' + emp[0].emp_no) if len(emp) > 0 else "*",
                    BOLUM=masraf.bolum_id.name or None,
                    NOTLAR=masraf.notlar or None,
                    CURRENCY=masraf.currency_id.name or None,
                    DURUM=("" if "state" not in vals else masraf.state),
                    DETAILS=details or None,
                    MASRAF_NO=masraf.masraf_no
                )
                conn.commit()
            except Exception as ex:
                conn.rollback()
                print(ex)
                raise UserError(self.env["oracle.conn"].simplify_error_message(ex))
            return ret


    @api.model
    def remove_func(self, vals):
        self.env.cr.execute("""delete from harkt_masraf where masraf_no=%s""", (vals.get("masraf_no"),))
        return True

    @api.model
    def write_or_create(self, vals):
        print(vals)
        try:
            tr_company_id = self.env["tr.company"].search([("code", "=", vals.get("company"))]).id
            rec = self.env["harkt.masraf"].search(
                [("masraf_no", "=", vals.get("masraf_no")),
                 ("tr_company_id", "=", tr_company_id)
                 ])
            print("kişi:")
            print(vals.get("kisi_id"))
            if vals.get("kisi_id"):
                print("emp:")
                emp = self.env["hr.employee"].sudo().search([("emp_no", "=", vals.get("kisi_id"))])
                print(emp)
                talep_eden_id = None
                if len(emp) > 0:
                    emp = emp[0]
                    if emp.user_id:
                        talep_eden_id = emp.user_id.id
            bolum_id = None
            bolum = self.env["harkt.muhasebe.kodu"].search([("tr_company_id", "=", tr_company_id),
                                                            ("kod_yapisi", "=", "B"),
                                                            ("name", "=", vals.get("bolum"))])
            if len(bolum) > 0:
                bolum_id = bolum[0].id
            currency_id = None
            currency = self.env["res.currency"].search([("name", "=", vals.get("currency_code"))])
            if len(currency) > 0:
                currency_id = currency[0].id

            result = False
            data = {
                "tr_company_id": tr_company_id,
                "masraf_no": vals.get("masraf_no"),
                "talep_eden_id": talep_eden_id,
                "bolum_id": bolum_id,
                "notlar": vals.get("notlar"),
                "currency_id": currency_id,
                "state": vals.get("durum"),
                "supercall": True
            }
            if len(rec) == 0:
                ret = self.create(data)
                self.set_followers()
                result = True
            else:
                ret = rec.write(data)
                rec.set_followers()
                result = True
            
        except Exception as ex:
            result = ex
        return result

    def unlink(self):
        conn = self.env["oracle.conn"].connect(1, False)
        ret = {}
        try:
            c = conn.cursor()
            #ret = super(HarktMasraf, self).unlink()
            c.execute("""
                        BEGIN
                            ODOO_PORTAL_API.masraf_sil_odoo2_ifs(:MASRAF_NO);
                        END;
                        """,
                      MASRAF_NO = self.masraf_no,
            )
            self.env.cr.execute("""delete from harkt_masraf where id=%s""", (self.id,))
            conn.commit()
        except Exception as ex:
            conn.rollback()
            print(ex)
            raise UserError(self.env["oracle.conn"].simplify_error_message(ex))
        return ret

    def set_followers(self):
        partner_ids = []
        #talep eden kişiyi takipçi olarak ekliyoruz
        partner_ids.append(self.talep_eden_id.partner_id.id)
        #satirdaki ilgilileri takipçi olarak ekliyoruz
        for satir in self.masraf_satir_ids:
            partner_ids.append(satir.kisi_id.partner_id.id)
        #talep edenin 1. amirini takipçi olarak ekliyoruz
        partner_ids.append(self.talep_eden_id.employee_id.parent_id.user_id.partner_id.id)
        # talep edenin 2. amirini takipçi olarak ekliyoruz
        partner_ids.append(self.talep_eden_id.employee_id.parent_id.parent_id.user_id.partner_id.id)
        #satırdaki kişilerin 1. amirini takipçi olarak ekliyoruz
        for satir in self.masraf_satir_ids:
            if satir.kisi_id:
                partner_ids.append(satir.kisi_id.employee_id.parent_id.user_id.partner_id.id)
        # satırdaki kişilerin 2. amirini takipçi olarak ekliyoruz
        for satir in self.masraf_satir_ids:
            if satir.kisi_id:
                partner_ids.append(satir.kisi_id.employee_id.parent_id.parent_id.user_id.partner_id.id)
        partner_ids = list(dict.fromkeys(partner_ids))
        partner_ids = [i for i in partner_ids if i]
        for partner_id in partner_ids:
            if partner_id and not self.env['mail.followers'].search([('res_id', '=', self.id),('res_model', '=', "harkt.masraf"),('partner_id', '=', partner_id)]):
                self.env['mail.followers'].sudo().create({
                    "res_id": self.id,
                    "res_model": "harkt.masraf",
                    "partner_id": partner_id
                })

