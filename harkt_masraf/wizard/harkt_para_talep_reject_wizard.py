from odoo import api, fields, models
from odoo.exceptions import UserError


class HarktParaTalepRejectWizard(models.TransientModel):
    _name = 'harkt.para.talep.reject.wizard'
    _description = 'Hareket Para Talebi Reddi'

    workflow_id = fields.Integer("Para Talep Id", default=lambda self: self.env.context.get('active_id', None))
    reject_reason = fields.Char(string="Red Açıklama")

    def action_reject_with_reason(self):
        if not self.reject_reason:
            raise UserError('Red Sebebi girilmeden reddedilemez')
        workflow = self.env["harkt.para.talep"].search([('id', '=', self.workflow_id)])
        conn = self.env["oracle.conn"].connect(False, False)
        try:
            c = conn.cursor()
            c.execute("""
                       BEGIN
                           ifsapp.odoo_portal_api.para_talebi_onay_odoo2_ifs(:TALEP_NO, :SEQUENCE_NO, :ROUTE, 'REJ', :NOTE);
                       END;""",
                      TALEP_NO=workflow.talep_no,
                      SEQUENCE_NO=workflow.sequence_no,
                      ROUTE=workflow.route,
                      NOTE=self.reject_reason)
            conn.commit()

            #c.callproc("ifsapp.odoo_portal_api.para_talebi_red",
            #           [workflow.talep_no,
            #             self.reject_reason])
            conn.commit()
            #workflow.remove_sas()
            res_action = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Başarılı',
                    'message': "Başarıyla Reddedildi",
                    'sticky': False,  # True/False will display for few seconds if false
                    'next': {'type': 'ir.actions.client','tag': 'reload',},
                }
            }
            return res_action
        except Exception as e:
            res_action = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Bir hata oluştu',
                    'message': e,
                    'sticky': False  # True/False will display for few seconds if false
                }
            }
            return res_action