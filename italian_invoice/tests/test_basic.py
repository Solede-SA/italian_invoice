"""Basic tests for Italian Invoice app."""

import frappe
from frappe.tests.utils import FrappeTestCase

from italian_invoice.install import fix_erpnext_italy_duplicate_fields

# Ignore these doctypes as they are created by Company itself
test_ignore = ["Account", "Cost Center", "Payment Terms Template", "Salary Component", "Warehouse"]

# Ensure these doctypes have test records before running tests
test_dependencies = [
	"Warehouse Type",
	"UOM",
	"Customer Group",
	"Supplier Group",
	"Territory",
	"Fiscal Year",
]


class TestBasicFunctionality(FrappeTestCase):
	"""Test basic app functionality."""

	def test_app_installed(self):
		"""Test that the app is properly installed."""
		installed_apps = frappe.get_installed_apps()
		self.assertIn("italian_invoice", installed_apps)

	def test_module_exists(self):
		"""Test that the module is accessible."""
		try:
			import italian_invoice

			self.assertTrue(True)
		except ImportError:
			self.fail("italian_invoice module not found")

	def test_company_custom_fields(self):
		"""Test that custom fields are properly added to Company."""
		# Fix ERPNext Italy duplicate fields before creating Company
		# This prevents ValidationError when Italy regional setup runs
		fix_erpnext_italy_duplicate_fields()

		# Create required master data first
		for wh_type in ["Transit", "Regular", "Fixed Asset"]:
			if not frappe.db.exists("Warehouse Type", wh_type):
				frappe.get_doc({"doctype": "Warehouse Type", "name": wh_type}).insert(ignore_permissions=True)

		# Create a minimal test company to verify custom field exists
		if not frappe.db.exists("Company", "_Test Italian Company"):
			company = frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": "_Test Italian Company",
					"abbr": "_TIC",
					"default_currency": "EUR",
					"country": "Italy",
					"custom_codice_sistema_interscambio": "0000000",
				}
			)
			company.insert(ignore_permissions=True)

		company = frappe.get_doc("Company", "_Test Italian Company")

		self.assertTrue(
			hasattr(company, "custom_codice_sistema_interscambio"),
			"Company should have custom_codice_sistema_interscambio field",
		)
		self.assertEqual(
			company.custom_codice_sistema_interscambio,
			"0000000",
			"custom_codice_sistema_interscambio should be set to 0000000",
		)
