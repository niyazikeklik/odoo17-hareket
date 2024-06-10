

from odoo import api, fields, models


class TrCariEkstreKf(models.AbstractModel):
    _name = 'report.tr_mutabakat_ifs.cari_ekstre_kf'
    _description="Ifs Cari Ekstre Kf"


    @api.model
    def _get_report_values(self, docids, data=None,):
        docs = self.env["tr.mut.kf"].browse(docids)
        doc_model="tr.mut.kf"
        muh_bakiye_tl = 0.0
        muh_bakiye_tl, ekstre_rows = self.env["report.tr_mutabakat_ifs.cari_ekstre"].get_ifs_ekstre(docs[0].company_id.ifs_sirket_kodu,
                            docs[0].vat,
                            docs[0].ilk_ekstre_tarihi,
                            docs[0].tarih
                            )
        return {
            'doc_ids': docids,
            'doc_model': doc_model,
            'docs': docs,
            'dvz_ekstre_rows': ekstre_rows,
            'muh_bakiye_tl': muh_bakiye_tl
        }


class TrCariEkstre(models.AbstractModel):
    _name = 'report.tr_mutabakat_ifs.cari_ekstre'
    _description="Ifs Cari Ekstre"


    @api.model
    def _get_report_values(self, docids, data=None,):
        print(docids)
        docs = self.env["tr.mut"].browse(docids)
        doc_model="tr.mut"
        muh_bakiye_tl = 0.0
        muh_bakiye_tl, ekstre_rows = self.get_ifs_ekstre(docs[0].company_id.ifs_sirket_kodu,
                            docs[0].vat,
                            docs[0].ilk_ekstre_tarihi,
                            docs[0].tarih
                            )
        print("muhasebe_bakiye:")
        print(muh_bakiye_tl)
        return {
            'doc_ids': docids,
            'doc_model': doc_model,
            'docs': docs,
            'dvz_ekstre_rows': ekstre_rows,
            'muh_bakiye_tl': muh_bakiye_tl
        }

    def get_ifs_ekstre(self, ifs_sirket_kodu, vergi_no, baslangic, bitis):
        conn = self.env["oracle.conn"].connect(False, False)
        c = conn.cursor()

        # döviz ekstre oluşturma
        muh_bakiye_tl = 0.0
        pb = []
        c.execute("""
                        SELECT  currency_code, 
                                :BASLANGIC_TARIHI voucher_date,
                                null voucher_type,
                                null voucher_no,
                                'Devir' transaction_type,
                                'Devir' ledger_item_series_id,
                                'Devir' aciklama,
                                NVL(sum(DECODE(SIGN(q.FULL_CURR_AMOUNT),-1,0,q.FULL_CURR_AMOUNT)),0) doviz_borc,
                                NVL(sum(DECODE(SIGN(q.FULL_CURR_AMOUNT),1,0,-q.FULL_CURR_AMOUNT)),0) doviz_alacak,
                                NVL(sum(DECODE(SIGN(q.full_dom_amount),-1,0,q.full_dom_amount)),0) tl_borc,
                                NVL(sum(DECODE(SIGN(q.full_dom_amount), 1,0,-q.full_dom_amount)),0) tl_alacak
                        FROM    IFSAPP.TRYPE_ALL_LEDGER_QRY q
                        WHERE   q.company = :COMPANY_CODE 
                                        AND q.vat_number = :VKN_TCKN_NO 
                                        and q.voucher_date < :BASLANGIC_TARIHI
                        GROUP BY CURRENCY_CODE
                        UNION ALL
                        SELECT  q.currency_code,
                                    q.voucher_date,
                                    q.voucher_type,
                                    q.voucher_no,
                                    q.transaction_type,
                                    q.ledger_item_series_id,
                                    (case when invoice_id is not null then ledger_item_id || ' / ' else '' end) ||
                                    voucher_type||'-'||voucher_no aciklama,
                                    NVL(DECODE(SIGN(q.full_CURR_AMOUNT),-1,0,q.full_CURR_AMOUNT),0) doviz_borc,
                                    NVL(DECODE(SIGN(q.full_CURR_AMOUNT),1,0,-q.full_CURR_AMOUNT),0) doviz_alacak,
                                    NVL(DECODE(SIGN(q.full_dom_amount),-1,0,q.full_dom_amount),0) tl_borc,
                                    NVL(DECODE(SIGN(q.full_dom_amount), 1,0,-q.full_dom_amount),0) tl_alacak
                            FROM IFSAPP.TRYPE_ALL_LEDGER_QRY q
                            WHERE q.company = :COMPANY_CODE 
                                            AND q.vat_number = :VKN_TCKN_NO 
                                            and q.voucher_date >= :BASLANGIC_TARIHI
                                            and q.voucher_date <= :BITIS_TARIHI
                            ORDER BY CURRENCY_CODE, voucher_date asc
                            """,
                  COMPANY_CODE=ifs_sirket_kodu,
                  VKN_TCKN_NO=vergi_no,
                  BASLANGIC_TARIHI=baslangic,
                  BITIS_TARIHI=bitis)
        doviz = "*"
        pb_last_index = -1
        row_index = -1
        for row in c.fetchall():
            muh_bakiye_tl = muh_bakiye_tl + row[9] - row[10]
            if row[0] != doviz:
                tl_bakiye = row[9] - row[10]
                dvz_bakiye = row[7] - row[8]
                islem = "Devir"
                if doviz != '*':
                    pb[pb_last_index]["DETAY"][row_index]["bold"] = 1
                doviz = row[0]
                pb.append({
                    "DETAY": [],
                    "DOVIZ": doviz
                })
                pb_last_index = pb_last_index + 1
                row_index = 0
            else:
                tl_bakiye = tl_bakiye + row[9] - row[10]
                dvz_bakiye = dvz_bakiye + row[7] - row[8]
                islem = "Diğer"
                row_index = row_index + 1

            if row[2] == "DVZ":
                islem = "Kur F. Fat."
            elif row[5] in ("PR", "CD", "SI") and row[4] == 'InvoiceLedgerItem':
                islem = "Fatura"
            elif row[5] in ("PR", "CD", "SI") and row[4] != 'InvoiceLedgerItem':
                islem = "Ödeme"
            elif row[5] == "MAVANS" or row[4] == "TAVANS":
                islem = "Ödeme"
            elif row[5] == "II":
                islem = "Çek İade"

            s = {
                "tarih": row[1].strftime("%d.%m.%Y"),
                "islem": islem,
                "aciklama": row[6],
                "doviz": row[0],
                "kur": ((row[9] - row[10]) / (row[7] - row[8])) if (row[7] - row[8]) != 0 else False,
                "tl_borc": row[9],
                "tl_alacak": row[10],
                "tl_bakiye": tl_bakiye,
                "doviz_borc": row[7],
                "doviz_alacak": row[8],
                "doviz_bakiye": dvz_bakiye,
                "bold": 0
            }
            pb[pb_last_index]["DETAY"].append(s)
        pb[pb_last_index]["DETAY"][row_index]["bold"] = 1

        return muh_bakiye_tl, pb







