
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo import http, tools, _
from odoo.exceptions import UserError
from odoo.http import request


class AuthSignupHomee(AuthSignupHome):

    @http.route()
    def web_login(self, *args, **kw):
        response = super().web_login(*args, **kw)

        if request.params.get('login_success'):
            user_name = request.params.get('login')
            password = request.params.get('password')
            
            user = request.env['res.partner'].sudo().search([('email', '=', user_name)], limit=1)
            hr_employee = request.env['hr.employee'].sudo().search([('work_email', '=', user_name)], limit=1)
            is_mavi_yaka = request.env["tr.company"].is_mavi_yaka(hr_employee.emp_no) if hr_employee else False
            tc_no = request.env["tr.company"].get_person_tc_no(hr_employee.emp_no) if hr_employee else False
            if user and user.signup_token and password == tc_no and is_mavi_yaka:
                return request.redirect('/web/reset_password?db=%s&token=%s' % (request.db, user.signup_token))
            
        return response
    