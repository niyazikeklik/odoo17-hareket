from odoo import http
from odoo.http import request, content_disposition


class IfsFileController(http.Controller):
    @http.route('/web/file/download_document', type='http', auth="public")
    def download_document(self, fullpath=None, filename=None, **kw):
        with open(fullpath, mode='rb') as file:
            fileContent = file.read()
        return request.make_response(fileContent, [('Content-Type', 'application/octet-stream'),
                                            ('Content-Disposition', content_disposition(filename))])
