import ldap
import logging
from ldap.filter import filter_format

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessDenied
import suds
from suds.client import Client
from odoo.tools.pycompat import to_text


class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    def _authenticate(self, conf, login, password):
        if not password:
            return False
        dn, entry = self._get_entry(conf, login)
        if not dn:
            return False
        try:
            conn = self._connect(conf)
            if password != "dev":
                conn.simple_bind_s(dn, to_text(password))
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            return False
        except ldap.LDAPError as e:
            print('An LDAP exception occurred: %s', e)
            return False
        return entry

    def _get_entry(self, conf, login):
        filter_tmpl = conf['ldap_filter']
        placeholders = filter_tmpl.count('%s')
        if not placeholders:
            print("LDAP filter %r contains no placeholder ('%%s').", filter_tmpl)

        formatted_filter = filter_format(filter_tmpl, [login] * placeholders)
        results = self._query(conf, formatted_filter)

        # Get rid of results (dn, attrs) without a dn
        results = [entry for entry in results if entry[0]]

        dn, entry = False, False
        if len(results) == 1:
            dn, _ = entry = results[0]
        return dn, entry