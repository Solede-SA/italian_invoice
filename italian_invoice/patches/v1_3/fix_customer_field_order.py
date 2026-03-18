"""
Fix posizione custom_first_name/custom_last_name nel form Customer.

Quando esiste un Property Setter field_order su Customer (creato da Customize Form),
i campi custom non presenti nella lista finiscono in fondo al form.
Questa patch inserisce i campi nella posizione corretta (dopo salutation).
"""
import json

import frappe


def execute():
	ps_name = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "Customer", "property": "field_order"},
		"name",
	)
	if not ps_name:
		return

	ps = frappe.get_doc("Property Setter", ps_name)
	field_order = json.loads(ps.value)

	# Rimuovi vecchi first_name/last_name (Custom Fields rimossi da patch v1_1)
	# Solo se non sono campi standard del DocType
	standard_fields = {
		f.fieldname
		for f in frappe.get_meta("Customer", cached=False).fields
		if not getattr(f, "is_custom_field", False)
	}

	for old_field in ("first_name", "last_name"):
		if old_field in field_order and old_field not in standard_fields:
			field_order.remove(old_field)

	# Inserisci custom_first_name e custom_last_name dopo salutation
	changed = False
	if "salutation" in field_order:
		sal_idx = field_order.index("salutation")
		for i, fieldname in enumerate(("custom_first_name", "custom_last_name")):
			if fieldname not in field_order:
				field_order.insert(sal_idx + 1 + i, fieldname)
				changed = True

	if changed:
		ps.value = json.dumps(field_order)
		ps.save()
		frappe.clear_cache(doctype="Customer")
		print("✓ Aggiornato field_order di Customer: custom_first_name/custom_last_name dopo salutation")
	else:
		print("⊙ field_order di Customer già corretto")
