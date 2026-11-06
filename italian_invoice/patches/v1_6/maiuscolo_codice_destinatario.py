"""I codici destinatario già salvati in minuscolo o con spazi (dal 06/11/2026 il validate del Customer li
normalizza): maiuscoli e senza spazi, come li vuole lo schema XML."""

import frappe


def execute():
	frappe.db.sql(
		"update `tabCustomer` set custom_codice_univoco = upper(trim(custom_codice_univoco)) "
		"where ifnull(custom_codice_univoco, '') != '' and cast(custom_codice_univoco as binary) != cast(upper(trim(custom_codice_univoco)) as binary)"
	)
