"""Natura N2, N3 e N6 senza sottocodice → scarto SdI 00445 (dal 1/1/2021)."""

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.validation.natura import codice_natura, is_natura_generica, righe_con_natura_generica


class TestNaturaGenerica(UnitTestCase):
	def test_codici_generici(self):
		for valore in ("N2", "N3", "N6", "N3-Non Imponibili", "n6-Inversione Contabile"):
			self.assertTrue(is_natura_generica(valore), valore)

	def test_sottocodici_e_altri_codici_ammessi(self):
		for valore in ("N1", "N2.1", "N3.5", "N4", "N5", "N6.3", "N7", "", None):
			self.assertFalse(is_natura_generica(valore), valore)

	def test_codice_dal_testo_della_select(self):
		self.assertEqual(codice_natura("N1-Escluse ex art. 15"), "N1")
		self.assertIsNone(codice_natura(""))

	def test_righe_della_fattura(self):
		doc = frappe._dict(
			items=[
				frappe._dict(idx=1, custom_motivo_esenzione_iva="N3.2"),
				frappe._dict(idx=2, custom_motivo_esenzione_iva="N3"),
			],
			taxes=[frappe._dict(idx=1, custom_motivo_esenzione_iva=None, tax_exemption_reason="N6-Inversione Contabile")],
		)
		self.assertEqual(righe_con_natura_generica(doc), ["articolo riga 2 (N3)", "tasse riga 1 (N6)"])
