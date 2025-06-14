# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk Project",
    "summary": "Add the option to select project in the tickets.",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "category": "After-Sales",
    "author": "PuntSistemes S.L.U., " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/helpdesk",
    "depends": ["helpdesk_mgmt", "project"],
    "data": [
        "views/helpdesk_ticket_views.xml",
        "views/helpdesk_ticket_team_views.xml",
        "views/project_views.xml",
        "views/project_task_views.xml",
    ],
    "development_status": "Beta",
    "auto_install": True,
}
