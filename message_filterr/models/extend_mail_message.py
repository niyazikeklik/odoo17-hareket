
from odoo import api, fields, models

class ExtendMailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("body"):
                vals["body"] = self.env["message.filter.helper"].get_cleaned_text(vals["body"], vals["model"])
        return super(ExtendMailMessage, self).create(vals_list)
    
    
    

    


