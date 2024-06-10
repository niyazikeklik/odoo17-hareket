from pathlib import Path

from odoo import models, fields, api
import base64

from odoo.exceptions import UserError

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def unlink(self):
        if len(self)>1:
            return super(IrAttachment, self).unlink()
        else:
            key = False
            if self.res_model == "harkt.masraf":
                lu_name = 'HarktMasrafGiris'
                ms = self.env["harkt.masraf"].sudo().search([("id", "=", self.res_id)])
                key = """MASRAF_NO=""" + ms.masraf_no + """^"""
            elif self.res_model == "harkt.para.talep":
                lu_name = 'HarktParaTalep'
                pt = self.env["harkt.para.talep"].sudo().search([("id", "=", self.res_id)])
                key = """TALEP_NO=""" + pt.talep_no + """^"""
            if key:
                conn = self.env["oracle.conn"].connect(1, False)

                try:
                    c = conn.cursor()
                    c.execute("""
                                declare
                                   doc_no_    varchar2(2000);
                                   doc_sheet_ varchar2(2000);
                                   doc_rev_   varchar2(2000);
                                   file_name_ varchar2(2000);
                                begin
                                   odoo_portal_api.Dokuman_Sil(:NAME,:LU_NAME, :KEY);
                                end;""",
                              NAME= self.name[0:self.name.rfind(".")],
                              LU_NAME = lu_name,
                              KEY = key)
                    conn.commit()
                except Exception as ex:
                    conn.rollback()
                    raise UserError(ex)
            return super(IrAttachment, self).unlink()
    @api.model
    def create(self, vals):
        ret = super(IrAttachment, self).create(vals)
        if vals.get("res_model") == "harkt.masraf":
            ms = self.env["harkt.masraf"].sudo().search([("id", "=", vals.get("res_id"))])

            conn = self.env["oracle.conn"].connect(1, False)
            dosya_adi = vals.get("name")
            name = dosya_adi[0:dosya_adi.rfind(".")]
            ext = dosya_adi[dosya_adi.rfind(".") + 1:]
            try:
                c = conn.cursor()
                doc_no = c.var(str)
                doc_sheet = c.var(str)
                doc_rev = c.var(str)
                file_name = c.var(str)
                c.execute("""
                    declare
                       doc_no_    varchar2(2000);
                       doc_sheet_ varchar2(2000);
                       doc_rev_   varchar2(2000);
                       file_name_ varchar2(2000);
                       lu_name_   varchar2(50) := 'HarktMasrafGiris';
                       key_       varchar2(50) := 'MASRAF_NO="""+ms.masraf_no+"""^';
                    begin
                       odoo_portal_api.Dokuman_Ekle(:NAME,:DOC_NO,:DOC_SHEET,:DOC_REV,:FILE_NAME,:EXT,lu_name_, key_);
                    end;""",
                          NAME = name,
                          EXT = ext,
                          DOC_NO = doc_no,
                          DOC_SHEET = doc_sheet,
                          DOC_REV = doc_rev,
                          FILE_NAME = file_name)
                self.send_to_ftp(file_name.getvalue(), vals.get("raw"), ret.id)
                conn.commit()
            except Exception as ex:
                conn.rollback()
                raise UserError(ex)
        elif vals.get("res.model") == "harkt.para.talebi":
            pt = self.env["harkt.para.talep"].sudo().search([("id", "=", vals.get("res_id"))])

            conn = self.env["oracle.conn"].connect(1, False)
            dosya_adi = vals.get("name")
            name = dosya_adi[0:dosya_adi.rfind(".")]
            ext = dosya_adi[dosya_adi.rfind(".") + 1:]
            try:
                c = conn.cursor()
                doc_no = c.var(str)
                doc_sheet = c.var(str)
                doc_rev = c.var(str)
                file_name = c.var(str)
                c.execute("""
                                declare
                                   doc_no_    varchar2(2000);
                                   doc_sheet_ varchar2(2000);
                                   doc_rev_   varchar2(2000);
                                   file_name_ varchar2(2000);
                                   lu_name_   varchar2(50) := 'HarktParaTalep';
                                   key_       varchar2(50) := 'TALEP_NO=""" + pt.talep_no + """^';
                                begin
                                   odoo_portal_api.Dokuman_Ekle(:NAME,:DOC_NO,:DOC_SHEET,:DOC_REV,:FILE_NAME,:EXT,lu_name_, key_);
                                end;""",
                          NAME=name,
                          EXT=ext,
                          DOC_NO=doc_no,
                          DOC_SHEET=doc_sheet,
                          DOC_REV=doc_rev,
                          FILE_NAME=file_name)
                self.send_to_ftp(file_name.getvalue(), vals.get("raw"))
                conn.commit()
            except Exception as ex:
                conn.rollback()
                raise UserError(ex)
        return ret

    def send_to_ftp(self, file_name, raw, attach_id):
        local_copy_path = "/mnt/ifs/"+file_name
        new_file =open(local_copy_path, "wb")
        data = self.env["ir.attachment"].browse(attach_id).datas
        b64decoded_data = base64.b64decode(data)
        new_file.write(b64decoded_data)
        new_file.close()
        file = open(local_copy_path, "rb")
        ftp = self.env["sas.dosya"].ftp_connect()
        ftp.cwd("/RM_MASRAF")
        ftp.storbinary("STOR "+file_name, file)
        file.close()
        ftp.close()

    def attach_ftp_files(self):
        conn = self.env["oracle.conn"].connect(1, False)
        try:
            ftp = self.env["sas.dosya"].ftp_connect()
            c = conn.cursor()
            reader = c.execute("""
                 select 'Ekle' operasyon, replace(substr(key_ref,instr(key_ref,'=')+1),'^','') key_ref, dt.title, e.path, e.file_name, e.user_file_name,
                    decode(dr.lu_name,'HarktMasrafGiris','harkt.masraf','HarktParaTalep','harkt.para.talep','*') res_model from doc_reference_object_tab dr, doc_title_tab dt , edm_file_tab e
                    where dr.lu_name  in('HarktMasrafGiris','HarktParaTalep') and dt.doc_class = dr.doc_class and dt.doc_no = dr.doc_no
                    and dr.doc_class = e.doc_class and dr.doc_no = e.doc_no and dr.doc_sheet = e.doc_sheet and dr.doc_rev = e.doc_rev
                    and   dr.rowversion>=sysdate-1/24
                    and e.user_file_name is not null
 
                    union all
                    (
                    select 'Sil' operasyon, replace(substr(key_ref,instr(key_ref,'=')+1),'^','') key_ref, dt.title,e.path, e.file_name, e.user_file_name,
                     decode(dr.lu_name,'HarktMasrafGiris','harkt.masraf','HarktParaTalep','harkt.para.talep','*') res_model from doc_reference_object_tab as of timestamp sysdate-1/96 dr, doc_title_tab as of timestamp sysdate-1/96 dt,
                    edm_file_tab as of timestamp sysdate-1/96 e 
                    where dr.lu_name  in('HarktMasrafGiris','HarktParaTalep') and dt.doc_class = dr.doc_class and dt.doc_no = dr.doc_no
                     and dr.doc_class = e.doc_class and dr.doc_no = e.doc_no and dr.doc_sheet = e.doc_sheet and dr.doc_rev = e.doc_rev
                     and e.user_file_name is not null
                    minus
                    select 'Sil' operasyon, replace(substr(key_ref,instr(key_ref,'=')+1),'^','') key_ref, dt.title,e.path, e.file_name, e.user_file_name,
                     decode(dr.lu_name,'HarktMasrafGiris','harkt.masraf','HarktParaTalep','harkt.para.talep','*') res_model from doc_reference_object_tab dr, doc_title_tab dt , edm_file_tab e
                    where dr.lu_name  in('HarktMasrafGiris','HarktParaTalep') and dt.doc_class = dr.doc_class and dt.doc_no = dr.doc_no
                    and dr.doc_class = e.doc_class and dr.doc_no = e.doc_no and dr.doc_sheet = e.doc_sheet and dr.doc_rev = e.doc_rev
                    and e.user_file_name is not null
                    )
            """)
            result = reader.fetchall()
            for row in result:
                if row[0] == "Ekle":
                    cnt = 0
                    masraf_id = False
                    talep_id = False
                    if row[6] == "harkt.masraf":
                        masraf_id = self.env["harkt.masraf"].search([("masraf_no", "=", row[1])])[0].id
                        cnt = self.env["ir.attachment"].search_count([("res_model", "=", row[6]),("res_id", "=", masraf_id),
                                                          ("name", "=", row[5])])
                    elif row[6] == "harkt.para.talep":
                        talep_id = self.env["harkt.para.talep"].search([("para_talep_no", "=", row[1])])[0].id
                        cnt = self.env["ir.attachment"].search_count([("res_model", "=", row[6]),("res_id", "=", talep_id),
                                                          ("name", "=", row[5])])
                    if cnt == 0:
                        ftp.cwd("/" + row[3])
                        filename = row[4]
                        ftp.retrbinary('RETR %s' % filename, open("/mnt/ifs/" + filename, 'wb').write)
                        data = Path("/mnt/ifs/" + filename).read_bytes()
                        if filename[-4:].upper() == "HTML":
                            mime_type = "text/html"
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
                            mime_type = "application/octet_stream"

                        vals = {
                            'res_model': row[6],
                            'res_id': masraf_id or talep_id,
                            'datas': base64.b64encode(data),
                            'name': row[5],
                            'mimetype': mime_type
                        }
                        self.env['ir.attachment'].create(vals)
                else:
                    cnt = 0
                    if row[6] == "harkt.masraf":
                        masraf_id = self.env["harkt.masraf"].search([("masraf_no", "=", row[1])])[0].id
                        cnt = self.env["ir.attachment"].search(
                            [("res_model", "=", row[6]), ("res_id", "=", masraf_id),
                             ("name", "=", row[5])]).unlink()
                    elif row[6] == "harkt.para.talep":
                        talep_id = self.env["harkt.para.talep"].search([("para_talep_no", "=", row[1])])[0].id
                        cnt = self.env["ir.attachment"].search(
                            [("res_model", "=", row[6]), ("res_id", "=", talep_id),
                             ("name", "=", row[5])]).unlink()

        except Exception as ex:
            raise UserError("İşlem Başarısız")


