# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrWorkResMontaj(models.Model):
    _name = 'hr.work.res.montaj'
    _description = "Res Montage of Work Entry"
    _order = "id desc"

    work_entry_id = fields.Many2one("hr.work.entry", "Work Entry")
    res_montaj_tipi_id = fields.Many2one("hr.res.montaj.tipi", "Res Montage Type")
    tirbun_no = fields.Char("Tirbun No")
    aciklama = fields.Char("Description")
    toplam_saat = fields.Float("Saat")