"""CodiceFiscale del cessionario nell'XML.

Bug di partenza: il checkout di daeok salva la Partita IVA anche come codice fiscale; per ditte
individuali e associazioni con Partita IVA il codice fiscale vero è un altro → scarto SdI 00324
«IdFiscaleIVA e CodiceFiscale non coerenti» (SINV/26/00228, PWR LAB).
"""

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.utilities.fatture import get_xml_fiscal_code


def _party(tax_id, fiscal_code):
	return frappe._dict(tax_id=tax_id, fiscal_code=fiscal_code)


class TestCodiceFiscaleXml(UnitTestCase):
	def test_copia_della_partita_iva_non_va_nell_xml(self):
		self.assertIsNone(get_xml_fiscal_code(_party("02769380466", "02769380466")))
		self.assertIsNone(get_xml_fiscal_code(_party("IT02769380466", "02769380466")))

	def test_codice_fiscale_diverso_resta(self):
		self.assertEqual(get_xml_fiscal_code(_party("02769380466", "92076510467")), "92076510467")
		self.assertEqual(get_xml_fiscal_code(_party("03994460362", "TRLFRC84E13F240B")), "TRLFRC84E13F240B")

	def test_senza_partita_iva_resta_il_codice_fiscale(self):
		self.assertEqual(get_xml_fiscal_code(_party(None, "92999999919")), "92999999919")
		self.assertEqual(get_xml_fiscal_code(_party("", "RSSMRA80A01H501U")), "RSSMRA80A01H501U")
