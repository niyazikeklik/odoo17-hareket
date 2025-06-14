{
    "name": "Helpdesk Ticket Timesheet",
    "summary": "Add HR Timesheet to the tickets for Helpdesk Management.",
    "author": "Aresoltec Canarias, "
    "Punt Sistemes, "
    "SDi Soluciones Digitales, "
    "Solvos, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/helpdesk",
    "license": "AGPL-3",
    "category": "After-Sales",
    "version": "17.0.1.0.0",
    "depends": [
        "helpdesk_mgmt_project",
        "hr_timesheet",
        "project_timesheet_time_control",
    ],
    "data": [
        "views/helpdesk_team_views.xml",
        "views/helpdesk_ticket_views.xml",
         "views/hr_timesheet_views.xml",
        "report/report_timesheet_templates.xml",
    ],
    "demo": ["demo/helpdesk_mgmt_timesheet_demo.xml"],
}
