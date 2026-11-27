"""La data di registrazione di una fattura ricevuta è il giorno in cui è arrivata dal Sistema di Interscambio, nel
fuso del sito: il momento lo dà il provider in UTC (`created_at`), dentro la Fattura Fornitori SDI.

Caso di partenza (ottobre 2026): le fatture prendevano la data del giorno dell'importazione e finivano nel mese
sbagliato rispetto al commercialista."""

import json
from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.utilities.fatture import data_ricezione


def _dati(created_at):
	invoice = {"uuid": "prova", "payload": {"fattura_elettronica_body": [{}]}}
	if created_at:
		invoice["created_at"] = created_at
	return json.dumps({"event": "supplier-invoice", "data": {"data": {"invoice": invoice}}})


@patch("frappe.utils.data.get_system_timezone", return_value="Europe/Rome")
class TestDataRicezione(UnitTestCase):
	def test_giorno_italiano_dal_momento_in_utc(self, _fuso):
		self.assertEqual(str(data_ricezione(_dati("2026-10-29T10:40:29+00:00"))), "2026-10-29")
		# 23:30 UTC del 31/10 è già il 01/11 in Italia: la fattura è di novembre
		self.assertEqual(str(data_ricezione(_dati("2026-10-31T23:30:00+00:00"))), "2026-11-01")

	def test_senza_momento_di_arrivo_si_ferma(self, _fuso):
		with self.assertRaises(frappe.ValidationError):
			data_ricezione(_dati(None))
