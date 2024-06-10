# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import suds
from suds.client import Client


class TrCompany(models.Model):
    _name = "tr.company"
    _description = "Group Company"
    _inherit = ['mail.thread']
    _order = "name"

    name = fields.Char('Group Company Name', required=True)
    code = fields.Char('Group Company Code', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True,default=lambda self: self.env.company, required=True)
    note = fields.Text('Notes')
    logo = fields.Binary("Logo", required=False)
    official_name= fields.Char("Official Name")
    address = fields.Char("Address")
    phone = fields.Char("Phone")
    fax = fields.Char("Fax")
    website = fields.Char("Website")
    tax_number = fields.Char("Tax Number")


