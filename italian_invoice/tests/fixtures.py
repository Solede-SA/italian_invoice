"""Test fixtures for Italian Invoice app."""

import frappe


def before_tests():
	"""Setup test fixtures before running tests."""
	# Ensure test company has required custom fields
	if frappe.db.exists("Company", "_Test Company"):
		company = frappe.get_doc("Company", "_Test Company")
		if hasattr(company, "custom_codice_sistema_interscambio"):
			if not company.custom_codice_sistema_interscambio:
				company.custom_codice_sistema_interscambio = "0000000"
				company.save(ignore_permissions=True)
				frappe.db.commit()
