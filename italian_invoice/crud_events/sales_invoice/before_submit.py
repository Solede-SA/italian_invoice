import frappe
from frappe import _


def execute(doc, method=None):
	"""Validazione fail-loud dei campi obbligatori per la fattura elettronica (SDI).

	Eseguita al SUBMIT (non al save): una bozza può essere incompleta, ma una fattura
	sottomessa/trasmissibile a SDI deve avere indirizzo cliente, P.IVA/Codice Fiscale e —
	per le Pubbliche Amministrazioni — il Codice Destinatario (codice univoco IPA).

	Centralizzata qui: copre TUTTE le Sales Invoice del bench (garemed, daeok, manuali),
	così la regola fiscale è una sola e non duplicata per app.
	"""
	if not doc.customer_address:
		frappe.throw(_("Sales Invoice {0}: indirizzo di fatturazione mancante, obbligatorio per la fattura elettronica.").format(doc.name))

	customer = frappe.db.get_value(
		"Customer", doc.customer,
		["tax_id", "fiscal_code", "custom_codice_univoco", "is_public_administration"],
		as_dict=True,
	)
	if not customer:
		frappe.throw(_("Sales Invoice {0}: cliente {1} non trovato.").format(doc.name, doc.customer))

	# B2B: Partita IVA (tax_id). B2C / privati: Codice Fiscale (fiscal_code). Per la fattura
	# elettronica ne basta uno dei due — i privati non hanno P.IVA.
	if not (customer.tax_id or customer.fiscal_code or doc.get("tax_id")):
		frappe.throw(_("Cliente {0}: Partita IVA / Codice Fiscale mancante, obbligatorio per la fattura elettronica.").format(doc.customer))

	if customer.is_public_administration and not customer.custom_codice_univoco:
		frappe.throw(_("Cliente PA {0}: Codice Destinatario (codice univoco IPA) mancante, obbligatorio per fatturare alla Pubblica Amministrazione.").format(doc.customer))
