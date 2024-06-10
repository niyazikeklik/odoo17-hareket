# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrResMontajTipi(models.Model):
    _name = 'hr.res.montaj.tipi'
    _description = "Res Montaj Types"
    _order = "id desc"

    code = fields.Char("Code")
    name = fields.Char("Name")
    active = fields.Boolean("Active", default = True)