import json

import frappe


def before_install():
	"""
	Fix ERPNext Italy regional setup bug that creates duplicate fieldnames.
	Migrates data from ERPNext regional Custom Fields before removing them.
	"""
	fix_erpnext_italy_duplicate_fields()


def after_install():
	"""Create default document types and ensure required fields for e-invoicing"""
	create_default_document_types()
	create_italian_customer_fields()


def create_default_document_types():
	"""Create default Tipologia di documento e-Invoice records"""

	document_types = [
		{"codice": "TD01", "descrizione": "Fattura", "tipologia": "Fattura"},
		{
			"codice": "TD02",
			"descrizione": "Acconto/Anticipo su fattura",
			"tipologia": "Fattura",
		},
		{
			"codice": "TD03",
			"descrizione": "Acconto/Anticipo su parcella",
			"tipologia": "Fattura",
		},
		{"codice": "TD04", "descrizione": "Nota di credito", "tipologia": "Fattura"},
		{"codice": "TD05", "descrizione": "Nota di debito", "tipologia": "Fattura"},
		{"codice": "TD06", "descrizione": "Parcella", "tipologia": "Fattura"},
		{
			"codice": "TD16",
			"descrizione": "Integrazione fattura reverse charge interno",
			"tipologia": "Fattura",
		},
		{
			"codice": "TD17",
			"descrizione": "Integrazione/autofattura per acquisto servizi dall'estero",
			"tipologia": "AutoFattura",
		},
		{
			"codice": "TD18",
			"descrizione": "Integrazione per acquisto di beni intracomunitari",
			"tipologia": "AutoFattura",
		},
		{
			"codice": "TD19",
			"descrizione": "Integrazione/autofattura per acquisto di beni ex art.17 c.2 DPR 633/72",
			"tipologia": "AutoFattura",
		},
		{
			"codice": "TD20",
			"descrizione": "Autofattura per regolarizzazione e integrazione delle fatture (art.6 c.8 d.lgs. 471/97 o art.46 c.5 D.L. 331/93)",
			"tipologia": "AutoFattura",
		},
		{
			"codice": "TD21",
			"descrizione": "Autofattura per splafonamento",
			"tipologia": "AutoFattura",
		},
		{
			"codice": "TD22",
			"descrizione": "Estrazione beni da Deposito IVA",
			"tipologia": "Fattura",
		},
		{
			"codice": "TD23",
			"descrizione": "Estrazione beni da Deposito IVA con versamento dell'IVA",
			"tipologia": "Fattura",
		},
		{
			"codice": "TD24",
			"descrizione": "Fattura differita di cui all'art.21, comma 4, lett. a)",
			"tipologia": "Fattura",
		},
		{
			"codice": "TD25",
			"descrizione": "Fattura differita di cui all'art.21, comma 4, terzo periodo lett. b)",
			"tipologia": "Fattura",
		},
		{
			"codice": "TD26",
			"descrizione": "Cessione di beni ammortizzabili e per passaggi interni (ex art.36 DPR 633/72)",
			"tipologia": "Fattura",
		},
		{
			"codice": "TD27",
			"descrizione": "Fattura per autoconsumo o per cessioni gratuite senza rivalsa",
			"tipologia": "Fattura",
		},
	]

	for doc_type in document_types:
		# Check if record already exists
		if not frappe.db.exists("Tipologia di documento e-Invoice", {"codice": doc_type["codice"]}):
			doc = frappe.get_doc(
				{
					"doctype": "Tipologia di documento e-Invoice",
					"codice": doc_type["codice"],
					"descrizione": doc_type["descrizione"],
					"tipologia": doc_type["tipologia"],
				}
			)
			doc.insert(ignore_permissions=True)
			frappe.db.commit()

	frappe.msgprint("Default document types created successfully", alert=True)


def create_italian_customer_fields():
	"""
	Create custom_first_name and custom_last_name Custom Fields for Italian e-invoicing.
	Uses custom_ prefix to avoid conflicts with standard Customer fields.
	"""
	fields_to_create = [
		{
			"doctype": "Custom Field",
			"dt": "Customer",
			"fieldname": "custom_first_name",
			"fieldtype": "Data",
			"label": "First Name (E-Invoice)",
			"insert_after": "salutation",
			"print_hide": 1,
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
			"depends_on": "eval:doc.customer_type=='Individual'",
			"module": "Italian Invoice",
		},
	]

	created_count = 0
	skipped_count = 0

	for field_data in fields_to_create:
		custom_field_name = f"{field_data['dt']}-{field_data['fieldname']}"

		# Check if Custom Field already exists with correct module
		existing_field = frappe.db.get_value("Custom Field", custom_field_name, "module")
		if existing_field and existing_field == "Italian Invoice":
			print(f"⊙ Campo già esistente, skip: {custom_field_name}")
			skipped_count += 1
			continue
		elif existing_field:
			# Field exists but with wrong module, remove it first
			print(f"⊙ Rimozione campo con module errato: {custom_field_name}")
			frappe.delete_doc("Custom Field", custom_field_name, force=True, ignore_permissions=True)
			frappe.db.commit()

		# Create the Custom Field
		try:
			custom_field = frappe.get_doc(field_data)
			custom_field.insert(ignore_permissions=True)
			frappe.db.commit()
			created_count += 1
			print(f"✓ Creato campo: {custom_field_name}")
		except Exception as e:
			print(f"✗ Errore creazione {custom_field_name}: {str(e)}")
			frappe.log_error(
				f"Errore creazione campo {custom_field_name}: {str(e)}",
				"Italian Invoice Install Error",
			)
			continue

	if created_count > 0 or skipped_count > 0:
		print(f"\n{'='*60}")
		print(f"Campi Customer per e-invoicing: {created_count} creati, {skipped_count} già esistenti")
		print(f"{'='*60}\n")

	# Restore migrated data if any
	restore_migrated_customer_data()


