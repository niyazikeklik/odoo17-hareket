
from odoo import fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    plate = fields.Char("Plate")
    fleet_number = fields.Char("Fleet Number")

    planned_lower_engine = fields.Char("Lower Engine(Planned)")
    planned_upper_engine = fields.Char("Upper Engine(Planned)")
    planned_km = fields.Integer("Km(Planned)")

    actual_lower_engine = fields.Char("Lower Engine(Actual)")
    actual_upper_engine = fields.Char("Upper Engine(Actual)")
    actual_km = fields.Integer("Km(Actual)")

    location = fields.Char("Location")
    project = fields.Char("Project")


