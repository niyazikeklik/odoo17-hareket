from odoo import fields, models
class EmployeeLeavesum(models.Model):
    _name = "tr.employee.leavesum"
    _description = "Çalışan Yıllık İzin Özeti"
    employee_id = fields.Many2one('hr.employee', 'Çalışan')
    year = fields.Char("Yıl")
    earned = fields.Float("Hakedilen")
    used = fields.Float("Kullanılan")
    rest = fields.Float("Kalan")