from odoo import fields, models, api
from odoo.exceptions import UserError


class HelpdeskTicketChannel(models.Model):
    _name = "helpdesk.ticket.channel"
    _description = "Helpdesk Ticket Channel"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    isDefault = fields.Boolean(string="Default Channel", default=False)

    @api.model
    def create(self, vals):
        if vals.get("isDefault"):
            self.search([("isDefault", "=", True)]).write({"isDefault": False})
        return super(HelpdeskTicketChannel, self).create(vals)
    @api.model
    def write(self, vals):
        if vals.get("isDefault"):
            self.search([("isDefault", "=", True)]).write({"isDefault": False})
        return super(HelpdeskTicketChannel, self).write(vals)
    @api.model
    def unlink(self):
        if self.isDefault:
            raise UserError("You can not delete default channel")
        return super(HelpdeskTicketChannel, self).unlink()


