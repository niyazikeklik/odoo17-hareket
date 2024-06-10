from dateutil.rrule import rrule, DAILY

from datetime import  datetime, date, time
from pytz import  UTC
from odoo import models, fields, api
ROUNDING_FACTOR = 16

EMP_QUERY = """
select
                   ce.employee_id emp_no,
                   PERS_ADDRESS_API.Get_Address(ce.person_id, nvl(person_info_address_api.Get_Default_Address(ce.person_id, Address_Type_Code_Api.Get_Client_Value(4)),'01')) adres,
                   comm_method_api.Get_Value('PERSON', ce.person_id, 'MOBILE') telefon,
                   comm_method_api.Get_Value('PERSON', ce.person_id,'E_MAIL') email,
                   pi.name,
                   pc.ihbara_esas_tarihi ise_giris_tarihi,
                   pc.baslama_tarihi isyeri_baslangic_tarihi,
                   company_org_api.Get_Org_Name(ce.company, company_pers_assign_api.Get_Org_Code(ce.company, ce.employee_id, trunc(sysdate))) departman,
                   company_position_api.Get_Position_Title(ce.company, company_pers_assign_api.Get_Pos_Code(ce.company, ce.employee_id, trunc(sysdate))) pozisyon,
                   kb.tc_kimlik_no,
                   kb.baba_adi,
                   kb.ana_adi,
                   p.place_of_birth dogum_yeri,
                   p.date_of_birth dogum_tarihi,
                   decode(nvl(p.Gender_Id, 0), 1, 'male', 2, 'female', 'other') cinsiyet,
                   blood_type_api.Decode(p.blood_type) kan_grubu, 
                   pc.isyeri_kodu, 
                   trbrd_isyeri_api.Get_Unvan(pc.company_id,pc.isyeri_kodu) isyeri_unvani, 
                   case when (select count(1) from code_b b where b.company = pc.company_id and b.code_b = '100') = 0 THEN
                     trbrd_personel_sicil_api.get_code_i(pc.company, pc.emp_no, pc.seq_no, trbrd_personel_calisma_api.get_aktif_satir_no(pc.company, pc.emp_no, pc.seq_no))
                   else
                     trbrd_personel_sicil_api.get_code_b(pc.company, pc.emp_no, pc.seq_no, trbrd_personel_calisma_api.get_aktif_satir_no(pc.company, pc.emp_no, pc.seq_no))
                   END dept, 
                   nvl(PERS_ADDRESS_API.Get_Address1(ce.person_id),'*') adres1,
                   nvl(PERS_ADDRESS_API.Get_Address2(ce.person_id),'*') adres2, 
                   db.data, 
                   trbrd_personel_banka_api.Get_Iban(pc.company_id, pc.emp_no,pc.seq_no,trbrd_personel_banka_api.Get_Birincil_Sira_No(pc.company_id, pc.emp_no,pc.seq_no)) iban_no, 
                   trbrd_personel_calisma_api.Get_Banka_Kodu(pc.company_id, pc.emp_no,pc.seq_no) banka_kodu, 
                   pi.person_id,
                   ce.company,
                   odoo_portal_api.get_emp_org_code(pc.company_id, pc.emp_no),
                   odoo_portal_api.get_sup_emp_no(pc.company_id, pc.emp_no),
                   (select Company_Emp_Category_API.Decode(company_id,emp_cat_id)  from company_person_tab t where t.emp_no = pc.emp_no and t.company_id = ce.company) emp_cat_name
              from company_emp_tab            ce,
                   person_info_tab            pi,
                   trbrd_kimlik_bilgileri_tab kb,
                   pers_tab                   p,
                   trbrd_personel_calisma_2 pc,
                   binary_object_data_block_tab db
             where
               p.person_id = pi.person_id
               and pi.person_id = ce.person_id
               and pi.person_id = kb.person_id
               AND pc.company_id = ce.company
               and pc.emp_no = ce.employee_id
               and pc.seq_no = trbrd_personel_calisma_api.Get_Aktif_Seq_No(pc.company_id, pc.emp_no)
               AND pc.bitis_tarihi is null 
               AND db.blob_id(+) = pi.picture_id
"""

