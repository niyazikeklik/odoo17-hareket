###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class HelpdeskTicketTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    allow_timesheet = fields.Boolean()

    # 'default_project_id' field is already defined in helpdesk_mgmt_project module.
    # default_project_id = fields.Many2one(
    #     comodel_name="project.project",
    #     string="Default Project",
    # )

    @api.constrains("allow_timesheet")
    def _check_constrains_allow_timesheet(self):
        if not self.allow_timesheet:
            self.default_project_id = False
