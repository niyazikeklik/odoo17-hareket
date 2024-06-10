from odoo import models, fields, api
import json
from ftplib import FTP


class SasDosya(models.Model):
    _name = "sas.dosya"
    _description = "Dosya"

    baslik_id = fields.Many2one('sas.baslik',
                                 string='Satınalma Siparişi',
                                 index=True)

    user_created = fields.Char('Oluşturan')
    title = fields.Char('Başlık')
    file_name = fields.Char('Dosya Adı')
    path = fields.Char('Dosya Yolu')
    file_type = fields.Char('Dosya Tipi')

    def action_download_file(self):
        for rec in self:
            ftp = rec.ftp_connect()
            ftp.cwd("/" + rec.path)
            filename = rec.file_name
            ftp.retrbinary('RETR %s' % rec.file_name, open("/mnt/ifs/" + rec.file_name, 'wb').write)
            ftp.close()
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/file/download_document?fullpath=' + "/mnt/ifs/" + rec.file_name + '&filename=' + rec.file_name,
                'target': 'blank',
            }

    def ftp_connect(self):
        ftp = FTP()
        ftp.connect("10.0.0.84", 990)
        ftp.login("odooftpuser", "Har3k3t0$00U$er.")
        return ftp