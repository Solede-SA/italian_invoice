"""Fornitore nuovo dalla fattura ricevuta: il gruppo è quello predefinito delle Impostazioni Acquisti, mai il primo
trovato (era a volte il gruppo di gruppi, che ERPNext rifiuta)."""

from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.utilities.fatture_passive import get_default_supplier_group


class TestFornitoreNuovo(UnitTestCase):
	def test_gruppo_predefinito(self):
		with patch.object(frappe.db, "get_single_value", return_value="Services"):
			self.assertEqual(get_default_supplier_group(), "Services")

	def test_senza_gruppo_predefinito_si_ferma(self):
		with patch.object(frappe.db, "get_single_value", return_value=None):
			with self.assertRaisesRegex(frappe.ValidationError, "gruppo fornitori predefinito"):
				get_default_supplier_group()
