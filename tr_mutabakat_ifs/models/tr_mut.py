from datetime import date, timedelta, datetime

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import config


class TrMut(models.Model):
    _inherit = 'tr.mut'

    ilk_ekstre_tarihi = fields.Date("İlk Ekstre Tarihi", default=date(date.today().year, 1, 1) if date.today().month>=4 else date(date.today().year-1, 1, 1))

    def action_tekrar_hesapla(self):
        for rec in self:
            if rec.state in("Taslak","Reddedildi"):
                rec._ifs_cari_mutabakat_getir(rec.company_id.ifs_sirket_kodu, rec.tarih.strftime('%d.%m.%Y'), rec.vat, 0)

    def _ifs_cari_mutabakat_getir(self, ifs_sirket_kodu, tarih, vkn_tckn_no, min_hareket_sayisi):
        try:
            if not tarih:
                bitis_tarihi = date(year=date.today().year, month=date.today().month, day=1) - timedelta(days=1)
            else:
                bitis_tarihi = datetime.strptime(tarih,'%d.%m.%Y')
            company = self.env["res.company"].sudo().search([("ifs_sirket_kodu","=", ifs_sirket_kodu)])
            period_name = str(bitis_tarihi.year) + "-" + str(bitis_tarihi.month).zfill(2)
            donem = self.env["tr.mut.donem"].search([("name", "=", period_name)])
            if len(donem) == 0:
                donem = self.env["tr.mut.donem"].create({
                    "name": period_name
                })
            conn = self.env["oracle.conn"].connect(False, False)
            c = conn.cursor()
            c.execute("""
            select vat_number, currency_code, identity, name, 
                        nvl((select 
                        case when instr(nvl(primary_contact_email,'-'),'@')>0 and instr(nvl(secondary_contact_email,'-'),'@')>0 then primary_contact_email||','||secondary_contact_email 
                        when instr(nvl(primary_contact_email,'-'),'@')>0 and instr(nvl(secondary_contact_email,'-'),'@')<=0 then primary_contact_email
                        when  instr(nvl(primary_contact_email,'-'),'@')<=0 and instr(nvl(secondary_contact_email,'-'),'@')>0 then primary_contact_email
                        else null end email
                        from ifsapp.trpay_supp_agrmnt_contact a where a.supplier_id = qq.identity),
                         (select 
                        case when instr(nvl(primary_contact_email,'-'),'@')>0 and instr(nvl(secondary_contact_email,'-'),'@')>0 then primary_contact_email||','||secondary_contact_email 
                        when instr(nvl(primary_contact_email,'-'),'@')>0 and instr(nvl(secondary_contact_email,'-'),'@')<=0 then primary_contact_email
                        when  instr(nvl(primary_contact_email,'-'),'@')<=0 and instr(nvl(secondary_contact_email,'-'),'@')>0 then primary_contact_email
                        else null end email
                        from ifsapp.trpay_cust_agrmnt_contact a where a.customer_id = qq.identity))
                          email,
                        amount,
                        bu_ayki_hareket from
                        (
                        SELECT 
                            q.vat_number,
                            q.currency_code, 
                            max(q.identity) identity, 
                            max(q.name) name,
                            sum(q.full_curr_amount) amount,
                            nvl(sum((case when to_char(voucher_date,'MMyyyy')= to_char(:BITIS_TARIHI,'MMyyyy') then 1 else 0 end)),0) bu_ayki_hareket
                        FROM ifsapp.trype_all_ledger_qry q 
                        WHERE q.company = :COMPANY_CODE 
                        AND q.vat_number like :VKN_TCKN_NO 
                        AND q.voucher_date <= :BITIS_TARIHI
                        AND q.vat_number is not null 
                        and q.vat_number not in('1111111111','11111111111','2222222222','22222222222','18098263108','44201108134')
                        group by q.vat_number, q.currency_code) qq""",
                      COMPANY_CODE = ifs_sirket_kodu,
                      VKN_TCKN_NO=vkn_tckn_no,
                      BITIS_TARIHI = bitis_tarihi
                      )
            sonuclar = c.fetchall()
            for row in sonuclar:
                if row[6] >= min_hareket_sayisi:
                    dvz = ("bakiye_tl" if row[1] in( "TL", 'TRY') else ('bakiye_usd' if row[1]=="USD" else ("bakiye_eur" if row[1]=="EUR" else "diger_para")))
                    partner = self.env["res.partner"].search([("vat", "=", row[0])], limit=1)
                    if len(partner) == 0:
                        partner = self.env["res.partner"].create({
                            "vat": row[0],
                            "name": row[3],
                            "ref": row[2],
                            "email": row[4]
                        })
                    else:
                        partner.write({
                            "vat": row[0],
                            "name": row[3] if row[3] else partner.name,
                            "ref": row[2] if row[2] else partner.ref,
                            "email": row[4] if row[4] else partner.email
                        })

                    mut = self.env["tr.mut"].search(
                        [("company_id", "=", company.id), ("partner_id", "=", partner.id), ("donem_id", "=", donem.id),
                         ("state", "in", ["Taslak", "Reddedildi"])])

                    if len(mut) >= 1:
                        mut[0].write({
                            "tarih": bitis_tarihi,
                            dvz:row[5]
                        })
                    else:
                        self.env["tr.mut"].create({
                            "company_id":company.id,
                            dvz: row[5],
                            "partner_id":partner.id,
                            "tarih": bitis_tarihi
                        })

            self._cr.execute("""update tr_mut 
            set bakiye_tl=coalesce(bakiye_tl,0),
                bakiye_usd=coalesce(bakiye_usd,0),
                bakiye_eur=coalesce(bakiye_eur,0),
                diger_para=coalesce(diger_para,0)
            where donem_id = """+donem.id)

        except Exception as ex:
            print(ex)
        finally:
            print("finally")

    def btn_cari_ekstre_mail(self):
        self.ensure_one()
        if self.survey_input_id:
            inputs = self.env["survey.user_input"].search([("id","=",self.survey_input_id.id)])
            if len(inputs) == 0:
                self.survey_input_id = False

        if not self.survey_input_id:
            survey_input = self.env["survey.user_input"].create({
                "survey_id": self.env.ref("tr_mutabakat.tr_mut_survey").id,
                "partner_id": self.partner_id.id,
                "tr_mut_id": self.id
            })
            self.survey_input_id = survey_input.id

        template_id = self.env.ref('tr_mutabakat_ifs.mail_template_tr_cari_ekstre_eposta').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        ctx = {
            'default_model': 'tr.mut',
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

    def btn_cari_ekstre_mail_multi(self):
        for rec in self:
            if rec.survey_input_id:
                inputs = self.env["survey.user_input"].search([("id","=",rec.survey_input_id.id)])
                if len(inputs) == 0:
                    rec.survey_input_id = False
            if not rec.survey_input_id:
                survey_input = self.env["survey.user_input"].create({
                    "survey_id": self.env.ref("tr_mutabakat.tr_mut_survey").id,
                    "partner_id": rec.partner_id.id,
                    "tr_mut_id": rec.id
                })
                rec.survey_input_id = survey_input.id

            template_id = self.env.ref('tr_mutabakat_ifs.mail_template_tr_cari_ekstre_eposta').id
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(rec.id)

    def action_open_ssrs_extre(self):
        if config.get("ssrs_ekstre_link"):
            adres = config.get("ssrs_ekstre_link")
            adres = adres + "&SIRKET=" + self.company_id.ifs_sirket_kodu + \
                    "&VKN_TCKN_NO=" + self.vat + \
                    "&ILK_TARIH=" + self.ilk_ekstre_tarihi.strftime("%d.%m.%Y") + \
                    "&SON_TARIH=" + self.tarih.strftime("%d.%m.%Y")
            return {
                'type': 'ir.actions.act_url',
                'url': adres,
                'target': 'blank'
            }
        else:
            raise UserError("Lisansınız bu işlem için uygun değil")

