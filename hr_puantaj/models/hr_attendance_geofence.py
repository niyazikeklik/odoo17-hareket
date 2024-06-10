import json

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.tools import safe_eval
from shapely.geometry import Polygon, Point


class HrAttendanceGeofence(models.Model):
    _name = "hr.attendance.geofence"
    _description = "Attendance Geofence"
    _order = "id desc"
    
    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda s: s.env.company.id, index=True)
    employee_ids = fields.Many2many('hr.employee', 'employee_geofence_rel', 'geofence_id', 'emp_id', string='Employees')
    overlay_paths = fields.Text(string='Paths')
    project_id = fields.Many2one("harkt.proje", "Proje")

    def is_inside(self, latitude, longtitude):
        coords = json.loads(self.overlay_paths).get("features")[0].get("geometry").get("coordinates")[0]
        geodata = []
        for rec in coords:
            geodata.append(tuple(rec))
        geofence = Polygon(geodata)

        return geofence.contains(Point(latitude, longtitude))

    def get_goefence_ids_from_coordinates(self, latitude, longtitude):
        result = []
        for rec in self.env["hr.attendance.geofence"].search([]):
            if rec.is_inside(latitude, longtitude):
                result.append(rec.id)
        #return self.env["hr.attendance.geofence"].search([("id", "in", result)])
        return result
