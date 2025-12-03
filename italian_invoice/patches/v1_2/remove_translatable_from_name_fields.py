"""
Rimuove il flag translatable dai campi custom_first_name/custom_last_name.

I nomi propri non devono essere traducibili perché vanno nel XML della fattura elettronica.
Questo patch aggiorna i Custom Fields esistenti per rimuovere il flag translatable.
"""

import frappe


def execute():
	"""
	Rimuove translatable=1 dai campi custom_first_name e custom_last_name.
	"""
	print("\n" + "=" * 60)
	print("RIMOZIONE FLAG TRANSLATABLE DA CAMPI NOME")
	print("=" * 60)

	fields_to_update = [
		"Customer-custom_first_name",
		"Customer-custom_last_name",
	]

	updated_count = 0
	for field_name in fields_to_update:
		try:
			if frappe.db.exists("Custom Field", field_name):
				# Update translatable to 0
				frappe.db.set_value(
					"Custom Field",
					field_name,
					"translatable",
					0,
					update_modified=False,
				)
				updated_count += 1
				print(f"✓ Rimosso translatable da: {field_name}")
			else:
				print(f"⊙ Campo non esistente: {field_name}")
		except Exception as e:
			print(f"✗ Errore aggiornamento {field_name}: {str(e)}")
			frappe.log_error(
				f"Errore aggiornamento campo {field_name}: {str(e)}",
				"Remove Translatable Error",
			)

	frappe.db.commit()
	frappe.clear_cache(doctype="Customer")

	print("=" * 60)
	print(f"Aggiornati {updated_count} campi")
	print("=" * 60 + "\n")
