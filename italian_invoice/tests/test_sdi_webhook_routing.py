"""Test routing webhook SDI: ricevute di conservazione per fatture passive."""

import frappe
from frappe.tests.utils import FrappeTestCase

from italian_invoice.utilities.fatture import handle_sdi_webhook

UUID_PASSIVA = "test-uuid-passiva-0001"


def _receipt_payload(uuid):
	return {
		"data": {
			"object_id": uuid,
			"invoice_uuid": uuid,
			"status": "stored",
			"created_at": "2026-07-21T13:25:11+00:00",
			"updated_at": "2026-07-21T13:26:18+00:00",
			"receipt_received_at": "2026-07-21T13:26:18+00:00",
		},
		"event": "legal-storage-receipt",
	}


class TestLegalStorageReceiptRouting(FrappeTestCase):
	def test_receipt_per_fattura_passiva_registra_conservazione(self):
		fattura = frappe.get_doc({
			"doctype": "Fattura Fornitori SDI",
			"uuid": UUID_PASSIVA,
			"denominazione_fornitore": "Fornitore Test",
			"partita_iva_fornitore": "01234567890",
			"via_webhook": 1,
		}).insert()

		result = handle_sdi_webhook("legal_storage_receipt", _receipt_payload(UUID_PASSIVA))

		self.assertTrue(result["success"])
		fattura.reload()
		self.assertEqual(fattura.conservata, 1)
		self.assertIsNotNone(fattura.data_conservazione)

	def test_receipt_con_uuid_sconosciuto_fallisce(self):
		with self.assertRaises(frappe.ValidationError):
			handle_sdi_webhook("legal_storage_receipt", _receipt_payload("uuid-inesistente-9999"))
