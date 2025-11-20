"""Test fixtures for Italian Invoice app."""

import frappe


def before_tests():
	"""Setup test fixtures before running tests."""
	frappe.db.begin()

	# Patch the _Test Company if it exists or will be created
	# This runs before Frappe creates test records
	if frappe.db.exists("Company", "_Test Company"):
		company = frappe.get_doc("Company", "_Test Company")
		if not company.get("custom_codice_sistema_interscambio"):
			company.custom_codice_sistema_interscambio = "0000000"
			company.save(ignore_permissions=True)
			frappe.db.commit()

	# Monkey patch the Company creation to always include the custom field
	original_insert = frappe.model.document.Document.insert

	def patched_insert(self, *args, **kwargs):
		if self.doctype == "Company" and not self.get("custom_codice_sistema_interscambio"):
			self.custom_codice_sistema_interscambio = "0000000"
		return original_insert(self, *args, **kwargs)

	frappe.model.document.Document.insert = patched_insert
