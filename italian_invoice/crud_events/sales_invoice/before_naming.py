import frappe


def execute(doc, method=None):
	"""Assegna la naming series in base al tipo di cliente/documento, lato server.

	Eseguito in `before_naming` (gira durante set_new_name, PRIMA di validate): è
	l'unico punto in cui la naming series è ancora modificabile per il nome del
	documento. Garantisce la serie PAINV per le Pubbliche Amministrazioni su TUTTI
	i canali di creazione (Desk, API, integrazione OpenAPI, import) — il JS client
	da solo non basta perché viene bypassato dalle creazioni server-side.
	"""
	# Le rettifiche (amend) conservano la serie del documento originale.
	if doc.amended_from:
		return

	# Nota di credito: serie NCINV e tipo TD04 (come il JS), anche quando nasce dal codice con make_sales_return,
	# che copia il TD01 della fattura stornata
	if doc.is_return:
		doc.naming_series = "NCINV/.YY./"
		doc.custom_tipo_di_documento = "TD04"
		return

	is_pa = frappe.db.get_value("Customer", doc.customer, "is_public_administration")
	doc.naming_series = "PAINV/.YY./" if is_pa else "SINV/.YY./"
