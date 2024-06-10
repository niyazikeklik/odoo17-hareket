from dateutil.utils import today

from odoo import models, fields, api
from datetime import datetime,timedelta

from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    oracle_username = fields.Char("Oracle Username")
    oracle_password = fields.Char("Oracle Password")

    def action_test(self):
        if self.oracle_username and self.oracle_password:
            try:
                conn = self.env["oracle.conn"].connect(False, False)
                conn.close()
            except Exception as ex:
                raise UserError("Bağlantı testi başarısız. Kullanıcı adı veya şifresi hatalı olabilir.")
            title = "Başarılı"
            message = "Bağlantı başarılı"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': title,
                    'message': message,
                    'sticky': False,
                }
            }
        else:
            raise UserError("Önce IFS kullanıcı adı ve şifresi girilmelidir.")