"""Ritenuta, bollo, cassa previdenziale e scadenze delle fatture ricevute: calcoli e controlli senza sito (le
letture di Company, Item e Mode of Payment sono finte).

Caso di partenza: PINV/26/00111 (parcella di un ragioniere) era stata registrata senza ritenuta: riga 80,00 con
ritenuta «SI», cassa 4 % = 3,20 non soggetta, imponibile IVA 83,20, ritenuta 20 % = 16,00, totale documento
101,50, netto da pagare 85,50, una rata da 101,50 (al lordo).
"""

from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.utilities import fatture_passive_extra as extra

COMPANY = "Società di prova"
IMPOSTAZIONI = {
	"custom_account_ritenuta": "35.03.11 - Erario c/ritenute - X",
	"custom_account_bollo": "35.07.27 - Bollo - X",
	"custom_account_cassa_previdenziale": "61.01.19.03 - Cassa - X",
	"custom_item_cassa_previdenziale": "GEN-CASSA-PREV",
	"stock_uom": "Nr",
}
RIGHE = [{"numero_linea": 1, "prezzo_totale": 80.00, "ritenuta": "SI"}]


def _doc_parcella(**modifiche):
	doc = {
		"tipo_documento": "TD06",
		"numero": "384/00",
		"data": "2026-05-14",
		"importo_totale_documento": 101.50,
		"dati_ritenuta": [
			{"tipo_ritenuta": "RT01", "importo_ritenuta": 16.00, "aliquota_ritenuta": 20.00, "causale_pagamento": "A"}
		],
		"dati_cassa_previdenziale": [
			{"tipo_cassa": "TC08", "al_cassa": 4.00, "importo_contributo_cassa": 3.20, "imponibile_cassa": 80.00, "aliquota_iva": 22.00}
		],
		"dati_bollo": None,
	}
	doc.update(modifiche)
	return doc


def _pagamento(rate, condizioni="TP02"):
	return [{"condizioni_pagamento": condizioni, "dettaglio_pagamento": rate}]


def _valore_in_cache_finto(doctype, name, campo):
	return IMPOSTAZIONI.get(campo)


class TestBlocchi(UnitTestCase):
	def setUp(self):
		super().setUp()
		finto = patch.object(frappe, "get_cached_value", side_effect=_valore_in_cache_finto)
		finto.start()
		self.addCleanup(finto.stop)

	def _integra(self, doc, is_return=False):
		return extra.integra_blocchi(doc, RIGHE, COMPANY, is_return)

	def test_parcella_con_cassa_e_ritenuta(self):
		righe, tasse, campi = self._integra(_doc_parcella())
		self.assertEqual(len(righe), 1)
		self.assertEqual((righe[0]["item_code"], righe[0]["rate"], righe[0]["uom"], righe[0]["expense_account"]), ("GEN-CASSA-PREV", 3.2, "Nr", IMPOSTAZIONI["custom_account_cassa_previdenziale"]))
		self.assertEqual(righe[0]["tax_rate"], 22.0)
		self.assertEqual(len(tasse), 1)
		ritenuta = tasse[0]
		self.assertEqual((ritenuta["add_deduct_tax"], ritenuta["category"], ritenuta["tax_amount"]), ("Deduct", "Total", 16.0))
		self.assertEqual(ritenuta["account_head"], IMPOSTAZIONI["custom_account_ritenuta"])
		self.assertEqual(campi, {"custom_ritenuta_tipo": "RT01", "custom_ritenuta_causale": "A", "custom_ritenuta_importo": 16.0})

	def test_cassa_soggetta_a_ritenuta_entra_nella_base(self):
		doc = _doc_parcella()
		doc["dati_cassa_previdenziale"][0]["ritenuta"] = "SI"
		doc["dati_ritenuta"][0]["importo_ritenuta"] = 16.64  # 20 % di 83,20
		self.assertEqual(self._integra(doc)[1][0]["tax_amount"], 16.64)

	def test_ritenuta_che_non_torna_ferma(self):
		doc = _doc_parcella()
		doc["dati_ritenuta"][0]["importo_ritenuta"] = 15.00
		with self.assertRaisesRegex(frappe.ValidationError, "non torna"):
			self._integra(doc)

	def test_tipo_di_ritenuta_non_gestito_ferma(self):
		doc = _doc_parcella()
		doc["dati_ritenuta"][0]["tipo_ritenuta"] = "RT04"
		with self.assertRaisesRegex(frappe.ValidationError, "RT04"):
			self._integra(doc)

	def test_cassa_sconosciuta_ferma(self):
		doc = _doc_parcella()
		doc["dati_cassa_previdenziale"][0]["tipo_cassa"] = "TC99"
		with self.assertRaisesRegex(frappe.ValidationError, "TC99"):
			self._integra(doc)

	def test_bollo_virtuale(self):
		doc = _doc_parcella(dati_ritenuta=None, dati_cassa_previdenziale=None, dati_bollo={"bollo_virtuale": "SI", "importo_bollo": 2.00})
		righe, tasse, campi = self._integra(doc)
		self.assertEqual((righe, campi), ([], {}))
		self.assertEqual((tasse[0]["add_deduct_tax"], tasse[0]["tax_amount"], tasse[0]["account_head"]), ("Add", 2.0, IMPOSTAZIONI["custom_account_bollo"]))

	def test_nota_di_credito_inverte_i_segni(self):
		righe, tasse, _campi = self._integra(_doc_parcella(), is_return=True)
		self.assertEqual((righe[0]["qty"], righe[0]["rate"]), (-1, 3.2))
		self.assertEqual(tasse[0]["tax_amount"], -16.0)

	def test_documento_senza_blocchi_non_cambia_nulla(self):
		self.assertEqual(self._integra(_doc_parcella(dati_ritenuta=None, dati_cassa_previdenziale=None)), ([], [], {}))

	def test_impostazione_mancante_ferma_con_il_campo(self):
		with patch.object(frappe, "get_cached_value", return_value=None), self.assertRaisesRegex(
			frappe.ValidationError, "custom_item_cassa_previdenziale"
		):
			self._integra(_doc_parcella())


