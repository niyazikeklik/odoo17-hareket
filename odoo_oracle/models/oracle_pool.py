from odoo import models, fields, api


class OraclePool(models.Model):
    _name = 'oracle.pool'
    _description = "Oracle Pool"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Query Name", required=True)
    table_name = fields.Char("Table Name", required=True)
    cron_id = fields.Many2one("ir.cron", string="Zamanlanmış Aksiyon")
    query = fields.Text("query")
    company_id = fields.Many2one("res.company", "Company")
    state = fields.Selection([("draft", "Draft"), ("passive","Passive"), ("active", "Active")], compute="_compute_state",
                             store=True)

    @api.depends("cron_id", "cron_id.active")
    def _compute_state(self):
        for rec in self:
            if not rec.cron_id:
                self.state = "draft"
            elif rec.cron_id and not rec.cron_id.active:
                self.state = "passive"
            else:
                self.state = "active"

    @api.onchange("cron_id")
    def cron_id_onchange(self):
        for rec in self:
            print(self.env["ir.model"].search([("model","=","oracle.pool")]).id)
            if rec.cron_id:
                rec.cron_id.name = "ORACLE Havuz: "+rec.name
                rec.cron_id.model_id = self.env["ir.model"].search([("model","=","oracle.pool")]).id
                rec.cron_id.user_id = self.env.user.id
                rec.cron_id.code = """env["oracle.pool"].search([('table_name', '=', '"""+rec.table_name+"""')]).execute_pool()"""

    def execute_pool(self):
        self._cr.execute("""select exists(select 1 from pg_tables where tablename='"""+self.table_name+"""') as table_existance""")
        rows = self._cr.fetchall()

        if rows[0][0]:
            self._cr.execute("""drop table """+self.table_name)

        conn = self.env["oracle.conn"].connect(self.company_id.id, False)
        c = conn.cursor()
        c.execute(self.query)
        rows = c.fetchall()
        fields = ""
        for col in c.description:
            print(col[0])
            if str(col[1])[-8:-1] == "VARCHAR":
                fields = fields +" " + col[0] + " character varying("+str(col[2])+"), "
            elif str(col[1])[-5:-1] == "DATE":
                fields = fields + " " + col[0] + " timestamp without time zone, "
            elif str(col[1])[-7:-1] == "NUMBER":
                fields = fields + " "+str(col[0]) +" float, "
            else:
                fields = fields + " "+str(col[0]) +" text, "
        fields = fields[:-2]
        self._cr.execute("""
            create table """+self.table_name+"""("""+fields+""")""")
        for row in rows:
            vals = ""
            i = 0
            for col in c.description:
                if row[i] and row[i] is not None:
                    if str(col[1])[-8:-1] == "VARCHAR":
                        vals = vals + "'"+row[i].replace("'","''")+"', "
                    elif str(col[1])[-5:-1] == "DATE":
                        vals = vals + "'"+row[i].strftime("%Y-%m-%d")+"', "
                    elif str(col[1])[-7:-1] == "NUMBER":
                        vals = vals + str(row[i])+", "
                    else:
                        vals = vals + "'" + row[i].replace("'","''")+ "', "
                else:
                    vals = vals + "null, "
                #print(vals)
                i = i + 1
            vals = vals[:-2]
            self._cr.execute("""insert into """+self.table_name+""" values("""+vals+""")""")




