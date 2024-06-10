from dateutil.utils import today

from odoo import models, fields, api
from datetime import datetime,timedelta

from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    oracle_server = fields.Char("Oracle Server")
    oracle_port = fields.Char("Oracle Port")
    oracle_service_name = fields.Char("Oracle Service Name")
    oracle_generic_username = fields.Char("Oracle Generic Username")
    oracle_generic_password = fields.Char("Oracle Generic Password")
    oracle_client_path = fields.Char("Oracle Client Installation Path")

