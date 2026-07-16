# Run this once per database to configure it as a real Cambodia company:
#   docker compose exec -T odoo bash -c '/entrypoint.sh odoo shell -d <your_db> --no-http' \
#       < setup_cambodia_localization.py
#
# Safe to re-run: setting the country/chart/tax again just confirms the same state.
# Does NOT set the company's Tax ID (TIN) - that's real business data and must be
# entered manually under Settings > Companies > Tax ID.

company = env.company
kh = env.ref('base.kh')

company.partner_id.country_id = kh.id
print(f"Company country set to: {company.partner_id.country_id.name}")

env['account.chart.template'].try_loading('kh', company, install_demo=False)
print(f"Chart template loaded: {company.chart_template}")

income_account = env['account.account'].search([('code', '=', '40100')], limit=1)
tax_nt = env['account.tax'].search([('name', '=', '10% M NT')], limit=1)
if income_account and tax_nt:
    income_account.tax_ids = [(6, 0, [tax_nt.id])]
    print(f"Default tax on {income_account.code} {income_account.name}: {income_account.tax_ids.mapped('name')}")
else:
    print("WARNING: could not find account 40100 or tax '10% M NT' - check manually.")

env.cr.commit()
print("Done. Remember to set the real Tax ID (TIN) manually under Settings > Companies.")
