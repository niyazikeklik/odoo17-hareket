
import pandas as pd
from odoo import models, fields, api

class FileConverter(models.Model):
    _name = 'file.converter'
    _description = 'File Converter'
    
    def xls_to_xlsx(self, file_path):
        xls = pd.read_excel(file_path)
        file1=file_path[:-3]
        xlsx_path = file1 + "xlsx"
        xlsx_path =xlsx_path.replace("/mnt/ifs/","/opt/odoo/excel")
        #xlsx_path = file_path.replace('.xls', '.xlsx').replace(".XLS",".xlsx")
        xls.to_excel(xlsx_path, index=False)
        return xlsx_path
