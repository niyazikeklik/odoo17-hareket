from datetime import datetime

import werkzeug

from odoo import models, fields, api
from odoo.exceptions import UserError


class TrMut(models.Model):
    _name = 'tr.mut'
    _description = "E-Mutabakat"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "tarih desc,name asc"
    name = fields.Char("Ad", compute="_compute_name", store=True)
    company_id = fields.Many2one("res.company", string="Şirket", default=lambda self: self.env.company, required=True)
    tarih = fields.Date("Mutabakat Tarihi", required=True, default = datetime.today())
    donem_id = fields.Many2one("tr.mut.donem", string="Mutabakat Dönemi", compute="_compute_donem_id", store=True)
    partner_id = fields.Many2one("res.partner", string="Firma", required=True)
    vat = fields.Char("Vkn/Tckn No", related="partner_id.vat", store=True, readonly=False)
    email = fields.Char("Email", related="partner_id.email", store=True, readonly=False)
    bakiye_tl = fields.Float("TL Bakiye")
    bakiye_usd = fields.Float("USD Bakiye")
    bakiye_eur = fields.Float("EUR Bakiye")
    diger_para = fields.Float("Diğer Para")
    diger_para_varmi = fields.Selection([("Evet","Evet"),("Hayır","Hayır")],"Diğer Para Var mı?",compute="_compute_diger_para_varmi", store=True)
    state = fields.Selection([("Taslak","Taslak"),
                              ("Gönderildi","Gönderildi"),("Kabul Edildi","Kabul Edildi"),("Reddedildi","Reddedildi")],
                             default="Taslak", string="Durum", tracking=True)
    survey_input_id = fields.Many2one("survey.user_input", "Mutabakat Yanıtı")
    survey_start_url = fields.Char("Anket Url", compute="_compute_survey_start_url", store=True)

    red_aciklama = fields.Char("Red Açıklama", tracking=True)

    @api.depends("diger_para")
    def _compute_diger_para_varmi(self):
        for rec in self:
            if rec.diger_para and rec.diger_para != 0:
                rec.diger_para_varmi = "Evet"
            else:
                rec.diger_para_varmi = "Hayır"

    def action_yanit_sifirla(self):
        for rec in self:
            rec.write({
                'state':'Taslak',
                'survey_input_id':False
            })

    @api.depends('survey_input_id', 'survey_input_id.access_token')
    def _compute_survey_start_url(self):
        for invite in self:
            adres = invite.survey_input_id.get_base_url().replace("192.168.1.15","212.174.9.78")
            invite.survey_start_url = werkzeug.urls.url_join(adres,
                                                             invite.survey_input_id.get_start_url().
                                                             replace("/start","").
                                                             replace("?answer_token=","/")) if invite.survey_input_id else False

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        self.filtered(lambda o: o.state == 'Taslak' and o.email).with_context(tracking_disable=True).write(
            {'state': 'Gönderildi'})
        return super(TrMut, self.with_context(
            mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    def write(self, vals):
        ret = super(TrMut, self).write(vals)
        if vals.get("state"):
            if vals.get("state") == "Taslak" and self.survey_input_id:
                raise UserError("Taslağa çevirmek için lütfen Yanıt Sıfırla düğmesini kullanınız.")
        return ret

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



    def btn_send_mail(self):
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

        template_id = self.env.ref('tr_mutabakat.mail_template_tr_mut_eposta').id

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

    def btn_send_mail_multi(self):
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

            template_id= self.env.ref('tr_mutabakat.mail_template_tr_mut_eposta').id
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(rec.id)
            if rec.state == "Taslak":
                rec.state = "Gönderildi"



