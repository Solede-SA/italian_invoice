"""Rimuove il campo di prova "custom_test" da Sales Invoice.

Residuo di un test manuale (label "Test", visibile agli utenti nel tab SDI),
mai referenziato da codice: l'entry è stata tolta da custom/sales_invoice.json
e questa patch elimina la riga già presente in tabCustom Field sui siti
esistenti. La colonna resta (Frappe non droppa colonne): innocua e vuota.
Idempotente: delete_doc con ignore_missing (default) non fallisce se il
campo non esiste (siti nuovi).
"""

import frappe


def execute():
	frappe.delete_doc("Custom Field", "Sales Invoice-custom_test", force=True, ignore_permissions=True)
