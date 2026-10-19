"""Causale e conto bancario nell'XML.

Bug di partenza: SINV/26/00223 (Colosseum) pagata con carta (MP08) è uscita con l'IBAN lituano di
Revolut, ABI e CAB ritagliati da quell'IBAN e la causale «Sales Invoice»; il cliente ha chiesto come
fare il bonifico.
"""

from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.utilities.fatture import get_xml_bank_account, get_xml_causale


def _term(code, bank_account=None):
	return frappe._dict(mode_of_payment_code=code, bank_account=bank_account)


def _bank_account(iban):
	return frappe._dict(bank="Banca", iban=iban, swift_number="BIC")


def _invoice(doctype="Sales Invoice", outstanding_amount=0.0, is_return=0):
	return frappe._dict(doctype=doctype, outstanding_amount=outstanding_amount, is_return=is_return)


class TestDatiPagamentoXml(UnitTestCase):
	def test_carta_senza_conto(self):
		self.assertIsNone(get_xml_bank_account(_term("MP08-Carta di pagamento"), "Revolut EUR"))

	def test_bonifico_senza_conto(self):
		self.assertIsNone(get_xml_bank_account(_term("MP05-Bonifico"), None))

	def test_bonifico_conto_italiano_con_abi_e_cab(self):
		iban = "IT60X0542811101000000123456"
		with patch.object(frappe.db, "get_value", return_value=_bank_account(iban)):
			bank_account = get_xml_bank_account(_term("MP05-Bonifico", "Conto"), None)
		self.assertEqual((bank_account.abi, bank_account.cab), ("05428", "11101"))

	def test_bonifico_conto_estero_senza_abi_e_cab(self):
		with patch.object(frappe.db, "get_value", return_value=_bank_account("LT073250000000007127")):
			bank_account = get_xml_bank_account(_term("MP05-Bonifico"), "Revolut EUR")
		self.assertEqual(bank_account.iban, "LT073250000000007127")
		self.assertIsNone(bank_account.abi)

	def test_bonifico_conto_senza_iban(self):
		with patch.object(frappe.db, "get_value", return_value=_bank_account(None)):
			self.assertRaises(frappe.ValidationError, get_xml_bank_account, _term("MP05-Bonifico"), "Conto")

	def test_causale_fattura_pagata(self):
		self.assertEqual(get_xml_causale(_invoice()), "Fattura già pagata. Non effettuare pagamenti.")

	def test_niente_causale_se_da_pagare_nota_di_credito_o_acquisto(self):
		self.assertIsNone(get_xml_causale(_invoice(outstanding_amount=60.88)))
		self.assertIsNone(get_xml_causale(_invoice(is_return=1)))
		self.assertIsNone(get_xml_causale(_invoice(doctype="Purchase Invoice")))
