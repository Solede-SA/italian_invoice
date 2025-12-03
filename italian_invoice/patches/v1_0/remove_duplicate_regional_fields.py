"""
Patch per rimuovere campi custom duplicati che sono già presenti come campi regionali di ERPNext v15.

Questo patch è necessario perché:
1. ERPNext v15 crea automaticamente campi regionali quando si seleziona "Italy" come regione
2. italian_invoice aveva gli stessi campi nei file custom/*.json
3. Questo causava campi duplicati e errori durante l'installazione

Il patch:
- Identifica campi duplicati (quelli marcati is_system_generated: 1)
- Rimuove i custom field dell'app se esiste già il campo system di ERPNext
- Preserva i dati esistenti
- È idempotente (può essere eseguito più volte senza problemi)
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""
	Rimuove campi custom duplicati che ERPNext v15 ha già creato come regional fields.
	"""
	# Campi regionali che ERPNext crea automaticamente per l'Italia
	regional_fields = {
		"Customer": [
			"first_name",
			"last_name",
			"fiscal_code",
			"pec",
			"recipient_code",
			"is_public_administration",
		],
		"Sales Invoice": [
			"company_fiscal_code",
			"company_fiscal_regime",
			"customer_fiscal_code",
			"type_of_document",
			"vat_collectability",
			"sb_e_invoicing_reference",
			"cb_e_invoicing_reference",
		],
		"Purchase Invoice": ["document_type", "destination_code", "imported_grand_total"],
	}

	removed_count = 0
	skipped_count = 0

	frappe.db.commit()  # Commit transazioni pendenti prima di iniziare

	for doctype, fieldnames in regional_fields.items():
		for fieldname in fieldnames:
			try:
				# Cerca il custom field dell'app italian_invoice
				custom_field_name = f"{doctype}-{fieldname}"

				if not frappe.db.exists("Custom Field", custom_field_name):
					# Campo non esiste come custom field, skip
					skipped_count += 1
					continue

				# Recupera il custom field
				custom_field = frappe.get_doc("Custom Field", custom_field_name)

				# Verifica che sia marcato come system_generated
				# (questi sono i campi che ERPNext crea automaticamente)
				if not custom_field.get("is_system_generated"):
					# Non è un campo system-generated, lo manteniamo
					skipped_count += 1
					continue

				# IMPORTANTE: Verifica che il campo esista nel doctype SENZA il custom field
				# Prima rimuoviamo temporaneamente il custom field dal meta
				# per vedere se ERPNext ha creato il campo di base

				# Get fresh meta
				frappe.clear_cache(doctype=doctype)
				meta = frappe.get_meta(doctype, cached=False)

				# Conta quante volte appare il fieldname
				field_count = sum(1 for f in meta.fields if f.fieldname == fieldname)

				if field_count < 2:
					# Il campo appare solo UNA volta, significa che è solo il nostro custom field
					# Se lo rimuoviamo, il campo sparirà completamente
					# QUINDI LO MANTENIAMO per retrocompatibilità
					print(f"⊙ Mantenuto campo (unica definizione): {doctype}.{fieldname}")
					skipped_count += 1
					continue

				# Se arriviamo qui, il campo appare 2+ volte = c'è un duplicato
				# Significa che ERPNext ha la sua versione E noi abbiamo la nostra
				# Quindi possiamo rimuovere la nostra in sicurezza

				# Tutto ok, rimuoviamo il custom field duplicato
				frappe.delete_doc("Custom Field", custom_field_name, force=True)
				frappe.db.commit()

				removed_count += 1
				print(f"✓ Rimosso campo duplicato: {doctype}.{fieldname}")

			except Exception as e:
				frappe.log_error(
					f"Errore durante rimozione di {doctype}.{fieldname}: {str(e)}",
					"Patch Remove Duplicate Fields Error",
				)
				frappe.db.rollback()
				# Continua con il prossimo campo
				continue

	# Clear cache per assicurarci che i meta siano aggiornati
	for doctype in regional_fields.keys():
		frappe.clear_cache(doctype=doctype)

	# Log finale
	message = f"Patch completato: {removed_count} campi rimossi, {skipped_count} campi saltati"
	print(f"\n{'='*60}")
	print(message)
	print(f"{'='*60}\n")

	frappe.db.commit()
