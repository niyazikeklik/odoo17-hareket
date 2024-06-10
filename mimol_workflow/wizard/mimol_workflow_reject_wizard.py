from odoo import api, fields, models
from odoo.exceptions import UserError


class MimolWorkflowRejectWizard(models.TransientModel):
    _name = 'mimol.workflow.reject.wizard'
    _description = 'Masraf Reddi'

    workflow_id = fields.Integer("Akış Id", default=lambda self: self.env.context.get('active_id', None))
    reject_reason = fields.Char(string="Red Sebebi")
    model_name = fields.Char("Model Name")

    def action_reject_with_reason(self):
        if not self.reject_reason:
            raise UserError('Red Sebebi girilmeden reddedilemez')
        workflow = self.env[self.model_name].search([('id', '=', self.workflow_id)])
        workflow.write({
            'reject_reason': self.reject_reason
        })
        workflow.action_reject()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }