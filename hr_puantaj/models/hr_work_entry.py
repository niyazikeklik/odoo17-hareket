from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import json

from odoo.exceptions import UserError


class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    giris_enlem = fields.Float("Giriş Enlem")
    giris_boylam = fields.Float("Giriş Boylam")
    cikis_enlem = fields.Float("Çıkış Enlem")
    cikis_boylam = fields.Float("Çıkış Boylam")
    giris_adres = fields.Char("Giriş Adres")
    cikis_adres = fields.Char("Çıkış Adres")
    giris_sehir = fields.Char("Giriş Şehir")
    cikis_sehir = fields.Char("Çıkış Şehir")

    project_id = fields.Many2one("harkt.proje", string="Proje")
    activity_id =fields.Many2one("harkt.aktivite", string="Aktivite")
    yapilan_is = fields.Char("Yapılan İş")
    hr_attendance_ids = fields.One2many("hr.attendance", "work_entry_id","In Out Information")
    res_montaj_ids = fields.One2many("hr.work.res.montaj", "work_entry_id", "Res Montage")

    department_id = fields.Many2one("hr.department", related="employee_id.department_id", string="Department")
    parent_id = fields.Many2one("hr.employee", related="employee_id.parent_id", string="Manager")

    state = fields.Selection(
        selection_add=[
            ("approved", "Approved"),
        ]
    )

    def _compute_giris_cikis(self):
        for entry in self:
            ilk_giris = False
            son_cikis = False
            worked_hours = 0
            mesai =False
            proje = False
            for rec in entry.hr_attendance_ids:
                if not ilk_giris:
                    ilk_giris = rec
                elif rec.check_in < ilk_giris.check_in:
                    ilk_giris = rec

                if not son_cikis:
                    son_cikis = rec
                elif rec.check_out > son_cikis.check_out:
                    son_cikis = rec
                worked_hours = worked_hours + rec.worked_hours

            if ilk_giris and son_cikis:
                aktivite = False
                proje = son_cikis.check_out_project_id or ilk_giris.check_in_project
                mesai = son_cikis.check_out_work_type_id or ilk_giris.check_in_work_type

                if proje:
                    aktivite = self.env["harkt.aktivite"].search([("project_id", '=', proje.id)])
                    if len(aktivite) != 1:
                        aktivite = False

                entry.write({
                    "giris_enlem": ilk_giris.check_in_latitude,
                    "giris_boylam": ilk_giris.check_in_longitude,
                    "cikis_enlem": son_cikis.check_out_latitude,
                    "cikis_boylam": son_cikis.check_out_longitude,
                    "giris_adres": ilk_giris.in_address,
                    "cikis_adres": son_cikis.out_address,
                    "yapilan_is": son_cikis.check_out_work,
                    "date_start": ilk_giris.check_in,
                    "date_stop": son_cikis.check_out,
                    "duration": worked_hours,
                    "giris_sehir": ilk_giris.in_city,
                    "cikis_sehir": son_cikis.out_city,
                    "activity_id": aktivite.id if aktivite else False,
                    "work_entry_type_id": mesai.id,
                    "project_id": proje.id if proje else False
                })


    employee_ids = fields.Many2many('hr.employee', string='Çalışan', required=False)
    department_ids = fields.Many2many('hr.department', string='Departman', required=False)

    def regenerate_work_entries(self):
        self.ensure_one()
        employee_ids = self.employee_ids
        if not employee_ids:
            if self.department_ids:
                employee_ids = self.env["hr.employee"].sudo().search([("department_id", "in", self.department_ids.ids)])
        if not employee_ids:
            employee_ids = self.env["hr.employee"].sudo().search([])
        date_from = max(self.date_from,
                        self.earliest_available_date) if self.earliest_available_date else self.date_from
        date_to = min(self.date_to, self.latest_available_date) if self.latest_available_date else self.date_to
        work_entries = self.env['hr.work.entry'].search([
            ('employee_id', 'in', employee_ids.ids),
            ('date_stop', '>=', date_from),
            ('date_start', '<=', date_to),
            ('state', '!=', 'validated')])

        write_vals = {field: False for field in self._work_entry_fields_to_nullify()}
        work_entries.write(write_vals)

        employee_ids.generate_work_entries(date_from, date_to, True)
    def do_action(self, data):
        return data
    def action_gunluk_puantaj_goster(self):
        print(self.env.user.employee_id.id)
        self.env["hr.attendance"].attendance_to_work_entry_for_emp(self.env.user.employee_id.id)

        res = self.env["hr.work.entry"].search([("employee_id", "=", self.env.user.employee_id.id), ("state","=","draft")], limit = 1)
        form_id =self.env.ref("hr_puantaj.hr_work_entry_wizard_view_form")
        print(res)
        return {
            "name": _("Daily Work Entry Confirmation"),
            "view_mode": "form",
            "res_model": "hr.work.entry",
            "domain": [],
            "res_id": res.id,
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": {"active_id": res.id},
            "views": [(form_id.id, "form")],
            "target": "new"
        }
    def action_approve(self):
        self.state = "validated"




