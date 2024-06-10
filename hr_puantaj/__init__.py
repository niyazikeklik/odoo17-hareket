from . import controllers
from . import models


def uninstall_hook(cr, registry):
    cr.execute("UPDATE ir_act_window "
               "SET view_mode=replace(view_mode, ',geofence_view', '')"
               "WHERE view_mode LIKE '%,geofence_view%';")
    cr.execute("UPDATE ir_act_window "
               "SET view_mode=replace(view_mode, 'geofence_view,', '')"
               "WHERE view_mode LIKE '%geofence_view,%';")
    cr.execute("DELETE FROM ir_act_window "
               "WHERE view_mode = 'geofence_view';")


def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie =version_info.get('server_serie')
    if server_serie!='17.0':
        raise UserError('Module support Odoo series 17.0 found {}.'.format(server_serie))
    return True