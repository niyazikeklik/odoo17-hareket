from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktParaTalep(models.Model):
    _name = 'harkt.para.talep'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Hareket Para Talep"
    _rec_name= "talep_no"
    _order = "talep_no desc"

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

    talep_no = fields.Char("Talep no", index=True, copy=False)
    talep_tarihi = fields.Date("Talep Tarihi", required=True)

    tr_company_id = fields.Many2one("tr.company", required=True, index=True, string="Grup Şirketi",
                                    domain="[('para_talebi','=',True),('id','in',allowed_company_ids)]",
                                    default=_get_default_company_id)



    def _compute_allowed_company_ids(self):
        for rec in self:
            if self.env.user.has_group('harkt_masraf.group_masraf_admin'):
                rec.allowed_company_ids = self.env["tr.company"].search([]).ids
            else:
                if self.env.user.employee_id.tr_company_id:
                    rec.allowed_company_ids = [self.env.user.employee_id.tr_company_id.id]
                else:
                    rec.allowed_company_ids = False



    talep_eden_id = fields.Many2one("res.users", string="Kişi", default=lambda self: self.env.user.id)
    #bolum = fields.Char("Bölüm", default=lambda self: self.env["harkt.masraf"].get_bolum() )
    bolum_id =fields.Many2one("harkt.muhasebe.kodu", domain="[('tr_company_id', '=', tr_company_id),('kod_yapisi','=','B')]")
    notlar = fields.Char("Notlar")
    currency_id =fields.Many2one("res.currency", required=True, string="Para Bilimi")
    project_id = fields.Many2one("harkt.proje","Proje", domain="[('tr_company_id', '=', tr_company_id)]", index=True)
    proje_turu = fields.Selection([("Etut","Etut"),
                                   ("Talimat","Talimat")
                                   ],string="Proje Türü")

    ref_talep = fields.Many2one("harkt.para.talep","Ref Talep", readonly=True)

    state = fields.Selection([("TASLAK", "TASLAK"),
                              ("KONTROL_BEKLIYOR", "KONTROL_BEKLIYOR"),
                              ("YAYINLANDI", "YAYINLANDI"),
                              ("ONAYLANDI", "ONAYLANDI"),
                              ("ODENECEK", "ODENECEK"),
                              ("ODENDI", "ODENDI"),
                              ("IPTAL", "IPTAL")
                              ], default="TASLAK")
    onay_ids = fields.One2many("harkt.para.talep.onay", "para_talep_id", "Onaylar")
    talep_satir_ids = fields.One2many("harkt.para.talep.line", inverse_name="para_talep_id", string= "Para Talep Satırları")
    sequence_no = fields.Integer("Sıra No")
    route = fields.Integer("Onay No")
    can_approve = fields.Boolean("Onaylayabilir", compute="_compute_can_approve")
    next_approver_ids = fields.Many2many("res.users","harkt_para_talep_approvers_rel", string="Onaylayıcılar", readonly=True)
    next_approver_id = fields.Many2one("res.users", string="Onaylayıcı", readonly=True)
    reject_reason = fields.Char("Red Sebebi")
    supercall = fields.Boolean(string="Supercall")
    bolum_id_can_change = fields.Boolean("Bölüm ID Değiştirebilir", compute="_compute_bolum_id_can_change", default=lambda self: self.env.user.has_group('harkt_masraf.group_masraf_admin'))
    toplam_try = fields.Float("Toplam TRY", compute="_compute_total")
    toplam_eur = fields.Float("Toplam EUR", compute="_compute_total")
    toplam_usd = fields.Float("Topla USD", compute="_compute_total")

    def _compute_total(self):
        for rec in self:
            if rec.currency_id.name == "TRY":
                rec.toplam_eur = 0
                rec.toplam_usd = 0
                temp_tutar = 0
                for line in rec.talep_satir_ids:
                    temp_tutar = temp_tutar + line.tutar*line.miktar
                rec.toplam_try = temp_tutar
            elif rec.currency_id.name == "USD":
                rec.toplam_eur = 0
                temp_tutar = 0
                temp_tutar_try = 0
                for line in rec.talep_satir_ids:
                    temp_tutar = temp_tutar + line.tutar*line.miktar
                    temp_tutar_try = temp_tutar_try + line.tutar * line.miktar*line.currency_rate
                rec.toplam_usd = temp_tutar
                rec.toplam_try = temp_tutar_try
            elif rec.currency_id.name == "EUR":
                rec.toplam_usd = 0
                temp_tutar = 0
                temp_tutar_try = 0
                for line in rec.talep_satir_ids:
                    temp_tutar = temp_tutar + line.tutar*line.miktar
                    temp_tutar_try = temp_tutar_try + line.tutar * line.miktar*line.currency_rate
                rec.toplam_eur = temp_tutar
                rec.toplam_try = temp_tutar_try
            else:
                rec.toplam_eur = 0
                rec.toplam_usd = 0
                rec.toplam_try = 0

    def _compute_bolum_id_can_change(self):
        for rec in self:
            if self.env.user.has_group('harkt_masraf.group_masraf_admin') and rec.state == "TASLAK":
                rec.bolum_id_can_change = True
            else:
                rec.bolum_id_can_change = False

    @api.onchange("tr_company_id", "talep_eden_id")
    def _onchange_tr_company_id(self):
        if self.tr_company_id and self.talep_eden_id:
            self.bolum_id = self.env["harkt.masraf"].get_bolum(self.tr_company_id.id, self.talep_eden_id.employee_id.emp_no)

    def _compute_can_approve(self):
        for rec in self:
            approve = False
            for approver in rec.next_approver_ids:
                if self.env.user.id == approver.id:
                    approve = True
            self.can_approve = approve

    def action_yayinla(self):
        for rec in self:
            if rec.state == "KONTROL_BEKLIYOR":
                rec.state = "YAYINLANDI"
                rec.write({
                    "supercall": True,
                    "next_approver_ids": [],
                    "next_approver_id": False
                })
    def action_iptal(self):
        for rec in self:
            rec.state = "IPTAL"
            rec.write({
                "supercall": True,
                "next_approver_ids": [],
                "next_approver_id": False
            })

    def action_onayla(self):
        for rec in self:
            if rec.can_approve:
                conn = self.env["oracle.conn"].connect(False, False)
                try:
                    c = conn.cursor()
                    c.execute("""
                    BEGIN
                        ifsapp.odoo_portal_api.para_talebi_onay_odoo2_ifs(:TALEP_NO, :SEQUENCE_NO, :ROUTE, 'APP');
                    END;""",
                              TALEP_NO = rec.talep_no,
                              SEQUENCE_NO= rec.sequence_no,
                              ROUTE = rec.route)
                    conn.commit()
                    res_action = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Başarılı',
                            'message': "Başarıyla Onaylandı",
                            'sticky': False,  # True/False will display for few seconds if false
                            'next': {'type': 'ir.actions.client','tag': 'reload',},
                        }
                    }
                    return res_action
                except Exception as e:
                    print(e)
                    raise UserError(self.env["oracle.conn"].simplify_error_message(e))

    def action_kontrol(self):
        for rec in self:
            if rec.state == "TASLAK":
                rec.state = "KONTROL_BEKLIYOR"
                rec.write({
                    "supercall": True,
                    "next_approver_ids": [],
                    "next_approver_id": False
                })

    @api.model
    def create(self, vals):
        if "supercall" in vals:
            return super(HarktParaTalep, self).create(vals)
        else:
            print(self.env.user.employee_id.tr_company_id.id)
            print(vals.get("tr_company_id"))
            if self.env.user.employee_id and "tr_company_id" in vals and vals.get(
                    "tr_company_id") and not self.env.user.has_group("'harkt_masraf.group_masraf_admin'"):
                if vals.get("tr_company_id") != self.env.user.employee_id.tr_company_id.id and self.env.user.id !=2:
                    raise UserError("Sadece çalıştığınız şirkete para talebi girebilirsiniz")

            conn = self.env["oracle.conn"].connect(1, False)
            ret = {}
            try:
                c = conn.cursor()
                ret = super(HarktParaTalep, self).create(vals)
                self.set_followers()
                para_talep = self.env["harkt.para.talep"].sudo().search([("id", "=", ret.id)])
                para_talep_no = c.var(str)

                if para_talep.ref_talep:
                    ref_talep = para_talep.ref_talep.talep_no
                else:
                    ref_talep = None
                print(ref_talep)

                lines =""
                satir_no = 1
                for rec in para_talep.talep_satir_ids:
                    rec.satir_no = satir_no
                    satir_no = satir_no + 1
                    emp = False
                    if rec.talep_edilen_id:
                        emp = self.env["hr.employee"].sudo().search(
                            [("user_id", "=", rec.talep_edilen_id.id)])
                        if len(emp) > 0:
                            emp = emp[0]

                    lines = lines + """
                    <ParaTalebiSatir>
                        <SATIR_NO>"""+str(rec.satir_no) + """</SATIR_NO>
                        <ONGRUP_NO>"""+(rec.ongrup_id.ongrup_kodu or "")+ """</ONGRUP_NO>
                        <MASRAF_TURU>"""+(rec.masraf_turu_id.masraf_turu_kodu or "")+ """</MASRAF_TURU>
                        <COMPANY_ID>"""+(para_talep.tr_company_id.code or "")+ """</COMPANY_ID>
                        <PROJECT_ID>"""+(para_talep.project_id.code or "")+ """</PROJECT_ID>
                        <BOLGE_ID>"""+(rec.bolge_id.code or "")+ """</BOLGE_ID>
                        <HARICI>"""+("TRUE" if rec.harici else "FALSE")+ """</HARICI>
                        <TALEP_EDILEN_ID>"""+(("P"+emp.person_id) if emp else "")+ """</TALEP_EDILEN_ID>
                        <VARLIK_ID>"""+(rec.varlik_id.code  or "")+ """</VARLIK_ID>
                        <BOLUM>"""+(para_talep.bolum_id.name  or "")+ """</BOLUM>
                        <MIKTAR>"""+(str(rec.miktar) or "")+ """</MIKTAR>
                        <TUTAR>"""+(str(rec.tutar) or "")+ """</TUTAR>
                        <DOVIZ_KURU>"""+(str(rec.currency_rate) or "1")+ """</DOVIZ_KURU>
                        <ULKE>"""+(rec.country_id.code or "")+ """</ULKE>
                        <KIRALIK>"""+("TRUE" if rec.kiralik else "FALSE")+ """</KIRALIK>
                        <KIRALIK_PLAKA>"""+(rec.kiralik_plaka or "")+ """</KIRALIK_PLAKA>
                        <ACIKLAMA>"""+(rec.aciklama or "")+ """</ACIKLAMA>
                        <HARICI_KIMLIK_NO>"""+(rec.harici_kimlik_no or "")+ """</HARICI_KIMLIK_NO>
                        <HARICI_ADRES>"""+(rec.harici_adres or "")+ """</HARICI_ADRES>
                        <HARICI_TELEFON>"""+(rec.harici_telefon or "")+ """</HARICI_TELEFON>
                        <HARICI_IBAN>"""+(rec.harici_iban or "")+ """</HARICI_IBAN>
                        <HARICI_AD_SOYAD>"""+(rec.harici_ad_soyad or "")+ """</HARICI_AD_SOYAD>
                        <IS_TAKIP_NO>"""+(rec.is_takip_no or "")+ """</IS_TAKIP_NO>
                    </ParaTalebiSatir>
                    """
                emp = self.env["hr.employee"].sudo().search([("user_id", "=", para_talep.talep_eden_id.id)])
                if len(emp) == 0:
                    raise UserError("Talep eden çalışan bulunamadı")
                print("EMP INFO")
                print(emp[0].emp_no)
                print(emp.name)
                details = """<?xml version="1.0" encoding="utf-16"?>
                    <ParaTalebi xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                        <COMPANY_ID>""" + (para_talep.tr_company_id.code or "") + """</COMPANY_ID>
                        <USER_ID>""" + ((emp[0].emp_no+"-"+emp.name) if (emp and emp.emp_no and emp.name) else "") + """</USER_ID>
                        <TALEP_TARIHI>""" + (para_talep.talep_tarihi.strftime("%Y-%M-%d") or "") + """</TALEP_TARIHI>
                        <BOLUM>""" + (para_talep.bolum_id.name or "")+ """</BOLUM>
                        <NOTLAR>""" + (para_talep.notlar or "")+ """</NOTLAR>
                        <PARA_BIRIMI>""" + (para_talep.currency_id.name or "")+ """</PARA_BIRIMI>
                        <PROJE>""" + (para_talep.project_id.code or "")+ """</PROJE>
                        <PROJE_TURU>""" + (para_talep.proje_turu or "")+ """</PROJE_TURU>
                        <DURUM>""" + (para_talep.state or "TASLAK")+ """</DURUM>
                        <REF_TALEP>""" + (ref_talep or "")+ """</REF_TALEP>
                        <ParaTalebiSatirlar>
                            """ + lines + """
                        </ParaTalebiSatirlar>
                    </ParaTalebi>"""
                c.execute(
                    """
                    BEGIN
                        IFSAPP.odoo_portal_api.para_talebi_odoo2_ifs(
                              :COMPANY_ID,
                              :USER_ID,
                              :TALEP_TARIHI,
                              :BOLUM,
                              :NOTLAR,
                              :PARA_BIRIMI,
                              :PROJE,
                              :PROJE_TURU,
                              :DURUM,
                              :REF_TALEP,
                              :DETAILS,
                              :SONUC);
                    END;""",
                    COMPANY_ID   = para_talep.tr_company_id.code or None,
                    USER_ID      = (emp[0].emp_no+"-"+emp.name) if (emp.emp_no and emp.name) else None,
                    TALEP_TARIHI = para_talep.talep_tarihi or None,
                    BOLUM        = para_talep.bolum_id.name or None,
                    NOTLAR       = para_talep.notlar or None,
                    PARA_BIRIMI  = para_talep.currency_id.name or None,
                    PROJE        = para_talep.project_id.code or None,
                    PROJE_TURU   = para_talep.proje_turu or None,
                    DURUM        = ("" if "state" not in vals else para_talep.state),
                    REF_TALEP    = ref_talep or None,
                    DETAILS      = details,
                    SONUC        = para_talep_no
                )
                print(para_talep_no)
                para_talep.write({
                    "talep_no": para_talep_no.getvalue(),
                    "supercall": True
                })
                conn.commit()
            except Exception as ex:
                conn.rollback()
                print(ex)
                raise UserError(self.env["oracle.conn"].simplify_error_message(ex))
            return ret

    @api.model
    def write(self, vals):
        if "supercall" in vals:
            return super(HarktParaTalep, self).write(vals)
        else:
            conn = self.env["oracle.conn"].connect(1, False)
            ret = {}
            try:
                c = conn.cursor()
                ret = super(HarktParaTalep, self).write(vals)
                self.set_followers()
                para_talep = self.env["harkt.para.talep"].sudo().search([("id", "=", self.id)])
                emp = self.env["hr.employee"].sudo().search([("user_id", "=", para_talep.talep_eden_id.id)])
                if len(emp) == 0:
                    raise UserError("Talep eden çalışan bulunamadı")
                if para_talep.ref_talep:
                    ref_talep = para_talep.ref_talep.talep_no
                else:
                    ref_talep = None
                print(ref_talep)

                lines = ""
                satir_no=1
                for rec in para_talep.talep_satir_ids:
                    if not rec.satir_no:
                        rec.satir_no = satir_no
                        satir_no = satir_no + 1
                    else:
                        satir_no = rec.satir_no +1
                    line_emp = False
                    if rec.talep_edilen_id:
                        line_emp = self.env["hr.employee"].sudo().search(
                            [("user_id", "=", rec.talep_edilen_id.id)])
                        if len(line_emp) > 0:
                            line_emp = line_emp[0]

                    lines = lines + """
                        <ParaTalebiSatir>
                            <SATIR_NO>""" + str(rec.satir_no) + """</SATIR_NO>
                            <ONGRUP_NO>""" + (rec.ongrup_id.ongrup_kodu or "") + """</ONGRUP_NO>
                            <MASRAF_TURU>""" + (rec.masraf_turu_id.masraf_turu_kodu or "") + """</MASRAF_TURU>
                            <COMPANY_ID>""" + (para_talep.tr_company_id.code or "") + """</COMPANY_ID>
                            <PROJECT_ID>""" + (para_talep.project_id.code or "") + """</PROJECT_ID>
                            <BOLGE_ID>""" + (rec.bolge_id.code or "") + """</BOLGE_ID>
                            <HARICI>""" + ("TRUE" if rec.harici else "FALSE") + """</HARICI>
                            <TALEP_EDILEN_ID>""" + (("P"+line_emp.person_id) if line_emp else "") + """</TALEP_EDILEN_ID>
                            <VARLIK_ID>""" + (rec.varlik_id.code or "") + """</VARLIK_ID>
                            <MIKTAR>""" + (str(rec.miktar) or "") + """</MIKTAR>
                            <TUTAR>""" + (str(rec.tutar) or "") + """</TUTAR>
                            <DOVIZ_KURU>"""+(str(rec.currency_rate) or "1")+ """</DOVIZ_KURU>
                            <ULKE>""" + (rec.country_id.code or "") + """</ULKE>
                            <KIRALIK>""" + ("TRUE" if rec.kiralik else "FALSE") + """</KIRALIK>
                            <KIRALIK_PLAKA>""" + (rec.kiralik_plaka or "") + """</KIRALIK_PLAKA>
                            <ACIKLAMA>""" + (rec.aciklama or "") + """</ACIKLAMA>
                            <HARICI_KIMLIK_NO>""" + (rec.harici_kimlik_no or "") + """</HARICI_KIMLIK_NO>
                            <HARICI_ADRES>""" + (rec.harici_adres or "") + """</HARICI_ADRES>
                            <HARICI_TELEFON>""" + (rec.harici_telefon or "") + """</HARICI_TELEFON>
                            <HARICI_IBAN>""" + (rec.harici_iban or "") + """</HARICI_IBAN>
                            <HARICI_AD_SOYAD>""" + (rec.harici_ad_soyad or "") + """</HARICI_AD_SOYAD>
                            <IS_TAKIP_NO>""" + (rec.is_takip_no or "") + """</IS_TAKIP_NO>
                        </ParaTalebiSatir>
                        """

                details = """<?xml version="1.0" encoding="utf-16"?>
                        <ParaTalebi xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                            <COMPANY_ID>""" + (para_talep.tr_company_id.code or "") + """</COMPANY_ID>
                            <USER_ID>""" + (
                    (emp[0].emp_no + "-" + emp.name) if (emp and emp.emp_no and emp.name) else "") + """</USER_ID>
                            <TALEP_TARIHI>""" + (para_talep.talep_tarihi.strftime("%Y-%M-%d") or "") + """</TALEP_TARIHI>
                            <BOLUM>""" + (para_talep.bolum_id.name or "") + """</BOLUM>
                            <NOTLAR>""" + (para_talep.notlar or "") + """</NOTLAR>
                            <PARA_BIRIMI>""" + (para_talep.currency_id.name or "") + """</PARA_BIRIMI>
                            <PROJE>""" + (para_talep.project_id.code or "") + """</PROJE>
                            <PROJE_TURU>""" + (para_talep.proje_turu or "") + """</PROJE_TURU>
                            <DURUM>""" + ("" if "state" not in vals else para_talep.state) + """</DURUM>
                            <REF_TALEP>""" + (ref_talep or "") + """</REF_TALEP>
                            <ParaTalebiSatirlar>
                                """ + lines + """
                            </ParaTalebiSatirlar>
                        </ParaTalebi>"""
                c.execute(
                    """
                    BEGIN
                        IFSAPP.odoo_portal_api.para_talebi_odoo2_ifs(
                              :COMPANY_ID,
                              :USER_ID,
                              :TALEP_TARIHI,
                              :BOLUM,
                              :NOTLAR,
                              :PARA_BIRIMI,
                              :PROJE,
                              :PROJE_TURU,
                              :DURUM,
                              :REF_TALEP,
                              :DETAILS,
                              :SONUC);
                    END;""",
                    COMPANY_ID=para_talep.tr_company_id.code or None,
                    USER_ID=(emp[0].emp_no + "-" + emp.name) if (emp.emp_no and emp.name) else None,
                    TALEP_TARIHI=para_talep.talep_tarihi or None,
                    BOLUM=para_talep.bolum_id.name or None,
                    NOTLAR=para_talep.notlar or None,
                    PARA_BIRIMI=para_talep.currency_id.name or None,
                    PROJE=para_talep.project_id.code or None,
                    PROJE_TURU=para_talep.proje_turu or None,
                    DURUM=("" if "state" not in vals else para_talep.state),
                    REF_TALEP=ref_talep or None,
                    DETAILS=details,
                    SONUC=para_talep.talep_no
                )

                print(para_talep.talep_no)
                conn.commit()
            except Exception as ex:
                conn.rollback()
                print(ex)
                raise UserError(self.env["oracle.conn"].simplify_error_message(ex))
            return ret


    @api.model
    def remove_func(self, vals):
        self.env.cr.execute("""delete from harkt_para_talep where talep_no=%s""", (vals.get("talep_no"),))
        return True

    @api.model
    def write_or_create(self, vals):
        print(vals)
        try:
            tr_company_id = self.env["tr.company"].search([("code", "=", vals.get("company"))]).id
            rec = self.env["harkt.para.talep"].search(
                [("talep_no", "=", vals.get("talep_no")),
                 ("tr_company_id", "=", tr_company_id)
                 ])
            emp = self.env["hr.employee"].sudo().search([("emp_no","=",vals.get("kisi_id"))])
            talep_eden_id = None
            if len(emp)>0:
                emp = emp[0]
                if emp.user_id:
                    talep_eden_id = emp.user_id.id
            bolum_id = None
            bolum = self.env["harkt.muhasebe.kodu"].search([("tr_company_id","=",tr_company_id),
                                                            ("kod_yapisi","=","B"),
                                                            ("name", "=", vals.get("bolum"))])
            if len(bolum)>0:
                bolum_id = bolum[0].id
            currency_id = None
            currency = self.env["res.currency"].search([("name", "=", vals.get("currency_code"))])
            if len(currency)>0:
                currency_id = currency[0].id
            project_id = None
            project = self.env["harkt.proje"].search([("code", "=", vals.get("proje"))])
            if len(project) > 0:
                project_id = project[0].id
            ref_talep_id = None
            if vals.get("ref_talep_no"):
                ref_talep = self.env["harkt.para.talep"].search(
                    [("talep_no", "=", vals.get("ref_talep_no")),
                     ("tr_company_id", "=", tr_company_id)
                     ])
                if len(ref_talep)>0:
                    ref_talep_id = ref_talep.id
            result = False
            data = {
                "tr_company_id": tr_company_id,
                "talep_no": vals.get("talep_no"),
                "talep_eden_id": talep_eden_id,
                "bolum_id": bolum_id,
                "notlar": vals.get("notlar"),
                "currency_id": currency_id,
                "talep_tarihi": vals.get("talep_tarihi"),
                "project_id": project_id,
                "proje_turu": vals.get("proje_turu"),
                "ref_talep": ref_talep_id,
                "state": vals.get("durum"),
                "supercall": True
            }
            if len(rec) == 0:
                ret = self.create(data)
                onaylayici = False
                sequence_no = 0
                route = 0
                for onay in vals.get("histories"):
                    onay["para_talep_id"] = ret.id
                    self.env["harkt.para.talep.onay"].create(onay)
                    if not onay.get("approver_sign") and not onaylayici:
                        onaylayici = onay["emp_no"]
                        sequence_no = onay["sequence_no"]
                        route = onay["route"]

                self.write({
                    "sequence_no": sequence_no,
                    "route": route,
                    "supercall": True
                })
                emp = self.env["hr.employee"].sudo().search([("person_id", "=", onaylayici)])
                print("sonraki onaylayıcıı")
                print(emp)
                if len(emp) == 1:
                    self.write({
                        "next_approver_ids": [emp.user_id.id],
                        "next_approver_id": emp.user_id.id,
                        "supercall": True
                    })
                result = True
            else:
                ret = rec.write(data)
                self.env.cr.execute("""delete from harkt_para_talep_onay where para_talep_id="""+str(rec.id))
                onaylayici = False
                sequence_no = 0
                route = 0
                for onay in vals.get("histories"):
                    onay["para_talep_id"] = rec.id
                    self.env["harkt.para.talep.onay"].create(onay)
                    if not onay.get("approver_sign") and not onaylayici:
                        onaylayici = onay["emp_no"]
                        sequence_no = onay["sequence_no"]
                        route = onay["route"]
                rec.write({
                    "sequence_no": sequence_no,
                    "route": route,
                    "supercall": True
                })
                emp = self.env["hr.employee"].sudo().search([("person_id", "=", onaylayici)])
                #print("sonraki onaylayıcı")
                #print(onaylayici)
                #print(emp.user_id.id)
                if len(emp) == 1:
                    rec.write({
                        "next_approver_ids": [emp.user_id.id],
                        "next_approver_id": emp.user_id.id,
                        "supercall": True
                    })
                result = True
            rec.set_followers()
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
                            ODOO_PORTAL_API.para_sil_odoo2_ifs(:TALEP_ID);
                        END;
                        """,
                      TALEP_ID = self.talep_no,
            )
            self.env.cr.execute("""delete from harkt_para_talep where id=%s""", (self.id,))
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
        for satir in self.talep_satir_ids:
            partner_ids.append(satir.talep_edilen_id.partner_id.id)
        #talep edenin 1. amirini takipçi olarak ekliyoruz
        partner_ids.append(self.talep_eden_id.employee_id.parent_id.user_id.partner_id.id)
        # talep edenin 2. amirini takipçi olarak ekliyoruz
        partner_ids.append(self.talep_eden_id.employee_id.parent_id.parent_id.user_id.partner_id.id)
        #satırdaki kişilerin 1. amirini takipçi olarak ekliyoruz
        for satir in self.talep_satir_ids:
            if satir.talep_edilen_id:
                partner_ids.append(satir.talep_edilen_id.employee_id.parent_id.user_id.partner_id.id)
        # satırdaki kişilerin 2. amirini takipçi olarak ekliyoruz
        for satir in self.talep_satir_ids:
            if satir.talep_edilen_id:
                partner_ids.append(satir.talep_edilen_id.employee_id.parent_id.parent_id.user_id.partner_id.id)
        #onaylayıcıları takipçi olarak ekliyoruz
        for onay in self.onay_ids:
            if onay.authorize_id:
                partner_ids.append(onay.authorize_id.partner_id.id)
        partner_ids = list(dict.fromkeys(partner_ids))
        partner_ids = [i for i in partner_ids if i]
        for partner_id in partner_ids:
            if partner_id and not self.env['mail.followers'].search([('res_id', '=', self.id),('res_model', '=', "harkt.para.talep"),('partner_id', '=', partner_id)]):
                self.env['mail.followers'].sudo().create({
                    "res_id": self.id,
                    "res_model": "harkt.para.talep",
                    "partner_id": partner_id
                })