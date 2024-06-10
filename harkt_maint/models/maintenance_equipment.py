
from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    plate = fields.Char("Plate")
    fleet_number = fields.Char("Fleet Number")

