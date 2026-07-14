"""Override regionale di `erpnext.regional.italy.utils.sales_invoice_validate`.

Registrato in hooks.py via `regional_overrides` (meccanismo ufficiale ERPNext:
`erpnext.allow_regional` usa l'override dell'ultima app installata).

Unica differenza dall'originale: per i clienti Company NON Pubblica
Amministrazione basta la Partita IVA OPPURE il Codice Fiscale — la fattura
elettronica ammette il cessionario identificato dal solo Codice Fiscale
(enti non commerciali senza Partita IVA: associazioni, condomini, ...).
L'originale pretende sempre la Partita IVA e blocca l'inserimento della
fattura. Il template new-e-invoice.xml emette IdFiscaleIVA solo se la
Partita IVA è presente.
"""

import frappe
from frappe import _

from erpnext.regional.italy.utils import validate_address


# Copia adattata di erpnext.regional.italy.utils.sales_invoice_validate:
# tenere allineata a monte, tranne il blocco marcato SOLEDE.
def sales_invoice_validate(doc):
	# Validate company
	if doc.doctype != "Sales Invoice":
		return

	if not doc.company_address:
		frappe.throw(
			_("Please set an Address on the Company '%s'" % doc.company),
			title=_("E-Invoicing Information Missing"),
		)
	else:
		validate_address(doc.company_address)

	company_fiscal_regime = frappe.get_cached_value("Company", doc.company, "fiscal_regime")
	if not company_fiscal_regime:
		frappe.throw(
			_("Fiscal Regime is mandatory, kindly set the fiscal regime in the company {0}").format(
				doc.company
			)
		)
	else:
		doc.company_fiscal_regime = company_fiscal_regime

	doc.company_tax_id = frappe.get_cached_value("Company", doc.company, "tax_id")
	doc.company_fiscal_code = frappe.get_cached_value("Company", doc.company, "fiscal_code")
	if not doc.company_tax_id or not doc.company_fiscal_code:
		frappe.throw(
			_("Please set both the Tax ID and Fiscal Code on Company {0}").format(doc.company),
			title=_("E-Invoicing Information Missing"),
		)
	# Validate customer details
	customer = frappe.get_doc("Customer", doc.customer)

	if customer.customer_type == "Individual":
		doc.customer_fiscal_code = customer.fiscal_code
		if not doc.customer_fiscal_code:
			frappe.throw(
				_("Please set Fiscal Code for the customer '%s'" % doc.customer),
				title=_("E-Invoicing Information Missing"),
			)
	else:
		if customer.is_public_administration:
			doc.customer_fiscal_code = customer.fiscal_code
			if not doc.customer_fiscal_code:
				frappe.throw(
					_("Please set Fiscal Code for the public administration '%s'" % doc.customer),
					title=_("E-Invoicing Information Missing"),
				)
		else:
			# SOLEDE: l'originale esige la Partita IVA (tax_id); qui basta uno
			# tra Partita IVA e Codice Fiscale, come ammesso da FatturaPA per
			# gli enti senza Partita IVA.
			doc.tax_id = customer.tax_id
			doc.customer_fiscal_code = customer.fiscal_code
			if not (doc.tax_id or doc.customer_fiscal_code):
				frappe.throw(
					_("Please set Tax ID or Fiscal Code for the customer '%s'" % doc.customer),
					title=_("E-Invoicing Information Missing"),
				)

	if not doc.customer_address:
		frappe.throw(_("Please set the Customer Address"), title=_("E-Invoicing Information Missing"))
	else:
		validate_address(doc.customer_address)

	if not len(doc.taxes):
		frappe.throw(
			_("Please set at least one row in the Taxes and Charges Table"),
			title=_("E-Invoicing Information Missing"),
		)
	else:
		for row in doc.taxes:
			if row.rate == 0 and row.tax_amount == 0 and not row.tax_exemption_reason:
				frappe.throw(
					_("Row {0}: Please set at Tax Exemption Reason in Sales Taxes and Charges").format(
						row.idx
					),
					title=_("E-Invoicing Information Missing"),
				)

	for schedule in doc.payment_schedule:
		if schedule.mode_of_payment and not schedule.mode_of_payment_code:
			schedule.mode_of_payment_code = frappe.get_cached_value(
				"Mode of Payment", schedule.mode_of_payment, "mode_of_payment_code"
			)
