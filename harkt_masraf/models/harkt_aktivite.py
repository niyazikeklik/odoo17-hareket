from odoo import models, fields, api
import json

from odoo.exceptions import UserError


class HarktAktivite(models.Model):
    _name = 'harkt.aktivite'
    _description = "Hareket Proje Aktivite"
    _rec_name = "display_name"


    activity_seq = fields.Integer("Aktivite Sıra No", required=True)
    activity_no =fields.Char("Aktivite No")
    project_id = fields.Many2one("harkt.proje","Proje",
                                 domain="[('tr_company_id', '=', tr_company_id),('kod_yapisi', '=', 'F')]", index=True)
    sub_project_no = fields.Char("Alt Proje No")
    activity_name = fields.Char("Aktivite Adı")

    display_name = fields.Char("Ad", compute="_compute_display_name")
    state =fields.Char("Durum")
    active = fields.Boolean("Aktif?", compute="_compute_active", store=True)

    @api.depends("state")
    def _compute_active(self):
        for rec in self:
            if rec.state == "Closed":
                rec.active = False
            else:
                rec.active = True

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = str(rec.activity_seq) + " - " + rec.activity_name

    def delete(self, activity_seq):
        self.env.cr.execute("delete from harkt_aktivite where activity_seq = '" + activity_seq + "'")
        return True

    @api.model
    def write_or_create(self, vals):
        print(vals)
        rec = self.env["harkt.aktivite"].search(
            [("activity_seq", "=", vals.get("activity_seq"))])
        project = self.env["harkt.proje"].search([("code", "=", vals.get("project"))])
        if len(project)>=1:
            project = project[0]
        else:
            project = False
        print(project)
        result = False

        data = {
            "project_id": project.id,
            "activity_seq": vals.get("activity_seq"),
            "activity_name": vals.get("activity_name"),
            "sub_project_no": vals.get("sub_project_no"),
            "activity_no": vals.get("activity_no"),
            "state": vals.get("state")
        }
        if len(rec) == 0:
            ret = self.env["harkt.aktivite"].create(data)
            result = True
        else:
            ret = rec.write(data)
            result = True
        return result