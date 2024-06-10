#helpdesk.cancel.reason
from odoo import api, fields, models

class HelpdeskCancelReason(models.Model):
    _inherit = "helpdesk.ticket"
    _name = "helpdesk.cancel.reason"
    _description = "Helpdesk Cancel Reason"

    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        string="Ticket",
        required=True,
        ondelete="cascade",
        readonly=True,
        default=lambda self: self._context.get("active_id"),

    )
    #one to one 
    #ticket_id = fields.Many2one(comodel_name="helpdesk.ticket", string="Ticket", required=True, ondelete="cascade", readonly=True, default=lambda self:
    #self._context.get("active_id"),)
    
    
    #one to many
    #ticket_ids = fields.One2many(comodel_name="helpdesk.ticket", inverse_name="cancel_reason_id", string="Tickets", required=True, ondelete="cascade", readonly=True, default=lambda self: self._context.get("active_ids"),)

    form_type = fields.Selection(
        [
            ("0", "Red"),
            ("1", "İptal")
        ],
        string="Form Type",
        required=True,
        default= lambda self: str(self._context.get("form_type")) if self._context.get("form_type") else "0",


    )






     #iptal sebebi
    name = fields.Selection(
        [
            ("yanlis", "Yanlış"),
            ("cozuldu", "Çözüldü"),
            ("diger", "Diğer")
        ],
        string="Reason",
        required=True,
        default="yanlis",
    )
    description = fields.Text(string="Description", required=True)

    @api.model_create_multi
    def create(self, vals_list):
        print("donduuuu 1")
        for vals in vals_list:
            ticket_id = int(self._context.get("active_id"))
            ticket = self.env["helpdesk.ticket"].browse(ticket_id)
            ticket.write({"stage_id": 5})
            # ticket.message_post(
            #     body="Talep iptal edildi. Sebep: %s" % vals["description"]
            # )
        return super(HelpdeskCancelReason, self).create(vals_list)




