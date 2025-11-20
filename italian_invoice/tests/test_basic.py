"""Basic tests for Italian Invoice app."""

import frappe
from frappe.tests.utils import FrappeTestCase


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
