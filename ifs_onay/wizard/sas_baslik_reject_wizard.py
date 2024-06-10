from odoo import api, fields, models
from odoo.exceptions import UserError


class SasBaslikRejectWizard(models.TransientModel):
    _name = 'sas.baslik.reject.wizard'
    _description = 'Satınalma Siparişi Reddi'

    workflow_id = fields.Integer("Sipariş Id", default=lambda self: self.env.context.get('active_id', None))
    red_kodu_id =fields.Many2one("sas.red.kodu", "Red Kodu")
    reject_reason = fields.Char(string="Red Açıklama")

    def action_reject_with_reason(self):
        if not self.reject_reason:
            raise UserError('Red Sebebi girilmeden reddedilemez')
        workflow = self.env["sas.baslik"].search([('id', '=', self.workflow_id)])
        """workflow.write({
            'reject_reason': self.reject_reason,
            'red_kodu_id': self.red_kodu_id
        })"""
        conn = self.env["oracle.conn"].connect(False, False)

        try:
            c = conn.cursor()
            c.callproc("ifsapp.odoo_portal_api.reject_sas",
                       [workflow.order_no,
                        workflow.change_order_no,
                        workflow.sequence_no,
                        self.red_kodu_id.reject_code,
                        self.reject_reason])
            conn.commit()
            action = self.env.ref("ifs_onay.sas_baslik_action").read()[0]
            #workflow.remove_sas()
            res_action = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Başarılı',
                    'message': "Başarıyla Reddedildi",
                    'sticky': False,  # True/False will display for few seconds if false
                    'next': action,
                }
            }
            return res_action
        except Exception as e:
            res_action = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Başarılı',
                    'message': e,
                    'sticky': False,  # True/False will display for few seconds if false
                    'next': {'type': 'ir.actions.client','tag': 'reload',},
                }
            }
            return res_action
            #raise UserError(e)
        #return workflow.action_reject(self.reject_reason, self.red_kodu_id)
        """return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }"""