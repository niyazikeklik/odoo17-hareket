from odoo import models, fields, api

class HrDepartment(models.Model):
    _inherit = 'hr.department'
    code = fields.Char("Dept Code")

    def get_departments_from_ifs(self):
        conn = self.env["oracle.conn"].connect(False, False)
        c = conn.cursor()
        query = """SELECT org_code, min(org_name), o.sup_org_code,
        min(COMPANY_ORG_API.Get_Org_Name(O.company_id,O.sup_org_code)) UST_DEPARTMAN
         FROM company_org o where org_code not in('000','MATRIX')
         group by org_code, sup_org_code
        order by length(org_code), org_code"""
        result = c.execute(query)
        for rec in result:
            self.env["hr.department"].create({
                "code": rec[0],
                "name": rec[1],
                "parent_id": self.env["hr.department"].search([("code","=",rec[2])]).id
            })