class TestScadenze(UnitTestCase):
	def setUp(self):
		super().setUp()
		finto = patch.object(extra, "modo_di_pagamento", side_effect=lambda codice: {"MP05": "Bonifico Bancario"}.get(codice))
		finto.start()
		self.addCleanup(finto.stop)

	def test_rata_unica_al_lordo_della_ritenuta_diventa_il_netto(self):
		pagamento = _pagamento([{"modalita_pagamento": "MP05", "data_riferimento_termini_pagamento": "2026-05-14", "giorni_termini_pagamento": 0, "importo_pagamento": 101.50}])
		righe = extra.scadenze(pagamento, "2026-05-14", 85.50, 101.50)
		self.assertEqual(len(righe), 1)
		self.assertEqual((str(righe[0]["due_date"]), righe[0]["payment_amount"], righe[0]["mode_of_payment"]), ("2026-05-14", 85.5, "Bonifico Bancario"))
		self.assertEqual(righe[0]["invoice_portion"], 100.0)

	def test_due_rate_con_scadenza_esplicita_e_giorni(self):
		pagamento = _pagamento(
			[
				{"modalita_pagamento": "MP05", "data_scadenza_pagamento": "2026-06-30", "importo_pagamento": 60.00},
				{"modalita_pagamento": "MP08", "data_riferimento_termini_pagamento": "2026-05-14", "giorni_termini_pagamento": 60, "importo_pagamento": 40.00},
			],
			condizioni="TP01",
		)
		righe = extra.scadenze(pagamento, "2026-05-14", 100.0, 100.0)
		self.assertEqual([str(r["due_date"]) for r in righe], ["2026-06-30", "2026-07-13"])
		self.assertEqual([r["payment_amount"] for r in righe], [60.0, 40.0])
		self.assertIsNone(righe[1]["mode_of_payment"])  # nessun Mode of Payment col codice: resta nella descrizione
		self.assertEqual(righe[1]["description"], "MP08")

	def test_rate_scalate_al_netto_quadrano_sull_ultima(self):
		pagamento = _pagamento([{"modalita_pagamento": "MP05", "data_scadenza_pagamento": "2026-06-30", "importo_pagamento": 50.75}, {"modalita_pagamento": "MP05", "data_scadenza_pagamento": "2026-07-31", "importo_pagamento": 50.75}])
		righe = extra.scadenze(pagamento, "2026-05-14", 85.50, 101.50)
		self.assertEqual(round(sum(r["payment_amount"] for r in righe), 2), 85.5)

	def test_somma_incoerente_ferma(self):
		pagamento = _pagamento([{"modalita_pagamento": "MP05", "data_scadenza_pagamento": "2026-06-30", "importo_pagamento": 70.00}])
		with self.assertRaisesRegex(frappe.ValidationError, "sommano 70.00"):
			extra.scadenze(pagamento, "2026-05-14", 85.50, 101.50)

	def test_rate_a_zero_fermano(self):
		pagamento = _pagamento([{"modalita_pagamento": "MP05", "data_scadenza_pagamento": "2026-06-30", "importo_pagamento": 0}])
		with self.assertRaisesRegex(frappe.ValidationError, "sommano 0.00"):
			extra.scadenze(pagamento, "2026-05-14", 85.50, 101.50)

	def test_scadenza_prima_del_documento_ferma(self):
		pagamento = _pagamento([{"modalita_pagamento": "MP05", "data_scadenza_pagamento": "2026-05-01", "importo_pagamento": 85.50}])
		with self.assertRaisesRegex(frappe.ValidationError, "precedente"):
			extra.scadenze(pagamento, "2026-05-14", 85.50, 101.50)

	def test_senza_dati_pagamento_nessuna_riga(self):
		self.assertEqual(extra.scadenze([], "2026-05-14", 85.50, 101.50), [])

	def test_iban(self):
		pagamento = _pagamento([{"modalita_pagamento": "MP05", "importo_pagamento": 85.50, "iban": "IT11E0843051151000000280365"}])
		self.assertEqual(extra.iban_fornitore(pagamento), "IT11E0843051151000000280365")
		self.assertIsNone(extra.iban_fornitore([]))


class TestModoDiPagamento(UnitTestCase):
	def test_codice_ambiguo_ferma(self):
		with patch.object(frappe, "get_all", return_value=["Credit Card", "Carta Prepagata"]), self.assertRaisesRegex(
			frappe.ValidationError, "MP08"
		):
			extra.modo_di_pagamento("MP08")

	def test_codice_senza_modo(self):
		with patch.object(frappe, "get_all", return_value=[]):
			self.assertIsNone(extra.modo_di_pagamento("MP12"))
		self.assertIsNone(extra.modo_di_pagamento(None))
