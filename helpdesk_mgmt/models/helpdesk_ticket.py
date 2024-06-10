
from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError
import re

class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _rec_name = "number"
    _rec_names_search = ["number", "name"]
    _order = "priority desc, sequence, number desc, id desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "portal.mixin"]

    @api.depends("team_id")
    def _compute_stage_id(self):
        for ticket in self:
            ticket.stage_id = ticket.team_id._get_applicable_stages()[:1]

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Show always the stages without team, or stages of the default team."""
        search_domain = [
            "|",
            ("id", "in", stages.ids),
            ("team_ids", "=", False),
        ]
        default_team_id = self.default_get(["team_id"]).get("team_id")
        if default_team_id:
            search_domain = [
                                "|",
                                ("team_ids", "=", default_team_id),
                            ] + search_domain
        return stages.search(search_domain, order=order)

    number = fields.Char(string="Ticket number", default="/", readonly=True)
    name = fields.Char(string="Title", required=True)
    description = fields.Html(required=True, sanitize_style=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned user",
        tracking=True,
        index=True,
        domain="team_id and [('share', '=', False),('id', 'in', user_ids)] or [('share', '=', False)]",  # noqa: B950
    )
    user_ids = fields.Many2many(
        comodel_name="res.users", related="team_id.user_ids", string="Users"
    )
    stage_id = fields.Many2one(
        comodel_name="helpdesk.ticket.stage",
        string="Stage",
        compute="_compute_stage_id",
        store=True,
        readonly=False,
        ondelete="restrict",
        tracking=True,
        group_expand="_read_group_stage_ids",
        copy=False,
        index=True,
        domain="['|',('team_ids', '=', team_id),('team_ids','=',False)]",
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="İlgili Kişi")
    partner_name = fields.Char()
    partner_email = fields.Char(string="Email")

    

    last_stage_update = fields.Datetime(default=fields.Datetime.now)
    assigned_date = fields.Datetime()
    closed_date = fields.Datetime()
    closed = fields.Boolean(related="stage_id.closed")
    unattended = fields.Boolean(related="stage_id.unattended", store=True)
    tag_ids = fields.Many2many(comodel_name="helpdesk.ticket.tag", string="Tags")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    channel_id = fields.Many2one(
        comodel_name="helpdesk.ticket.channel",
        string="Channel",
        #isDefault true olanı default olarak seçer
        default=lambda self: self.env["helpdesk.ticket.channel"].search([("isDefault", "=", True)], limit=1),
        help="Channel indicates where the source of a ticket"
        "comes from (it could be a phone call, an email...)"

    )
    category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Category",
    )
    team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Team",
        index=True,
    )
    priority = fields.Selection(
        selection=[
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Very High"),
        ],
        default="1",
    )
    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "helpdesk.ticket")],
        string="Media Attachments",
    )
    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked"),
        ],
    )
    sequence = fields.Integer(
        index=True,
        default=10,
        help="Gives the sequence order when displaying a list of tickets.",
    )
    active = fields.Boolean(default=True)

    @api.depends("name")
    def _compute_display_name(self):
        for ticket in self:
            ticket.display_name = f"{ticket.number} - {ticket.name}"

    def assign_to_me(self):
        self.team_id = self.env["helpdesk.ticket.team"].search(
            [("user_ids", "in", self.env.user.id)], limit=1
        )
    
        self.write(
            {
                "user_id": self.env.user.id,
                "team_id": self.team_id.id
            }
        )

    def action_to_cancel(self):
        action = {
              'name': 'Neden İptal Edildi?',
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'helpdesk.cancel.reason',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': {
                    'default_ticket_id': self.id,
                    'form_type': "0"
              }
        }
        return action
    

    
    def action_to_red(self):
        self.write({"stage_id": 6})

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email

    # eğer iptal edildi veya reddedildi ise stage_id değişemez.
    @api.onchange("stage_id")
    def onchange_stage_id(self):
        current_stage_id = self._origin.stage_id
        if current_stage_id.closed:
            self.stage_id = current_stage_id
            return {
                "warning": {
                    "title": _("Warning"),
                    "message": _("Kapalı bir statüde değişiklik yapamazsınız."),
                }
            }
            
        
    

        
        
        
    # kategorinin bağlı olduğu takımı alır
    @api.onchange("category_id")
    def onchange_category_id(self):
        if self.category_id:
            self.team_id = self.category_id.team_id
            #if(self.user_ids):
            #    self.user_id = self.user_ids[0]
            #else:
            #    self.user_id = False
            return {

                "domain": {
                    "user_id": [
                        ("id", "in", self.user_ids.ids),
                    ],
                },

                
            }

        
        
    
    
    def _resim_alanlarini_bul(self, metin):
        resim_alanlari = []
        desen = r'src="cid:([^"]+)"'
        eslesmeler = re.finditer(desen, metin)

        for eslesme in eslesmeler:
            if(eslesme.group(1).find("@") == -1):
                continue
            resim_adi = eslesme.group(1).split("@")[0]
            resim_id = eslesme.group(1).split("@")[1]
            baslangic_index = eslesme.start()
            bitis_index = eslesme.end()

            resim_alanlari.append({
                "başlangıç_index": baslangic_index,
                "bitiş_index": bitis_index,
                "resim_adı": resim_adi,
                "resim_id": resim_id
            })

        return resim_alanlari
    
    def resim_kaynaklarini_degistir(self, metin , tic_id):
        resim_alanlari = self._resim_alanlarini_bul(metin)
        for resim_alani in resim_alanlari:
            attachment = self.env["ir.attachment"].search([
                ("name", "ilike", resim_alani["resim_adı"] + "%" ),
                ("res_model", "=", "helpdesk.ticket"),
                ("res_id", "=", tic_id)
            ], limit=1)
            if attachment:
                resim_adresi = f"src=/web/image/{attachment.id}?filename={attachment.name}"
                metin = metin.replace(metin[resim_alani["başlangıç_index"]:resim_alani["bitiş_index"]], resim_adresi)
            
        return metin
                
                



    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    def _creation_subtype(self):
        return self.env.ref("helpdesk_mgmt.hlp_tck_created")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("number", "/") == "/":
                vals["number"] = self._prepare_ticket_number(vals)
            if vals.get("user_id") and not vals.get("assigned_date"):
                vals["assigned_date"] = fields.Datetime.now()
            if vals.get("description"):
                vals["description"] =  self.env["message.filter.helper"].get_cleaned_text(vals["description"], "helpdesk.ticket")
            
        res = super().create(vals_list)
        return res
    
    #read form 
    def read(self, fields, load="_classic_read"):
        res = super().read(fields, load)
        for ticket in res:
            #ticket["description"] = self.env["message.filter.helper"].get_cleaned_text(ticket["description"], "helpdesk.ticket")
            if("description" in ticket and self._name in "helpdesk.ticket" and ticket["description"] != False):
                ticket["description"] = self.resim_kaynaklarini_degistir(ticket["description"], ticket["id"])
        return res
    
    

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_ticket_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        for _ticket in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["helpdesk.ticket.stage"].browse([vals["stage_id"]])
                vals["last_stage_update"] = now
                if stage.closed:
                    vals["closed_date"] = now
            if vals.get("user_id"):
                vals["assigned_date"] = now
            if vals.get("description"):
                vals["description"] =  self.env["message.filter.helper"].get_cleaned_text(vals["description"], "helpdesk.ticket")
        
        res = super().write(vals)
        #self.resim_kaynaklarini_degistir()
        return res
        
                


    def action_duplicate_tickets(self):
        for ticket in self.browse(self.env.context["active_ids"]):
            ticket.copy()

    def _prepare_ticket_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("helpdesk.ticket.sequence") or "/"

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for item in self:
            item.access_url = "/my/ticket/%s" % (item.id)
        return res

    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        ticket = self[0]
        if "stage_id" in tracking and ticket.stage_id.mail_template_id:
            res["stage_id"] = (
                ticket.stage_id.mail_template_id,
                {
                    # Need to set mass_mail so that the email will always be sent
                    "composition_mode": "mass_mail",
                    "auto_delete_keep_log": False,
                    "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "email_layout_xmlid": "mail.mail_notification_light",
                },
            )
        return res

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new from mail gateway so we can set correct
        default values.
        """
        if custom_values is None:
            custom_values = {}
        defaults = {
            "name": msg.get("subject") or _("No Subject"),
            "description": msg.get("body"),
            "partner_email": msg.get("from"),
            "partner_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        # Write default values coming from msg
        ticket = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=ticket, force_create=False
            )
            if p
        ]
        ticket.message_subscribe(partner_ids)
        return ticket

    def message_update(self, msg, update_vals=None):
        """Override message_update to subscribe partners"""
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=self, force_create=False
            )
            if p
        ]
        self.message_subscribe(partner_ids)
        res = super().message_update(msg, update_vals=update_vals)
        return res
    

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for ticket in self:
                if ticket.partner_id:
                    ticket._message_add_suggested_recipient(
                        recipients, partner=ticket.partner_id, reason=_("Customer")
                    )
                elif ticket.partner_email:
                    ticket._message_add_suggested_recipient(
                        recipients,
                        email=ticket.partner_email,
                        reason=_("Customer Email"),
                    )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            return recipients
        return recipients

    def _notify_get_reply_to(self, default=None):
        """Override to set alias of tasks to their team if any."""
        aliases = self.sudo().mapped("team_id")._notify_get_reply_to(default=default)
        res = {ticket.id: aliases.get(ticket.team_id.id) for ticket in self}
        leftover = self.filtered(lambda rec: not rec.team_id)
        if leftover:
            res.update(
                super(HelpdeskTicket, leftover)._notify_get_reply_to(default=default)
            )
        return res
