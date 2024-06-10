from odoo import models, fields, api


class SasOnayTarihce(models.Model):
    _name = 'sas.onay.tarihce'
    _description = "Satınalma Onay Raporu"
    _rec_name = "sas_no"

    sas_no =fields.Char("Sas No")
    aciklama = fields.Char("Açıklama")
    sas_tarihi = fields.Date("Giriş Tarihi")
    tutar = fields.Float("Tutar")
    para_birimi= fields.Char("Para Birimi")
    birinci_onaylayan = fields.Char("Birinci Onaylayan")
    ikinci_onaylayan = fields.Char("İkinci Onaylayan")
    ucuncu_onaylayan = fields.Char("Üçüncü Onaylayan")
    malzemeler = fields.Text("Sipariş Detayı")
    son_onaylayici = fields.Char("Son Onaylayıcı")
    durum = fields.Char("Durum")
    sayi = fields.Integer("Sayı")
    grup =fields.Char("Grup")

    def _import_report_from_ifs(self):
        self.env.cr.execute("""delete from sas_onay_tarihce""")
        conn = self.env["oracle.conn"].connect(False, False)
        try:
            c = conn.cursor()
            c.execute("""select ORDER_NO, 
                ACIKLAMA, 
                GIRIS_TARIHI, 
                round(TUTAR,0), 
                CURRENCY_CODE, 
                BIRINCI_ONAYLAYAN, 
                IKINCI_ONAYLAYAN, 
                UCUNCU_ONAYLAYAN, 
                MALZEMELER, 
                son_onaylayici,
                rowstate,
                sayi,
                grup
                from SAS_SIPARIS_ONAY_DETAY_RAPORU
                """)
            result = c.fetchall()
            for row in result:
                self.env["sas.onay.tarihce"].create({
                    "sas_no": row[0],
                    "aciklama": row[1],
                    "sas_tarihi": row[2],
                    "tutar": row[3],
                    "para_birimi": row[4],
                    "birinci_onaylayan": row[5],
                    "ikinci_onaylayan": row[6],
                    "ucuncu_onaylayan": row[7],
                    "malzemeler": row[8],
                    "son_onaylayici": row[9],
                    "durum":row[10],
                    "sayi": row[11],
                    "grup": row[12]
                })
        except Exception as ex:
            print(ex)

