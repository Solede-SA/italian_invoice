"""Basic tests for Italian Invoice app."""

import frappe
from frappe.tests import IntegrationTestCase

from italian_invoice.tests.fixtures import ensure_test_company


class TestBasicFunctionality(IntegrationTestCase):
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
		company = frappe.get_doc("Company", ensure_test_company())

		self.assertTrue(
			hasattr(company, "custom_codice_sistema_interscambio"),
			"Company should have custom_codice_sistema_interscambio field",
		)
		self.assertEqual(
			company.custom_codice_sistema_interscambio,
			"0000000",
			"custom_codice_sistema_interscambio should be set to 0000000",
		)