class HrEmployeePrivate(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'
    date_from = fields.Date(string="İşe Giriş Tarihi")
    start_date_on_workplace = fields.Date(string="İşyeri Başlangıç Tarihi")
    date_until = fields.Date(string="İşten Çıkış Tarihi")
    emp_no = fields.Char(string="Sicil No")

    allocated_leave_days = fields.Float(string="Toplam İzin Hakedişi")
    used_leave_days = fields.Float(string="Kullanılan İzin")
    rest_leave_days = fields.Float(string="Kalan İzin")
    leave_allocation_date = fields.Date(string="İzin Hakedeceği Tarih")
    annual_leave_summaries = fields.One2many('tr.employee.leavesum', 'employee_id', string='Yıllık İzin Özeti')
    tr_company_id = fields.Many2one("tr.company", string="Grup Şirketi")
    person_id = fields.Char("IFS Kişi ID")
    acc_emp_no = fields.Char("Muhasebe Sicil No")
    birthday_flag = fields.Boolean("Doğumgünü")
    emp_cat = fields.Selection([('MAVI_YAKA', 'Mavi Yaka'), ('BEYAZ_YAKA', 'Beyaz Yaka')], string="Çalışan Türü")


    @api.model
    def get_dept_employee(self):
        cr = self._cr
        cr.execute("""select department_id, hr_department.name,count(*) 
        from hr_employee join hr_department on hr_department.id=hr_employee.department_id 
        group by hr_employee.department_id,hr_department.name""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][1], 'value': dat[i][2]})
        return data

    def associate_with_user(self, user_id):
        print(user_id)
        existing = self.env["hr.employee"].search([("user_id", "=", user_id), ("id","!=", self.id)])
        print(existing)
        print(self)
        if len(existing)>0:
            existing.write({"user_id":False})
            self.env.cr.commit()
        self.write({
            "user_id": user_id
        })
        self.env.cr.commit()
        user = self.env["res.users"].browse(user_id)
        print(user)
        """if user.company_id.id != self.company_id.id:
            user.write({
                "company_id": self.company_id.id,
                "company_ids": [(6, 0, [self.company_id.id])]
            })"""

    def get_emp_detail_from_ifs(self):
        if not self.tr_company_id:
            return False
            #raise UserError("Entegrasyon için kullanıcının şirketi girilmiş olmalıdır.")
        if self.emp_no:
            query = EMP_QUERY + """ 
                    and pc.emp_no = '""" + self.emp_no + """'
                    and ce.company = '""" + self.tr_company_id.code + """'"""
        elif self.work_email:
            query = EMP_QUERY + """ 
            and comm_method_api.Get_Value('PERSON', ce.person_id,'E_MAIL') = '"""+self.work_email+"""'
            and ce.company = '"""+self.tr_company_id.code+"""'"""
        elif self.identification_id:
            query = EMP_QUERY + """ 
            and kb.tc_kimlik_no = '""" + self.identification_id + """'
            and ce.company = '""" + self.tr_company_id.code + """'"""
        else:
            query=False
            return False
            #raise UserError("Entegrasyon için kullanıcının iş e-postası, sicil numarası veya tc kimlik numarası girilmiş olmalıdır.")
        conn = self.env["oracle.conn"].connect(False, False)
        c = conn.cursor()
        c.execute(query)
        result = c.fetchall()
        
        if len(result) == 0:
            return False
        
        tr_company=self.env["tr.company"].search([("code", "=", result[0][25])])[0]
        dept = self.env["hr.department"].search([("code","=",result[0][26])])
        parent = self.env["hr.employee"].search([("emp_no","=", result[0][27])])

        self.write({
            'active': True,
            'work_email': result[0][3],
            'job_title': result[0][8],
            'place_of_birth': result[0][12],
            'birthday': result[0][13],
            'gender': result[0][14],
            'mobile_phone': result[0][2],
            'company_id': self.env.user.company_id,
            'tr_company_id': tr_company.id,
            # 'work_location_id': work_location_id,
            'identification_id': result[0][9],
            'private_email': result[0][3],
            'date_from': result[0][5],
            'start_date_on_workplace': result[0][6],
            'emp_no': result[0][0],
            'acc_emp_no': 'P' + result[0][25] + result[0][0],
            'person_id': result[0][24],
            "image_1920" : result[0][21],
            "department_id": dept.id if len(dept)==1 else False,
            "parent_id": parent.id if len(parent)==1 else False,
            "coach_id": parent.id if len(parent)==1 else False,
            "emp_cat": result[0][28],
            "resource_calendar_id": self.env["resource.calendar"].search([("name","=","HAR1")]).id
                                    if result[0][28] == 'BEYAZ_YAKA'
                                    else self.env["resource.calendar"].search([("name","=","HAR2")]).id
        })

        self.work_contact_id.write({
            'email': result[0][3],
            'email_normalized': result[0][3],
            'lang': 'tr_TR',
            'tz': 'Turkey',
            'street': result[0][1],
            'street2': result[0][1],
            'mobile': result[0][2],
            'function': result[0][8],
            'vat': result[0][9],
        })

        if result[0][22] and result[0][23] and self.work_contact_id and len(result[0][22])>2:
            bank_account = self.env['res.partner.bank'].search([('acc_number', '=', result[0][22]),
                                                                ('partner_id', '=', self.work_contact_id.id),
                                                                ('company_id', '=', self.company_id.id) ])
            banks = self.env['res.bank'].search([('bic', '=', result[0][23])])
            if not bank_account and banks:
                self._cr.execute("delete from res_partner_bank where partner_id = %s", (self.work_contact_id.id,))
                bank_account = self.env['res.partner.bank'].create({
                    'acc_number': result[0][22],
                    'partner_id': self.work_contact_id.id,
                    'company_id': self.company_id.id,
                    'bank_id': banks[0].id
                })
                self.write({
                    'bank_account_id': bank_account.id
                })

        if result[0][5]:
            old_contact = self.env["hr.contract"].search([("employee_id","=",self.id),("date_start","!=",result[0][5]),("state","=","open")])
            new_contact = self.env["hr.contract"].search([("employee_id", "=", self.id), ("date_start", "=", result[0][5])])
            if len(old_contact) > 0:
                for c in old_contact:
                    c.write({
                        "state":"closed",
                        "date_end": datetime.today()
                    })
            if len(new_contact)==0:
                self.env["hr.contract"].create({
                    "name": self.emp_no,
                    "employee_id": self.id,
                    "date_start": result[0][5],
                    "date_end": False,
                    "wage": 0,
                    "state": "open"
                })


    def get_emp_annual_leave_from_ifs(self):
        if not self.emp_no or not self.tr_company_id:
            return
        self._cr.execute("delete from tr_employee_leavesum where employee_id = %s", (self.id,))
        query = """SELECT
        IZIN_HAKEDIS_TARIHI, 
        TOPLAM_HAKETTIGI_IZIN, 
        TOPLAM_KULLANDIGI_IZIN, 
        KALAN_IZIN FROM TRIFM_IZINLER4 
        WHERE RAPOR_TARIHI = TRUNC(SYSDATE) 
        AND COMPANY_ID = '"""+self.tr_company_id.code+"""'
        AND EMP_NO = '"""+self.emp_no+"""'"""
        conn = self.env["oracle.conn"].connect(False, False)
        c = conn.cursor()
        c.execute(query)

        result = c.fetchall()
        if len(result) == 1:
            self.write({
                'leave_allocation_date': result[0][0],
                'allocated_leave_days': result[0][1],
                'used_leave_days': result[0][2],
                'rest_leave_days': result[0][3]
            })
        query = """SELECT yil, hak_gun, kullandigi, hak_gun+kullandigi kalan from trifm_izinler3
                WHERE RAPOR_TARIHI = TRUNC(SYSDATE) 
                AND COMPANY_ID = '""" + self.tr_company_id.code + """'
                AND EMP_NO = '""" + self.emp_no + """'"""
        c.execute(query)
        result = c.fetchall()
        for rec in result:
            self.env['tr.employee.leavesum'].create(
                {
                    'employee_id': self.id,
                    'year': rec[0],
                    'earned': rec[1],
                    'used': rec[2],
                    'rest': rec[3]
                })

    def _user_and_employee_integration(self):
        for rec in self:
            self.env["tr.company"]._user_and_employee_integration(rec.tr_company_id.code, rec.emp_no)

    def _user_and_employee_integration2(self):
        self.get_emp_detail_from_ifs()
        self.get_emp_annual_leave_from_ifs()
        Ldap = self.env['res.company.ldap']
        found = False
        for conf in Ldap._get_ldap_dicts():
            if not found:
                login = self.work_email[0:self.work_email.find('@')]
                dn, entry = Ldap._get_entry(conf, login)
                conn = Ldap._connect(conf)
                if entry:
                    try:
                        user = Ldap._get_or_create_user(conf, login, entry)
                        self.associate_with_user(user)
                    except:
                        print(self.name + " kişisi için kullanıcı oluşturulurken hata oluştu")
                        print(self.work_email + " kişisi için kullanıcı oluşturulurken hata oluştu")
                    found = True
                else:
                    print(self.name + " için kullanıcı oluşturulamadı")
                    print(self.work_email + " için kullanıcı oluşturulamadı")

    @api.model
    def _get_unusual_days(self, date_from, date_to=None):
        # Checking the calendar directly allows to not grey out the leaves taken
        # by the employee
        calendar = self.env.user.employee_id.resource_calendar_id
        if not calendar:
            return {}
        dfrom = datetime.combine(fields.Date.from_string(date_from), time.min).replace(tzinfo=UTC)
        dto = datetime.combine(fields.Date.from_string(date_to), time.max).replace(tzinfo=UTC)

        works = {d[0].date() for d in calendar._work_intervals_batch(dfrom, dto)[False]}
        return {fields.Date.to_string(day.date()): (day.date() not in works) for day in rrule(DAILY, dfrom, until=dto)}

class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    @api.depends('department_id')
    def _compute_parent_id(self):
        for employee in self.filtered('department_id.manager_id'):
            if not employee.parent_id and employee.department_id.manager_id:
                employee.parent_id = employee.department_id.manager_id


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"
    emp_no = fields.Char('Sicil No')
    tr_company_id = fields.Many2one("tr.company", string="Grup Şirketi")
    bank_account_id = fields.Many2one(
        'res.partner.bank', 'Bank Account Number',
        domain="[('partner_id', '=', work_contact_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        groups="hr.group_hr_user",
        tracking=True,
        help='Employee bank salary account')
    birthday = fields.Date('Doğum Tarihi',tracking=True)
    birthday_this_year=fields.Date("Doğum Günü", compute = "_compute_birthday_this_year")
    birthday_color = fields.Integer("Doğumgünü Rengi", compute="_compute_birthday_color")
    emp_cat = fields.Selection([('MAVI_YAKA', 'Mavi Yaka'), ('BEYAZ_YAKA', 'Beyaz Yaka')], string="Çalışan Türü")

    def _compute_birthday_this_year(self):
        for rec in self:
            if rec.birthday:
                rec.birthday_this_year = date(year = date.today().year, month=rec.birthday.month, day = rec.birthday.day )
            else:
                rec.birthday_this_year = date(year=date.today().year+1, month=1, day=1)


    def _compute_birthday_color(self):
        for rec in self:
            if rec.birthday:
                rec.birthday_color = rec.department_id.id%10
            else:
                rec.birthday_color = 1

    date_from = fields.Date(string="İşe Giriş Tarihi")
    start_date_on_workplace = fields.Date(string="İşyeri Başlangıç Tarihi")
    date_until = fields.Date(string="İşten Çıkış Tarihi")
    emp_no = fields.Char(string="Sicil No")
    allocated_leave_days = fields.Float(string="Toplam İzin Hakedişi")
    used_leave_days = fields.Float(string="Kullanılan İzin")
    rest_leave_days = fields.Float(string="Kalan İzin")
    leave_allocation_date = fields.Date(string="İzin Hakedeceği Tarih")
    annual_leave_summaries = fields.One2many('tr.employee.leavesum', 'employee_id', string='Yıllık İzin Özeti')
    person_id = fields.Char("IFS Kişi ID")
    acc_emp_no = fields.Char(string="Muhasebe Sicil No")
    private_email = fields.Char(related='work_contact_id.email', string="Private Email")
    birthday_flag = fields.Boolean("Doğumgünü")
