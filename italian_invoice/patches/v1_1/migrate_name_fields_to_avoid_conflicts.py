"""
Migrazione dei campi first_name/last_name a custom_first_name/custom_last_name.

Questo patch è necessario per risolvere il conflitto con i campi standard del Customer doctype.
ERPNext ha campi standard first_name/last_name (Read Only che fanno fetch dal Contact),
e non possiamo creare Custom Fields con gli stessi nomi.

Il patch:
1. Salva i dati esistenti da first_name/last_name
2. Crea i nuovi campi custom_first_name/custom_last_name
3. Copia tutti i dati dai vecchi ai nuovi campi
4. Rimuove i vecchi Custom Fields problematici
5. È idempotente (può essere eseguito più volte)
"""

import frappe


def execute():
	"""
	Migra i dati da first_name/last_name a custom_first_name/custom_last_name.
	"""
	print("\n" + "=" * 60)
	print("MIGRAZIONE CAMPI NOME CUSTOMER")
	print("=" * 60)

	# Step 1: Salva i dati esistenti
	customers_data = {}
	try:
		customers = frappe.get_all(
			"Customer", fields=["name", "first_name", "last_name"], filters={"customer_type": "Individual"}
		)
		for customer in customers:
			if customer.get("first_name") or customer.get("last_name"):
				customers_data[customer.name] = {
					"first_name": customer.get("first_name"),
					"last_name": customer.get("last_name"),
				}
		print(f"✓ Salvati dati da {len(customers_data)} Customer")
	except Exception as e:
		print(f"⊙ Nessun dato da migrare: {str(e)}")

	# Step 2: Rimuovi i vecchi Custom Fields se esistono
	old_fields = ["Customer-first_name", "Customer-last_name"]
	for field_name in old_fields:
		try:
			if frappe.db.exists("Custom Field", field_name):
				frappe.delete_doc("Custom Field", field_name, force=True, ignore_permissions=True)
				print(f"✓ Rimosso vecchio Custom Field: {field_name}")
		except Exception as e:
			print(f"⊙ Errore rimozione {field_name}: {str(e)}")

	frappe.db.commit()
	frappe.clear_cache(doctype="Customer")

	# Step 3: Crea i nuovi campi
	new_fields = [
		{
			"doctype": "Custom Field",
			"dt": "Customer",
			"fieldname": "custom_first_name",
			"fieldtype": "Data",
			"label": "First Name (E-Invoice)",
			"insert_after": "salutation",
			"print_hide": 1,
			"translatable": 1,
			"depends_on": "eval:doc.customer_type=='Individual'",
			"mandatory_depends_on": "eval:doc.customer_type=='Individual'",
			"module": "Italian Invoice",
		},
		{
			"doctype": "Custom Field",
			"dt": "Customer",
			"fieldname": "custom_last_name",
			"fieldtype": "Data",
			"label": "Last Name (E-Invoice)",
			"insert_after": "custom_first_name",
			"print_hide": 1,
			"translatable": 1,
			"depends_on": "eval:doc.customer_type=='Individual'",
			"module": "Italian Invoice",
		},
	]

	created_count = 0
	for field_data in new_fields:
		try:
			custom_field_name = f"{field_data['dt']}-{field_data['fieldname']}"
			if not frappe.db.exists("Custom Field", custom_field_name):
				custom_field = frappe.get_doc(field_data)
				custom_field.insert(ignore_permissions=True)
				created_count += 1
				print(f"✓ Creato nuovo campo: {custom_field_name}")
			else:
				print(f"⊙ Campo già esistente: {custom_field_name}")
		except Exception as e:
			print(f"✗ Errore creazione campo: {str(e)}")
			frappe.log_error(f"Errore creazione campo: {str(e)}", "Name Fields Migration Error")

	frappe.db.commit()
	frappe.clear_cache(doctype="Customer")

	# Step 4: Ripristina i dati nei nuovi campi
	if customers_data:
		restored_count = 0
		for customer_name, data in customers_data.items():
			try:
				frappe.db.set_value(
					"Customer",
					customer_name,
					{
						"custom_first_name": data.get("first_name"),
						"custom_last_name": data.get("last_name"),
					},
					update_modified=False,
				)
				restored_count += 1
			except Exception as e:
				print(f"✗ Errore ripristino {customer_name}: {str(e)}")

		frappe.db.commit()
		print(f"✓ Ripristinati dati in {restored_count} Customer")

	print("=" * 60)
	print(f"Migrazione completata: {created_count} campi creati")
	print("=" * 60 + "\n")
