"""Customer: il codice destinatario si salva maiuscolo e senza spazi, e solo nel formato dello schema XML."""

import frappe

from italian_invoice.utilities import codice_destinatario


def validate(doc, method=None):
	doc.custom_codice_univoco = codice_destinatario.normalizza(doc.custom_codice_univoco)
	errore = codice_destinatario.errore(doc.name, doc.custom_codice_univoco, doc.is_public_administration)
	if errore:
		frappe.throw(errore)
