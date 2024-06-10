# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import random
from odoo import models
import xlsxwriter
import io
import base64

class TrCompany(models.Model):
    _inherit = "tr.company"

    def _hr_birthday_task(self):
        self._cr.execute("""update hr_employee set 
        birthday_flag=(CASE WHEN to_char(birthday,'dd.MM') = to_char(CURRENT_DATE,'dd.MM') then True Else False end)""")

    def _hr_departure_integration(self):
        for emp in self.env['hr.employee'].search([("tr_company_id", "!=", False), ("emp_no","!=", False) ]):
            query = """
            SELECT BITIS_TARIHI FROM TRBRD_PERSONEL_CALISMA_TAB WHERE COMPANY_ID = '"""+emp.tr_company_id.code+"""'
            AND EMP_NO = '"""+emp.emp_no+"""' ORDER BY SEQ_NO DESC
            """
            conn = self.env["oracle.conn"].connect(1, False)
            c = conn.cursor()
            c.execute(query)
            result = c.fetchall()
            if len(result)>0 and result[0][0]:
                emp.write({
                    "active":False,
                    "date_until":result[0][0],
                    "departure_date":result[0][0]
                })
                if emp.user_id:
                    emp.user_id.write(
                        {
                            'active': False
                        }
                    )
                    if emp.user_id.partner_id:
                        emp.user_id.partner_id.write(
                            {
                                'active': False
                            }
                        )

    def _create_user_name(self, name):
        name = name.replace("İ", "i")
        name = name.replace("Ö", "o")
        name = name.replace("Ü", "u")
        name = name.replace("Ğ", "g")
        name = name.replace("Ş", "s")
        name = name.replace("Ç", "c")
        name = name.lower()
        name = name.replace(" ", ".")
        name = name.replace("ı", "i")
        name = name.replace("ö", "o")
        name = name.replace("ü", "u")
        name = name.replace("ğ", "g")
        name = name.replace("ş", "s")
        name = name.replace("ç", "c")
        return name
    
    def remove_mavi_yaka_turkishchars_problem_users(self):
        problems_char = ["İ", "Ö", "Ü", "Ğ", "Ş", "Ç"]
        #get name includes problems char and mavi_Yaka user
        all_emps_exist_user  = self.env["hr.employee"].search([("user_id", "!=", False), ("emp_no", "!=", False)])
        for emp in all_emps_exist_user:
            if self.is_mavi_yaka(emp.emp_no) and emp.user_id:
                name = emp.name
                for char in problems_char:
                    if char in name:
                        emp.user_id.unlink()
                        break

    def _get_mavi_yaka_employees(self, company_id):
        sql = """   select emp_no from IFSAPP.COMPANY_PERSON_ALL cpa 
                    where cpa.company_id = '"""+company_id+"""'
                    and cpa.emp_cat_name  = 'MAVI_YAKA'
        """
        conn = self.env["oracle.conn"].connect(1, False)
        c = conn.cursor()
        c.execute(sql)
        ifs_mavi_yakalar = c.fetchall()
        return ifs_mavi_yakalar
    
    def get_personel_bolum_yonetici(self, emp_no, company_id):
        #IFSAPP.COMM_METHOD_API.Get_Default_Email(IFSAPP.HARKT_BT_UTIL_API.GET_PERSON_AMIR(cpa.EMP_NO, cpa.company_id)) YONETIICI_MAIL,
        #IFSAPP.COMPANY_ORG_API.Get_Org_Name(CPA.company_id, CPA.org_code) BOLUM
        sql = """   select 
                    IFSAPP.COMM_METHOD_API.Get_Default_Email(IFSAPP.HARKT_BT_UTIL_API.GET_PERSON_AMIR(cpa.EMP_NO, cpa.company_id)) YONETIICI_MAIL, 
                    IFSAPP.COMPANY_ORG_API.Get_Org_Name(CPA.company_id, CPA.org_code) BOLUM
                    from IFSAPP.COMPANY_PERSON_ALL cpa 
                    where cpa.emp_no = '"""+emp_no+"""'
                    and cpa.company_id = '"""+company_id+"""'
                    and rownum = 1
        """
        conn = self.env["oracle.conn"].connect(1, False)
        c = conn.cursor()
        c.execute(sql)
        personel_bolum_yonetici = c.fetchall()
        if len(personel_bolum_yonetici) > 0:
            return personel_bolum_yonetici[0]
        else:
            return ("", "")

    def is_mavi_yaka(self, emp_no):

        if emp_no == False or emp_no == None or emp_no == "" or emp_no == "0":
            return False
        

        sql = """   select emp_no from IFSAPP.COMPANY_PERSON_ALL cpa 
                    where cpa.emp_no = '"""+emp_no+"""'
                    and cpa.emp_cat_name  = 'MAVI_YAKA'
                    and rownum = 1
        """
        conn = self.env["oracle.conn"].connect(1, False)
        c = conn.cursor()
        c.execute(sql)
        ifs_mavi_yakalar = c.fetchall()
        if len(ifs_mavi_yakalar) > 0:
            return True
        else:
            return False
    
    def get_person_tc_no(self, emp_no):
        if emp_no:
            sql = "select TC_KIMLIK_NO from TRBRD_KIMLIK_BILGILERI where PERSON_ID = '" + emp_no + "'"
            conn = self.env["oracle.conn"].connect(1, False)
            c = conn.cursor()
            c.execute(sql)
            tc_no = c.fetchall()
            if len(tc_no) > 0:
                return tc_no[0][0]
            else:
                return ""
        else:
            return ""
        
    def _create_token(self):
        alfanumeric = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        token = ""
        bitt = 64
        for i in range(bitt):
            token += alfanumeric[random.randint(0, len(alfanumeric) - 1)]
        return token
    
    def create_sign_up_token_for_all_mavi_yaka_users(self):
        try:
            all_emps = self.env["hr.employee"].search([("user_id", "!=", False), ("emp_no", "!=", False)])
            for emp in all_emps:
                if self.is_mavi_yaka(emp.emp_no):
                    self.create_sign_token_for_user(emp)
        except Exception as ex:
            #send mail
            mail = self.env['mail.mail']
            #send ex to mail
            mail.create({
                'subject': 'Hata odoo',
                'email_from': 'odoo.hareket@hotmail.com',
                'email_to': 'niyazi.keklik@hareket.com',
                'body_html': "Hata oluştu: " + str(ex),
            }).send()
            print(ex)
        

                
    def change_all_mavi_yaka_users_password_to_tc(self):
        try:
            all_emps_exist_user  = self.env["hr.employee"].search([("user_id", "!=", False), ("emp_no", "!=", False)])
            for emp in all_emps_exist_user:
                if self.is_mavi_yaka(emp.emp_no) and emp.user_id:
                    tc_no = self.get_person_tc_no(emp.emp_no)
                    if tc_no:
                        emp.user_id.write({
                            "password": tc_no
                        })
        except Exception as ex:
            #send mail
            mail = self.env['mail.mail']
            #send ex to mail
            mail.create({
                'subject': 'Hata odoo',
                'email_from': 'odoo.hareket@hotmail.com',
                'email_to': 'niyazi.keklik@hareket.com',
                'body_html': "Hata oluştu: " + str(ex),
            }).send()
            print(ex)
            
                
            
        
    

        
    def create_sign_token_for_user(self, emp):
        user = emp.user_id
        res_partner = user.partner_id
        res_partner.write({
            "email": user.login,
            "signup_token": self._create_token(),
            "signup_type": "reset",
            "signup_expiration": datetime.datetime.now() + datetime.timedelta(days=1000),
        })
        self.env.cr.commit()
        print("Token oluşturuldu " + user.login)

    def _create_user_for_employee(self, company_id):
        emplooys_with_no_user = self.env["hr.employee"].search([("user_id", "=", False)])
        ifs_mavi_yakalar = self._get_mavi_yaka_employees(company_id)

        mavi_yakalar_without_user = emplooys_with_no_user.filtered(
            lambda emp: (emp.emp_no,) in ifs_mavi_yakalar 
        )
        beyaz_yakalar_without_user = emplooys_with_no_user - mavi_yakalar_without_user
        export_vals = []
        for emp in mavi_yakalar_without_user:
            #get emp sicil_No
            user_name = self._create_user_name(emp.name)
            start_with_user_name_count = self.env['res.users'].search_count([("login", "like", user_name + "%")]) 
            if start_with_user_name_count > 0: 
                user_name = user_name + str(start_with_user_name_count + 1)
            password = self.get_person_tc_no(emp.emp_no)
            if not password:
                password = user_name
            user_vals = {
                'name': emp.name,
                'login': user_name,
                'active': True,
                'password': password,
                'notification_type': 'inbox',
                'company_id': emp.company_id.id,
                'oracle_username': "ODOO",
                "oracle_password": "ODOO.123"
            }
            export_vals.append({
                "user_vals": user_vals,
                "emp": emp
            })
            pasif_emp = self.env["hr.employee"].search([("emp_no","=",emp.emp_no),("active","=",False)])
            if len(pasif_emp) > 0:
                pasif_emp = pasif_emp[0]
                pasif_user_id = pasif_emp.user_id
                pasif_emp.write({
                    "user_id": False,
                })
                emp.write({
                    "user_id": pasif_user_id.id
                })
                pasif_user_id.write({
                    "active": True,
                    "password": password
                })
                emp.user_id = pasif_user_id
                #self.create_sign_token_for_user(emp)
                print(emp.name +  " için kullanıcı aktifleştirildi login: " + user_name)
            else:
                SudoUser = self.env['res.users'].sudo();
                user = SudoUser.create(user_vals)
                self.env.cr.commit()
                emp.write({
                    "user_id": user.id
                })
                self.env.cr.commit()
                emp.user_id = user
                self.create_sign_token_for_user(emp)
                print(emp.name +  " için kullanıcı oluşturuldu login: " + user_name)
        #convert to excel file export_vals
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})
        worksheet.write('A1', 'Name', bold)
        worksheet.write('B1', 'Login', bold)
        worksheet.write('C1', 'Active', bold)
        worksheet.write('D1', 'Password', bold)
        worksheet.write('E1', 'Employee No', bold)
        worksheet.write('F1', 'Tur', bold)
        worksheet.write('G1', 'Bolum/Yonetici', bold)

        row = 1
        col = 0
        for user_obj in export_vals:
            worksheet.write(row, col, user_obj["user_vals"]['name'])
            worksheet.write(row, col + 1, user_obj["user_vals"]['login'])
            worksheet.write(row, col + 2, user_obj["user_vals"]['active'])
            worksheet.write(row, col + 3, user_obj["user_vals"]['password'])
            worksheet.write(row, col + 4, user_obj["emp"]["emp_no"])
            worksheet.write(row, col + 5, 'MAVI_YAKA')
            row += 1

        for beyaz_yaka in beyaz_yakalar_without_user:
            worksheet.write(row, col, beyaz_yaka['name'])
            worksheet.write(row, col + 1, '')
            worksheet.write(row, col + 2, '')
            worksheet.write(row, col + 3, '')
            worksheet.write(row, col + 4, beyaz_yaka["emp_no"])
            worksheet.write(row, col + 5, 'BEYAZ_YAKA (Kontrol edilmeli)')
            row += 1
        
        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()
        file_name = "Kullanıcılar.xlsx"

        #send mail
        mail = self.env['mail.mail']
        mail.create({
            'subject': 'Kullanıcılar',
            'email_from': 'odoo.hareket@hotmail.com',
            'email_to': 'niyazi.keklik@hareket.com',
            'body_html': 'Kullanıcılar ektedir',
            'attachment_ids': [(0, 0, {
                'name': file_name,
                'datas': base64.b64encode(file_data),
                'res_model': 'res.users',
            })]
        }).send()

        print("Kullanıcı oluşturma işlemi tamamlandı")
    
    def _user_and_employee_integration(self, company_code, emp_no):
        if not company_code:
            code = '%'
        else:
            code = company_code
        basestring = str
        query = """select distinct pc.company, pc.emp_no, pc.adi_soyadi from trbrd_personel_calisma_2 pc where 
                pc.bitis_tarihi is null  and pc.company like '"""+company_code+"""' and pc.emp_no like '"""+emp_no+"""'"""
        conn = self.env["oracle.conn"].connect(1, False)
        c = conn.cursor()
        c.execute(query)
        emps = c.fetchall()
        for emp in emps:
            print(emp)
            tr_company = self.env["tr.company"].search([("code", "=", emp[0])])
            found_emp = self.env["hr.employee"].search([("tr_company_id", "=", tr_company.id), ("emp_no", "=", emp[1])])
            if len(found_emp) == 0:
                self.env["hr.employee"].create({
                    "tr_company_id": tr_company.id,
                    "emp_no": emp[1],
                    "name": emp[2]
                })
                found_emp = self.env["hr.employee"].search(
                    [("tr_company_id", "=", tr_company.id), ("emp_no", "=", emp[1])])
            found_emp = found_emp[0]
            found_emp.get_emp_detail_from_ifs()
            found_emp.get_emp_annual_leave_from_ifs()
            found_emp = self.env["hr.employee"].search([("tr_company_id", "=", tr_company.id), ("emp_no", "=", emp[1])])[0]
            if found_emp.work_email:
                Ldap = self.env['res.company.ldap']
                found = False
                for conf in Ldap._get_ldap_dicts():
                    if not found:
                        login = found_emp.work_email[0:found_emp.work_email.find('@')]
                        dn, entry = Ldap._get_entry(conf, login)
                        conn = Ldap._connect(conf)
                        if entry:
                            try:
                                user = Ldap._get_or_create_user(conf, login, entry)
                                found_emp.associate_with_user(user)
                            except Exception as ex:
                                print(ex)
                                print(found_emp.name + " kişisi için kullanıcı oluşturulurken hata oluştu")
                            found = True
                        else:
                            print(found_emp.name + " için kullanıcı oluşturulamadı")