"""Il codice destinatario del cliente: salvato maiuscolo e senza spazi, rifiutato se fuori dallo schema XML."""

import frappe
from frappe.tests import IntegrationTestCase


class TestCodiceDestinatario(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.savepoint("codice")
		self.addCleanup(frappe.db.rollback, save_point="codice")

	def _cliente(self, codice, pubblica_amministrazione=0):
		return frappe.get_doc({
			"doctype": "Customer", "customer_name": "Cliente Prova Codice Destinatario", "customer_type": "Company",
			"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
			"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),
			"custom_codice_univoco": codice, "is_public_administration": pubblica_amministrazione,
		}).insert(ignore_permissions=True)

	def test_salvato_maiuscolo_senza_spazi(self):
		self.assertEqual(self._cliente(" krrh6b9 ").custom_codice_univoco, "KRRH6B9")

	def test_fuori_formato_rifiutato(self):
		with self.assertRaises(frappe.ValidationError):
			self._cliente("KRRH6B")  # 6 caratteri: solo per la Pubblica Amministrazione
		self.assertEqual(self._cliente("KRRH6B", pubblica_amministrazione=1).custom_codice_univoco, "KRRH6B")
