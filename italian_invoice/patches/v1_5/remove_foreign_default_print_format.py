"""Rimuove il Property Setter `Sales Invoice.default_print_format = CBM Fattura`.

Contaminazione da cbmedical in custom/sales_invoice.json (anche in openapi): ogni migrate
lo risincronizzava su tutti i siti, sovrascrivendo il default scelto in Customize Form e
puntando a un Print Format inesistente (stampa manuale ed email con PDF sbagliate o rotte).
L'entry è stata tolta dal JSON; qui si elimina la riga sui siti dove il Print Format non
esiste. Sui siti cbmedical (dove esiste) resta com'è.
"""

import frappe

PRINT_FORMAT = "CBM Fattura"
PROPERTY_SETTER = "Sales Invoice-main-default_print_format"


def execute():
	if frappe.db.exists("Print Format", PRINT_FORMAT):
		return
	if frappe.db.get_value("Property Setter", PROPERTY_SETTER, "value") == PRINT_FORMAT:
		frappe.delete_doc("Property Setter", PROPERTY_SETTER, force=True, ignore_permissions=True)
		frappe.clear_cache(doctype="Sales Invoice")
