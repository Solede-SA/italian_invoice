"""Test fixtures for Italian Invoice app."""

import frappe


def before_tests():
	"""Setup test fixtures before running tests."""
	frappe.flags.in_test = True

	# Create necessary Warehouse Types for ERPNext
	warehouse_types = ["Transit", "Regular", "Fixed Asset"]
	for wh_type in warehouse_types:
		if not frappe.db.exists("Warehouse Type", wh_type):
			frappe.get_doc({"doctype": "Warehouse Type", "name": wh_type}).insert(
				ignore_permissions=True, ignore_if_duplicate=True
			)

	# Create UOM if not exists
	if not frappe.db.exists("UOM", "Nos"):
		frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(
			ignore_permissions=True, ignore_if_duplicate=True
		)

	if not frappe.db.exists("UOM", "Unit"):
		frappe.get_doc({"doctype": "UOM", "uom_name": "Unit"}).insert(
			ignore_permissions=True, ignore_if_duplicate=True
		)

	frappe.db.commit()

	# Monkey patch Company creation to always include the custom field
	original_insert = frappe.model.document.Document.insert

	def patched_insert(self, *args, **kwargs):
		if self.doctype == "Company" and not self.get("custom_codice_sistema_interscambio"):
			self.custom_codice_sistema_interscambio = "0000000"
		return original_insert(self, *args, **kwargs)

	frappe.model.document.Document.insert = patched_insert
