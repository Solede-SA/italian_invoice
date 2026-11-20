"""L'articolo di una riga della fattura ricevuta: quello col nome uguale alla descrizione, mai uno a caso.

Caso di partenza: il 12/11/2026 una riga «CORSO DI INGLESE» senza articolo ha preso il primo articolo di servizio
trovato, un cespite: ERPNext le ha dato il conto dei cespiti al posto di quello proposto.
"""

from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.utilities import fatture_passive

RIGA = {"numero_linea": 1, "descrizione": "CORSO DI INGLESE"}


class TestArticoloDellaRiga(UnitTestCase):
	def test_trovato_per_nome(self):
		with patch.object(frappe.db, "get_value", return_value="GEN-FORMAZIONE") as letto:
			self.assertEqual(fatture_passive.get_or_create_item_code(RIGA), "GEN-FORMAZIONE")
		letto.assert_called_once_with("Item", {"item_name": "CORSO DI INGLESE"}, "name")

	def test_senza_articolo_si_ferma_anche_con_servizi_generici(self):
		with (
			patch.object(frappe.db, "get_value", return_value=None),
			patch.object(frappe.db, "exists", return_value=True),
			self.assertRaisesRegex(frappe.ValidationError, "riga 1 «CORSO DI INGLESE»"),
		):
			fatture_passive.get_or_create_item_code(RIGA)

	def test_senza_descrizione_si_ferma(self):
		with self.assertRaises(frappe.ValidationError):
			fatture_passive.get_or_create_item_code({"numero_linea": 2, "descrizione": ""})