def fix_erpnext_italy_duplicate_fields():
	"""
	Fix ERPNext Italy regional setup bug.

	ERPNext Italy regional setup creates Custom Fields 'first_name' and 'last_name' on Customer,
	but these fieldnames already exist as standard Read Only fields in the Customer doctype.
	This creates an invalid state causing UniqueFieldnameError.

	This function:
	1. Checks if problematic Custom Fields exist
	2. Saves all data from these fields
	3. Removes the Custom Fields
	4. Data will be restored in after_install when fields are recreated
	"""
	problematic_fields = ["Customer-first_name", "Customer-last_name"]

	fields_to_migrate = []
	for field_name in problematic_fields:
		if frappe.db.exists("Custom Field", field_name):
			fields_to_migrate.append(field_name)

	if not fields_to_migrate:
		print("✓ Nessun campo duplicato di ERPNext da migrare")
		return

	print(f"\n{'='*60}")
	print("MIGRAZIONE CAMPI DUPLICATI DI ERPNEXT")
	print(f"{'='*60}")
	print(f"Trovati {len(fields_to_migrate)} campi problematici da migrare")

	# Save data from all Customers (old field names)
	customers_data = {}
	customers = frappe.get_all(
		"Customer", fields=["name", "first_name", "last_name", "custom_first_name", "custom_last_name"]
	)

	for customer in customers:
		# Save from both old and new field names
		first = customer.get("custom_first_name") or customer.get("first_name")
		last = customer.get("custom_last_name") or customer.get("last_name")
		if first or last:
			customers_data[customer.name] = {"custom_first_name": first, "custom_last_name": last}

	if customers_data:
		print(f"✓ Salvati dati da {len(customers_data)} Customer")

		# Store data in a SingleDocType for retrieval in after_install
		if not frappe.db.exists("SingleDocType", "Italian Invoice Migration Data"):
			# Store in a simple JSON file in site's private folder
			migration_file = frappe.get_site_path("private", "files", "italian_invoice_migration.json")
			with open(migration_file, "w") as f:
				json.dump(customers_data, f)
			print(f"✓ Dati salvati in: {migration_file}")
	else:
		print("✓ Nessun dato da salvare")

	# Remove problematic Custom Fields
	for field_name in fields_to_migrate:
		try:
			frappe.delete_doc("Custom Field", field_name, force=True, ignore_permissions=True)
			print(f"✓ Rimosso Custom Field: {field_name}")
		except Exception as e:
			print(f"✗ Errore rimozione {field_name}: {str(e)}")
			frappe.log_error(
				f"Errore rimozione Custom Field {field_name}: {str(e)}", "Italian Invoice Migration"
			)

	frappe.db.commit()

	print(f"{'='*60}")
	print("Migrazione completata!")
	print(f"{'='*60}\n")


def restore_migrated_customer_data():
	"""
	Restore Customer data that was migrated during before_install.
	"""
	import os

	migration_file = frappe.get_site_path("private", "files", "italian_invoice_migration.json")

	if not os.path.exists(migration_file):
		print("✓ Nessun dato da ripristinare")
		return

	print(f"\n{'='*60}")
	print("RIPRISTINO DATI MIGRATI")
	print(f"{'='*60}")

	try:
		with open(migration_file) as f:
			customers_data = json.load(f)

		restored_count = 0
		for customer_name, data in customers_data.items():
			try:
				customer = frappe.get_doc("Customer", customer_name)
				if data.get("custom_first_name"):
					customer.custom_first_name = data["custom_first_name"]
				if data.get("custom_last_name"):
					customer.custom_last_name = data["custom_last_name"]
				customer.save(ignore_permissions=True)
				restored_count += 1
			except Exception as e:
				print(f"✗ Errore ripristino {customer_name}: {str(e)}")
				frappe.log_error(
					f"Errore ripristino dati Customer {customer_name}: {str(e)}",
					"Italian Invoice Data Restore",
				)

		frappe.db.commit()

		print(f"✓ Ripristinati dati per {restored_count} Customer")

		# Remove migration file
		os.remove(migration_file)
		print("✓ File di migrazione rimosso")

	except Exception as e:
		print(f"✗ Errore durante ripristino: {str(e)}")
		frappe.log_error(f"Errore ripristino dati migrati: {str(e)}", "Italian Invoice Data Restore")

	print(f"{'='*60}\n")
