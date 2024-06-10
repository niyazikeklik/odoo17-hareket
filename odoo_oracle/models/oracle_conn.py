import cx_Oracle
from cx_Oracle import DatabaseError

from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools import config


class OracleConn(models.Model):
    _name = 'oracle.conn'
    _description = "Oracle Connection for Odoo"

    ifs_link = fields.Char("IFS Link")

    def init_oracle_client(self, company):
        if company.oracle_client_path:
            try:
                cx_Oracle.init_oracle_client(lib_dir=company.oracle_client_path)
            except Exception as e:
                print("Bağlantı hatası: ", e)

    def connect(self, company_id, uid):
        if uid:
            user = self.env["res.users"].browse(uid)
        else:
            user = self.env.user
        if company_id:
            company = self.env["res.company"].browse(company_id)
        else:
            company = user.company_id

        self.init_oracle_client(company)
        dsn_tns = cx_Oracle.makedsn(company.oracle_server,
                                    company.oracle_port if company.oracle_port else 1521,
                                    company.oracle_service_name)
        if (company.oracle_generic_username and company.oracle_generic_password) or (user.oracle_username and user.oracle_password):
            str="(DESCRIPTION = (ADDRESS = (PROTOCOL = TCP)(HOST = " + company.oracle_server + ")(PORT = " + (company.oracle_port if company.oracle_port else "1521") + ")) (CONNECT_DATA=(SERVICE_NAME = " + company.oracle_service_name + ")))"
            conn = cx_Oracle.connect(user=user.oracle_username if user.oracle_username and not company_id else company.oracle_generic_username,
                                     password=user.oracle_password if user.oracle_password and not company_id else company.oracle_generic_password,
                                     dsn = str)
        else:
            raise UserError("Oracle Kullanıcı adı / Şifre bilgileri Şirket ayarlarında veya kullanıcı ayarlarında girili olmalıdır.")
        return conn

    def simplify_error_message(self, msg):
        if self.user_has_groups('base.group_no_one'):
            return msg
        elif type(msg) == DatabaseError:
            finish_index = str(msg).find("\n")
            return str(msg)[0:finish_index]
        else:
            return msg


