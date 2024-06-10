import datetime

import werkzeug.urls
from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
import requests
import json

GEOLOCATION = dp.get_precision("Gelocation")

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_latitude = fields.Float("Check-in Latitude", digits=GEOLOCATION, readonly=True)
    check_in_longitude = fields.Float("Check-in Longitude", digits=GEOLOCATION, readonly=True)
        
    check_out_latitude = fields.Float("Check-out Latitude", digits=GEOLOCATION, readonly=True)
    check_out_longitude = fields.Float("Check-out Longitude", digits=GEOLOCATION, readonly=True)
    
    check_in_location_link = fields.Char('Check In Location', compute='_compute_check_in_location_url')
    check_out_location_link = fields.Char('Check Out Location', compute='_compute_check_out_location_url')
    
    check_in_geofence_ids = fields.Many2many('hr.attendance.geofence', 'check_in_geofence_attendance_rel', 'attendance_id', 'geofence_id', string='Geofence Giriş')
    check_out_geofence_ids = fields.Many2many('hr.attendance.geofence', 'check_out_geofence_attendance_rel', 'attendance_id', 'geofence_id', string='Geofence Çıkış')
    
    check_in_photo = fields.Binary(string="Check In Photo", readonly=False)
    check_out_photo = fields.Binary(string="Check Out Photo", readonly=False)
    
    check_in_ipaddress = fields.Char(string="Check In IP", readonly=True)
    check_out_ipaddress = fields.Char(string="Check Out IP", readonly=True)
    
    check_in_work_type_id = fields.Many2one("hr.work.entry.type","Check In Work Type", store=True)
    check_out_work_type_id = fields.Many2one("hr.work.entry.type","Check Out Work Type", store=True)

    check_in_project_id =fields.Many2one("harkt.proje","Check In Project", store=True)
    check_out_project_id = fields.Many2one("harkt.proje","Check Out Project", store=True)

    check_in_work = fields.Char("Work To Do")
    check_out_work = fields.Char("Work Done")

    in_country_name = fields.Char(string="In Country", help="Based on coordinates", readonly=True, compute ="_compute_in_address", store=True)
    out_country_name = fields.Char(string="Out Country", help="Based on coordinates", readonly=True, compute ="_compute_out_address", store=True)

    in_city = fields.Char(string="In City", help="Based on coordinates", readonly=True, compute ="_compute_in_address", store=True)
    out_city = fields.Char(string="Out City", help="Based on coordinates", readonly=True, compute ="_compute_out_address", store=True)

    in_address = fields.Char(string="In Address", help="Based on coordinates", readonly=True, compute ="_compute_in_address", store=True)
    out_address = fields.Char(string="Out Address", help="Based on coordinates", readonly=True, compute ="_compute_out_address", store=True)

    work_entry_id = fields.Many2one("hr.work.entry", "Puantaj")
    #work_entry_id = fields.Integer("puantaj")

    @api.depends("check_in_latitude","check_in_longitude")
    def _compute_in_address(self):
        for rec in self:
            if rec.check_in_latitude == 0:
                rec.in_city = ""
                rec.in_address = ""
                rec.in_country_name = ""
            else:
                try:
                    url = """https://nominatim.openstreetmap.org/reverse.php?lat=""" + str(rec.check_out_latitude) + """&lon=""" + str(rec.check_out_longitude) + """&zoom=18&format=jsonv2"""
                    result = requests.get(url)
                    print(result.text)
                    location = json.loads(result.text)
                    rec.in_address = location.get("display_name")
                    try:
                        rec.in_country_name = location.get("address").get("country") or location.get("address").get("country")
                    except Exception as ex:
                        rec.in_country_name = ""
                        print(ex)
                    if rec.in_country_name == "Türkiye":
                        try:
                            rec.in_city = (location.get("address").get("province") or "") + "-" + (location.get("address").get("town") or "")
                        except Exception as ex:
                            rec.in_city = ""
                            print(ex)

                    try:
                        rec.in_city = location.get("address").get("state") or location.get("address").get("city") or location.get("address").get("province") or location.get("address").get("town")
                    except Exception as ex:
                        rec.in_city = ""
                        print(ex)
                    #rec.in_geofence_ids = self.env["hr.attendance.geofence"].get_goefence_ids_from_coordinates(rec.check_in_latitude, rec.check_in_longitude)
                except Exception as ex:
                    rec.out_city = ""
                    rec.out_country_name = ""
                    rec.out_address = ""

    @api.depends("check_out_latitude", "check_out_longitude")
    def _compute_out_address(self):
        for rec in self:
            if rec.check_out_latitude == 0:
                rec.out_city = ""
                rec.out_address = ""
                rec.out_country_name = ""
            else:
                #geolocator = Nominatim(user_agent="odooHareket")
                #location = geolocator.reverse((rec.check_out_latitude, rec.check_out_longitude))
                try:
                    url = """https://nominatim.openstreetmap.org/reverse.php?lat="""+str(rec.check_out_latitude)+"""&lon="""+str(rec.check_out_longitude)+"""&zoom=18&format=jsonv2"""
                    result = requests.get(url)
                    print(result.text)
                    location = json.loads(result.text)

                    rec.out_address = location.get("display_name")
                    try:
                        rec.out_country_name = location.get("address").get("country") or location.get("address").get(
                            "country")
                    except Exception as ex:
                        rec.out_country_name = ""
                        print(ex)
                    if rec.out_country_name == "Türkiye":
                        try:
                            rec.out_city = (location.get("address").get("province") or "") + "-" + (
                                        location.get("address").get("town") or "")
                        except Exception as ex:
                            rec.out_city = ""
                            print(ex)
                    try:
                        rec.out_city = location.get("address").get("state") or location.get("address").get(
                            "city") or location.get("address").get("province") or location.get("address").get("town")
                    except Exception as ex:
                        rec.out_city = ""
                        print(ex)
                except Exception as ex:
                    rec.out_city = ""
                    rec.out_country_name = ""
                    rec.out_address = ""
                #rec.out_geofence_ids = self.env["hr.attendance.geofence"].get_goefence_ids_from_coordinates(rec.check_out_latitude, rec.check_out_longitude)

    
    @api.depends('check_in_latitude','check_in_longitude')
    def _compute_check_in_location_url(self):
        for attendance in self:
            params = {
                'q': '%s,%s' % (attendance.check_in_latitude or '',attendance.check_in_longitude or ''),'z': 10,
            }
            attendance.check_in_location_link ='%s?%s' % ('https://maps.google.com/maps',werkzeug.urls.url_encode(params or None))

    @api.depends('check_out_latitude','check_out_longitude')
    def _compute_check_out_location_url(self):
        for attendance in self:
            params = {
                'q': '%s,%s' % (attendance.check_out_latitude or '',attendance.check_out_longitude or ''),'z': 10,
            }
            attendance.check_out_location_link = '%s?%s' % ('https://maps.google.com/maps',werkzeug.urls.url_encode(params or None))
            

    def attendance_to_work_entry(self):
        for rec in self:
            entry = self.env["hr.work.entry"].search([("employee_id", "=", rec.employee_id.id),
                ("date_start", ">=", datetime.datetime.combine(rec.check_in, datetime.time(0,0,0))),
                ("date_start", "<=", datetime.datetime.combine(rec.check_in, datetime.time(23,59,59)))],
                                             limit=1)

            if len(entry)==1:
                rec.work_entry_id = entry.id
                entry._compute_giris_cikis()

    def attendance_to_work_entry_for_emp(self,employee_id):
        for rec in self.env["hr.attendance"].search([("work_entry_id", "=", False), ("employee_id","=", employee_id)]):
            rec.attendance_to_work_entry()

    def action_details(self):
        return {
            "res_model": "hr.attendance",
            "type": "ir.actions.act_window",
            'view_type': "form",
            "view_mode": "form",
            "target": "current",
            "context": {},
            "res_id": self.id
        }
