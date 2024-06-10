import base64
from pathlib import Path

from odoo import models, fields, api
import json
from odoo.exceptions import UserError


class SasBaslik(models.Model):
    _name = 'sas.baslik'
    _description = "Satınalma Sipariş Başlığı"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "order_no"

    order_no = fields.Char("Sipariş No", required=True)
    vendor_no = fields.Char("Tedarikçi No", required=True)
    vendor_name = fields.Char("Tedarikçi Adı")
    site = fields.Char("Site")
    order_code = fields.Char("Sipariş Kodu") #sipairş kodu açıklması gelecek
    order_type = fields.Char("Sipariş Türü") # sipariş türü açıklaması gelecek
    delivery_date = fields.Date("Teslimat Tarihi")
    currency_code = fields.Char("Döviz")
    purchase_buyer = fields.Char("Satınalmacı") # satınalmacı adı
    coordinator = fields.Char("Koordinatör") #koordinator adı
    total_price = fields.Float("Toplam Tutar")
    gross_total_price = fields.Float("Toplam Tutar KDV Dahil")
    satir_ids = fields.One2many("sas.satir","baslik_id", "Satırlar")
    onay_ids = fields.One2many("sas.onay", "baslik_id", "Onaylar")
    doc_ids = fields.One2many("sas.dosya","baslik_id","Dosyalar")
    next_approver_id = fields.Many2one("res.users","Onayı Beklenen")
    can_approve = fields.Boolean("Onaylayabilir", compute="_compute_can_approve")
    active = fields.Boolean("Aktif", default=True)
    state = fields.Char("State")
    change_order_no= fields.Char("Değişim Emri No")
    sequence_no = fields.Integer("Sıra No")
    route =fields.Integer("Onay No")
    reject_reason = fields.Char("Red Sebebi")
    red_kodu_id = fields.Many2one("sas.red.kodu","Red Kodu")
    proje_no = fields.Char("Proje No")
    proje_adi = fields.Char("Proje Adı")
    notlar = fields.Char("Notlar")

    def _compute_can_approve(self):
        for rec in self:
            if self.env.user.id == rec.next_approver_id.id:
                self.can_approve = True
            else:
                self.can_approve = False

    def remove_sas(self):
        self.cancel_all_activities()
        self.env.cr.execute("delete from mail_activity where res_model = 'sas.baslik' and res_id="+str(self.id))
        try:
            self.env["ir.attachment"].search([("res_model","=","sas.baslik"),("res_id","=",self.id)]).unlink()
        except Exception as ex:
            print(ex)
        self.env.cr.execute("delete from sas_satir where baslik_id="+str(self.id))
        self.env.cr.execute("delete from sas_onay where baslik_id="+str(self.id))
        self.env.cr.execute("delete from sas_dosya where baslik_id="+str(self.id))
        self.env.cr.execute("delete from sas_baslik where id="+str(self.id))

    def check_from_ifs(self):
        conn = self.env["oracle.conn"].connect(False, False)
        try:
            c = conn.cursor()
            for rec in self:
                c.execute("begin ifsapp.odoo_portal_api.Portal_Send_Pur_Ord('"+rec.order_no+"',1); end;")
        except Exception as ex:
            print(ex)

    @api.model
    def create_or_write_all(self, data, check):
        results = self.env["sas.baslik"].search([("order_no","=", data["order_no"]),("active","in", [True,False])])
        for rec in results:
            rec.remove_sas()
            self.env.cr.commit()
        line_vals = data["satir_ids"]
        history_vals = data["onay_ids"]
        doc_vals = data["doc_ids"]
        data["satir_ids"] = False
        data["onay_ids"] = False
        data["doc_ids"] = False
        #if data["state"] not in("Planned","Released","Received") or len(history_vals) == 0:
        if data["state"] in ("Closed", "Stopped", "Cancelled") or len(history_vals) == 0:
            return True
        sas = super(SasBaslik,self).create(data)

        for satir in line_vals:
            satir["baslik_id"] = sas.id
            self.env["sas.satir"].create(satir)
        for doc in doc_vals:
            doc["baslik_id"] = sas.id
            self.env["sas.dosya"].create(doc)
        onaylayici = False
        sequence_no = 0
        route = 0
        change ="*"
        onay_atandi =False
        for onay in history_vals:
            onay["baslik_id"] = sas.id
            self.env["sas.onay"].create(onay)
            if not onay.get("approver_sign") and not onay.get("revoked_sign") and not onay_atandi:
                onay_atandi = True
                onaylayici = onay["authorize_id"]
                sequence_no = onay["sequence_no"]
                route = onay["route"]
                change = onay["change_order_no"]
        if sequence_no == 0:
            sas.remove_sas()
            return True
        sas.write({
            "sequence_no": sequence_no,
            "route": route,
            "change_order_no": change
        })
        emp = self.env["hr.employee"].search([("person_id", "=", onaylayici)])
        if len(emp) == 1:
            sas.write({
                "next_approver_id": emp.user_id.id
            })
        if check == 0:
            sas.create_activity()

        return sas

    def create_activity(self):
        for rec in self:
            note = rec.order_no + " numaralı satınalma siparişi onayınızı beklemektedir."
            rec.activity_schedule(
                "ifs_onay.mail_act_sas_onay",
                note=str(rec.id) + " nolu Satınalma siparişini onaylamanız beklenmektedir.",
                user_id=rec.next_approver_id.id)

    def cancel_all_activities(self):
        try:
            self.activity_unlink(["ifs_onay.mail_act_sas_onay"])
        except Exception as e:
            print(e)

    def action_confirm(self):
        if self.can_approve:
            conn = self.env["oracle.conn"].connect(False, False)
            try:
                c = conn.cursor()

                c.callproc("ifsapp.odoo_portal_api.approve_sas",
                           [self.order_no, self.change_order_no, self.sequence_no])
                conn.commit()
                action = self.env.ref("ifs_onay.sas_baslik_action").read()[0]
                res_action = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Başarılı',
                        'message': "Başarıyla Onaylandı",
                        'sticky': False,  # True/False will display for few seconds if false
                        'next': action,
                    }
                }
                return res_action
            except Exception as e:
                raise UserError(e)

    def action_reject(self, reject_reason, red_kodu_id):
        if self.can_approve:
            conn = self.env["oracle.conn"].connect(False, False)
            try:
                c = conn.cursor()
                c.callproc("ifsapp.odoo_portal_api.reject_sas",
                           [self.order_no, self.change_order_no, self.sequence_no, self.red_kodu_id.reject_code,
                            self.reject_reason])
                conn.commit()
                action = self.env.ref("ifs_onay.sas_baslik_action").read()[0]
                res_action = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Başarılı',
                        'message': "Başarıyla Reddedildi",
                        'sticky': False,  # True/False will display for few seconds if false
                        'next': action,
                    }
                }
                return res_action
            except Exception as e:
                raise UserError(e)

    def attach_ftp_files(self):
        ftp = self.env["sas.dosya"].ftp_connect()
        print("test1")
        for rec in self:
            print("test2")
            attach_count = 0

            #self.env["ir.attachment"].search([("res_model","=","sas.baslik"),("res_id","=",rec.id)]).unlink()
            attach_count =self.env["ir.attachment"].search_count([("res_model", "=", "sas.baslik"), ("res_id", "=", rec.id)])
            if attach_count == 0:
                for doc in rec.doc_ids:
                    print("test")
                    print(doc.path)
                    try:
                        ftp.cwd("/" + doc.path)
                        filename = doc.file_name
                        ftp.retrbinary('RETR %s' % filename, open("/mnt/ifs/" + filename, 'wb').write)
                        if filename[-3:].upper() == "XLS":
                            print("XLS")
                            filename = self.env["file.converter"].xls_to_xlsx("/mnt/ifs/" + filename)
                            print(filename)
                        data = Path("/mnt/ifs/" + filename).read_bytes()
                        if filename[-4:].upper() == "HTML":
                            mime_type= "text/html"
                        elif filename[-3:].upper() == "PDF":
                            mime_type = "application/pdf"
                        elif filename[-3:].upper() == "PNG":
                            mime_type = "image/png"
                        elif filename[-3:].upper() == "JPG" or filename[-4:].upper() == "JPEG":
                            mime_type = "image/jpeg"
                        elif filename[-3:].upper() == "BMP":
                            mime_type = "image/bmp"
                        elif filename[-4:].upper() == "XLSX" or filename[-4:].upper() == "XLSM":
                            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        elif filename[-3:].upper() == "XLS":
                            #mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            mime_type = "application/vnd.ms-excel"
                        elif filename[-4:].upper() == "DOCX":
                            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        elif filename[-3:].upper() == "MSG":
                            mime_type = "application/msword"
                        else:
                            mime_type="application/octet_stream"
                        """    
                        if filename[-4:].upper() == "HTML":
                            mime_type= "text/html"
                        elif filename[-3:].upper() == "PDF":
                            mime_type = "application/pdf"
                        elif filename[-3:].upper() == "PNG":
                            mime_type = "application/png"
                        elif filename[-3:].upper() == "JPG" or filename[-4:].upper() == "JPEG":
                            mime_type = "application/jpeg"
                        elif filename[-3:].upper() == "BMP":
                            mime_type = "application/bmp"
                        elif filename[-4:].upper() == "XLSX" or filename[-4:].upper() == "XLSM":
                            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        elif filename[-3:].upper() == "XLS":
                            mime_type = "application/vnd.ms-excel"
                        elif filename[-3:].upper() == "DOCX":
                            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        else:
                            mime_type="application/octet_stream"
                            """
                        vals = {
                            'res_model': 'sas.baslik',
                            'res_id': rec.id,
                            'datas': base64.b64encode(data),
                            'name': filename,
                            'mimetype': mime_type
                        }
                        self.env['ir.attachment'].create(vals)
                    except Exception as ex:
                        print(ex)
        ftp.close()