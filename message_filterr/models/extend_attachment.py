from odoo import models, fields, api, _

class ExtendAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _get_file_size(self):
        for record in self:
            if record.type == 'url':
                record.file_size = 0
            else:
                record.file_size = len(record.datas)

    file_size = fields.Integer(compute='_get_file_size', string='File Size', store=True)