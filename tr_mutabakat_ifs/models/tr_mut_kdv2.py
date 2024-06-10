from datetime import datetime, date, timedelta

import werkzeug

from odoo import models, fields, api
from odoo.exceptions import UserError


class TrMutKdv2(models.Model):
    _name = 'tr.mut.kdv2'
    _description = "KDV2 Bildirim"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "tarih desc,name asc"
    name = fields.Char("Ad", compute="_compute_name", store=True)
    company_id = fields.Many2one("res.company", string="Şirket", default=lambda self: self.env.company, required=True)
    tarih = fields.Date("Mutabakat Tarihi", required=True, default = datetime.today())
    donem_id = fields.Many2one("tr.mut.donem", string="Mutabakat Dönemi", compute="_compute_donem_id", store=True)
    partner_id = fields.Many2one("res.partner", string="Firma", required=True)
    vat = fields.Char("Vkn/Tckn No", related="partner_id.vat", store=True, readonly=False)
    email = fields.Char("Email", related="partner_id.email", store=True, readonly=False)
    tevkifat_tipi = fields.Char("Tevkifat Tipi")
    tevkifat_tutari = fields.Float("Tevkifat Tutarı")
    matrah = fields.Float("Matrah")
    ilgili_faturalar = fields.Text("İlgili Faturalar")
    state = fields.Selection([("Taslak", "Taslak"),
                              ("Gönderildi", "Gönderildi"),
                              ("Kabul Edildi", "Kabul Edildi"),
                              ("Reddedildi", "Reddedildi")
                              ],
                             default="Taslak", string="Durum", tracking=True)

    survey_input_id = fields.Many2one("survey.user_input", "Mutabakat Yanıtı")
    survey_start_url = fields.Char("Anket Url", compute="_compute_survey_start_url", store=True)
    red_aciklama = fields.Char("Red Açıklama", tracking=True)

    def action_yanit_sifirla(self):
        for rec in self:
            rec.write({
                'state':'Taslak',
                'survey_input_id':False
            })

    @api.depends('survey_input_id', 'survey_input_id.access_token')
    def _compute_survey_start_url(self):
        for invite in self:
            adres = invite.survey_input_id.get_base_url().replace("192.168.1.15", "212.174.9.78")
            invite.survey_start_url = werkzeug.urls.url_join(adres,
                                                             invite.survey_input_id.get_start_url().
                                                             replace("/start", "").
                                                             replace("?answer_token=","/")) if invite.survey_input_id else False

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        self.filtered(lambda o: o.state == 'Taslak' and o.email).with_context(tracking_disable=True).write(
            {'state': 'Gönderildi'})
        return super(TrMutKdv2, self.with_context(
            mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    @api.depends("diger_para")
    def _compute_diger_para_varmi(self):
        for rec in self:
            if rec.diger_para and rec.diger_para != 0:
                rec.diger_para_varmi = "Evet"
            else:
                rec.diger_para_varmi = "Hayır"

    @api.depends("partner_id","partner_id.name", "donem_id")
    def _compute_name(self):
        for rec in self:
            if rec.partner_id and rec.donem_id:
                rec.name = str(rec.partner_id.name)+"-"+rec.donem_id.name
            else:
                rec.name = ''

    @api.depends("tarih")
    def _compute_donem_id(self):
        for rec in self:
            period_name = str(rec.tarih.year) + "-" + str(rec.tarih.month).zfill(2)
            result = self.env["tr.mut.donem"].search([("name", "=", period_name)])
            if len(result) == 0:
                result = self.env["tr.mut.donem"].create({
                    "name": period_name
                })
            rec.donem_id = result.id

    def action_tekrar_hesapla(self):
        for rec in self:
            if rec.state in("Taslak"):
                rec._ifs_kdv2_getir(rec.company_id.ifs_sirket_kodu, rec.tarih.strftime('%d.%m.%Y'), rec.vat)

    def _ifs_kdv2_getir(self, ifs_sirket_kodu, tarih, vkn_tckn_no):
        try:
            conn = self.env["oracle.conn"].connect(False, False)
            c = conn.cursor()

            if not tarih:
                bitis_tarihi = date(year=datetime.today().year, month=datetime.today().month, day=1) - timedelta(days=1)
            else:
                bitis_tarihi = datetime.strptime(tarih,'%d.%m.%Y')
            print(bitis_tarihi)

            company = self.env["res.company"].sudo().search([("ifs_sirket_kodu","=", ifs_sirket_kodu)])
            period_name = str(bitis_tarihi.year) + "-" + str(bitis_tarihi.month).zfill(2)
            donem = self.env["tr.mut.donem"].search([("name", "=", period_name)])
            if len(donem) == 0:
                donem = self.env["tr.mut.donem"].create({
                    "name": period_name
                })

            c.execute("""
                        select 
                            a.association_no vergi_No,
                            min(identity) identity,
                            min(name) name,
                            min(email) email,
                            tevkifat_aciklama,
                            sum(tevkifat_tutar) tevkifat_tutar,
                            0 matrah,
                            LISTAGG(fatura_no, ', ') faturalar
                            from 
                            (                   
                              SELECT 
                                  s.association_no,
                                  s.supplier_id identity, 
                                  s.name name,
                                  nvl((select 
                                    case when instr(nvl(primary_contact_email,'-'),'@')>0 and instr(nvl(secondary_contact_email,'-'),'@')>0 then primary_contact_email||','||secondary_contact_email 
                                    when instr(nvl(primary_contact_email,'-'),'@')>0 and instr(nvl(secondary_contact_email,'-'),'@')<=0 then primary_contact_email
                                    when  instr(nvl(primary_contact_email,'-'),'@')<=0 and instr(nvl(secondary_contact_email,'-'),'@')>0 then primary_contact_email
                                    else null end email
                                    from ifsapp.trpay_supp_agrmnt_contact a where a.supplier_id = q.party_type_id),
                                     (select 
                                    case when instr(nvl(primary_contact_email,'-'),'@')>0 and instr(nvl(secondary_contact_email,'-'),'@')>0 then primary_contact_email||','||secondary_contact_email 
                                    when instr(nvl(primary_contact_email,'-'),'@')>0 and instr(nvl(secondary_contact_email,'-'),'@')<=0 then primary_contact_email
                                    when  instr(nvl(primary_contact_email,'-'),'@')<=0 and instr(nvl(secondary_contact_email,'-'),'@')>0 then primary_contact_email
                                    else null end email
                                    from ifsapp.trpay_cust_agrmnt_contact a where a.customer_id = q.party_type_id))
                                      email,
                                  q.code_j tevkifat_kodu,
                                  ifsapp.code_j_api.get_description(q.company,q.code_j) tevkifat_aciklama,
                                  q.amount tevkifat_tutar, q.reference_number fatura_no
                              FROM 
                                   ifsapp.trype_all_voucher_qry q, ifsapp.supplier_info s
                              WHERE q.company = :COMPANY_CODE
                              AND s.association_no like :VKN_TCKN_NO
                              AND q.accounting_year = :YIL
                              AND q.accounting_period=:AY
                              AND q.account = '391.04'
                              AND s.association_no is not null
                              and s.association_no not in('1111111111','11111111111','2222222222','22222222222','18098263108','44201108134')
                              and s.supplier_id = q.party_type_id
                            ) a
                            group by a.association_no,
                            tevkifat_aciklama""",
                      COMPANY_CODE = ifs_sirket_kodu,
                      VKN_TCKN_NO=vkn_tckn_no,
                      YIL = bitis_tarihi.year,
                      AY = bitis_tarihi.month
                      )
            sonuclar = c.fetchall()
            for row in sonuclar:
                partner = self.env["res.partner"].search([("vat", "=", row[0])])
                if len(partner) == 0:
                    partner = self.env["res.partner"].create({
                        "vat": row[0],
                        "name": row[2],
                        "ref": row[1],
                        "email": row[3],
                    })
                else:
                    partner = partner[0]
                    partner.write({
                        "vat": row[0],
                        "name": row[2] if row[2] else partner.name,
                        "ref": row[1] if row[1] else partner.ref,
                        "email": row[3] if row[3] else partner.email
                    })

                mut = self.env["tr.mut.kdv2"].search(
                    [("company_id", "=", company.id),
                     ("partner_id", "=", partner.id),
                     ("donem_id", "=", donem.id),
                     ("tevkifat_tipi", "=", row[4]),
                     ])

                if len(mut) >= 1:
                    mut[0].write({
                        "tevkifat_tutari": row[5],
                        "matrah": row[6],
                        "ilgili_faturalar": row[7]
                    })
                else:
                    self.env["tr.mut.kdv2"].create({
                        "company_id":company.id,
                        "partner_id":partner.id,
                        "tevkifat_tipi": row[4],
                        "tarih": bitis_tarihi,
                        "tevkifat_tutari": row[5],
                        "matrah": row[6],
                        "ilgili_faturalar": row[7]
                    })
            self._cr.execute("""update tr_mut_kdv 
                set tevkifat_tutari =coalesce(tevkifat_tutari,0),
                    matrah=coalesce(matrah,0)
                where donem_id = """ + donem.id)

        except Exception as ex:
            print(ex)
        finally:
            print("finally")

    def btn_send_mail(self):
        self.ensure_one()
        if self.survey_input_id:
            inputs = self.env["survey.user_input"].search([("id", "=", self.survey_input_id.id)])
            if len(inputs) == 0:
                self.survey_input_id = False

        if not self.survey_input_id:
            survey_input = self.env["survey.user_input"].create({
                "survey_id": self.env.ref("tr_mutabakat_ifs.tr_mut_kdv2_survey").id,
                "partner_id": self.partner_id.id,
                "tr_mut_kdv2_id": self.id
            })
            self.survey_input_id = survey_input.id

        template_id = self.env.ref('tr_mutabakat_ifs.mail_template_tr_mut_kdv2_eposta').id

        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        ctx = {
            'default_model': 'tr.mut.kdv2',
            'default_res_ids': [self.id],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'mark_so_as_sent': True,
            #'custom_layout': "mail.mail_notification_paynow",
            'force_email': True
        }

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            #'views': [(compose_form_id, 'form')],
            #'view_id': compose_form_id,
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def btn_send_mail_multi(self):
        for rec in self:
            if rec.survey_input_id:
                inputs = self.env["survey.user_input"].search([("id", "=", rec.survey_input_id.id)])
                if len(inputs) == 0:
                    rec.survey_input_id = False

            if not rec.survey_input_id:
                survey_input = self.env["survey.user_input"].create({
                    "survey_id": self.env.ref("tr_mutabakat_ifs.tr_mut_kdv2_survey").id,
                    "partner_id": rec.partner_id.id,
                    "tr_mut_kdv2_id": rec.id
                })
                rec.survey_input_id = survey_input.id
            template_id= self.env.ref('tr_mutabakat_ifs.mail_template_tr_mut_kdv2_eposta').id
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(rec.id)
            if rec.state == "Taslak":
                rec.state = "Gönderildi"

    def write(self, vals):
        ret = super(TrMutKdv2, self).write(vals)
        if vals.get("state"):
            if vals.get("state") == "Taslak" and self.survey_input_id:
                raise UserError("Taslağa çevirmek için lütfen Yanıt Sıfırla düğmesini kullanınız.")
        return ret



