# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Comunicación Veri*FACTU",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/sergiodeveloper5/verifactu",
    "author": "Aures Tic, ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {"python": ["zeep", "requests", "qrcode", "Pillow"]},
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/aeat_sii_tax_agency_data.xml",
        "data/ir_cron_data.xml",
        "views/aeat_tax_agency_view.xml",
        "views/account_move_view.xml",
        "views/account_fiscal_position_view.xml",
        "views/res_company_view.xml",
        "views/res_partner_view.xml",
        "views/account_journal_views.xml",
        "views/verifactu_queue_view.xml",
        "reports/verifactu_invoice_report.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_es_aeat_verifactu/static/src/css/verifactu.css",
        ],
    },
}
