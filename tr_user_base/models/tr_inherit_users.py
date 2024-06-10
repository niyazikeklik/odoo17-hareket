import pytz

from odoo import api, SUPERUSER_ID, models, registry, fields
from odoo.exceptions import AccessDenied
from odoo.http import request


class Users(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        if not password:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                with self._assert_can_auth():
                    user = self._login_without_email(login)
                    if not user:
                        raise AccessDenied
                    user._check_credentials(password, user_agent_env)
                    tz = request.httprequest.cookies.get('tz') if request else None
                    if tz in pytz.all_timezones and (not user.tz or not user.login_date):
                        # first login or missing tz -> set tz to browser tz
                        user.tz = tz
                    user._update_last_login()
        except AccessDenied as e:
            with registry(db).cursor() as cr:
                cr.execute("SELECT id FROM res_users WHERE lower(login)=%s", (login,))
                res = cr.fetchone()
                if res:
                    raise e

                env = api.Environment(cr, SUPERUSER_ID, {})
                Ldap = env['res.company.ldap']
                for conf in Ldap._get_ldap_dicts():
                    entry = Ldap._authenticate(conf, login, password)
                    if entry:
                        return Ldap._get_or_create_user(conf, login, entry)
                raise e
        return user.id

    def _login_without_email(self, login):
        if login.find('@') > 0:
            login_name = login[0:login.find('@')]
        else:
            login_name = login
        user = self.search(self._get_login_domain(login_name), order=self._get_login_order(), limit=1)
        if not user:
            user = self.search(self._get_login_domain(login), order=self._get_login_order(), limit=1)
            if not user:
                return False
            else:
                return user.with_user(user)
        else:
            return user.with_user(user)