from odoo import api, fields, models

class MessageFilter(models.Model):
    _name = "message.filter"
    _description = "Message Filter"

    name = fields.Char(string="Name", required=True)
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
    )
    baslangic = fields.Text(string="Başlangıç", required=True)
    bitis = fields.Text(string="Bitiş", required=True)
    replace_with = fields.Text(string="Bununla Değiştir")
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)