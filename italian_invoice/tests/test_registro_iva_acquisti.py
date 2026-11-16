"""Righe IVA delle fatture ricevute e Registro IVA Acquisti.

Bug di partenza (16/11/2026): ERPNext azzera l'aliquota delle righe a importo fisso, quindi il registro mostrava
imposta 0; il conto IVA si sceglieva per aliquota e al 10% finiva su un conto delle vendite; «Non Detraibile»
contava ritenute e debito dell'inversione contabile; le note di credito restavano fuori.
"""

from collections import defaultdict
from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.italian_invoice.report.registro_iva_acquisti.registro_iva_acquisti import add_taxes
from italian_invoice.patches.v1_7.iva_acquisti_conto_e_aliquota import abbina
from italian_invoice.utilities.fatture_passive import prepare_invoice_taxes

CONTO_IVA = "35.01.01 - IVA su acquisti - X"


def _tax(tax_amount, aliquota=0, imponibile=0, **campi):
	return frappe._dict(
		{
			"description": "IVA", "add_deduct_tax": "Add", "charge_type": "Actual", "rate": 0, "tax_amount": tax_amount,
			"aliquota": aliquota, "imponibile": imponibile, "account_type": "Tax", **campi,
		}
	)


def _columns(taxes):
	row = defaultdict(float)
	missing = add_taxes(row, taxes)
	return dict(row), missing


class TestRegistroIvaAcquisti(UnitTestCase):
	def test_righe_importate_per_aliquota(self):
		self.assertEqual(
			_columns([_tax(22, 22, 100), _tax(5, 10, 50)]),
			({"imponibile_22": 100, "imposta_22": 22, "imponibile_10": 50, "imposta_10": 5}, 0),
		)

	def test_iva_sul_conto_del_costo_o_del_cespite_e_indetraibile(self):
		self.assertEqual(
			_columns([_tax(7.66, 22, 34.84, account_type=""), _tax(57.62, 22, 261.89, account_type="Fixed Asset")]),
			({"imponibile_22": 296.73, "indetraibile": 65.28}, 0),
		)

	def test_ritenuta_e_debito_inversione_contabile_non_sono_iva_a_credito(self):
		self.assertEqual(
			_columns([
				_tax(220, 22, 1000),
				_tax(200, add_deduct_tax="Deduct", description="Ritenuta d'acconto 20%"),
				_tax(220, add_deduct_tax="Deduct"),
			]),
			({"imponibile_22": 1000, "imposta_22": 220}, 0),
		)

	def test_nota_di_credito_con_il_suo_segno(self):
		self.assertEqual(_columns([_tax(-22, 22, -100)]), ({"imponibile_22": -100, "imposta_22": -22}, 0))

	def test_natura_esente_o_non_imponibile(self):
		self.assertEqual(
			_columns([_tax(0, 0, 80, description="Esente art. 10"), _tax(0, 0, 20, description="Natura N3.1")]),
			({"esente": 80, "non_imponibile": 20}, 0),
		)

	def test_riga_iva_senza_aliquota_da_completare_il_bollo_non_conta(self):
		self.assertEqual(
			_columns([_tax(11), _tax(2, account_type="", description="Imposta di bollo")]),
			({}, 1),
		)

	def test_riga_calcolata_da_erpnext_usa_la_sua_aliquota(self):
		self.assertEqual(
			_columns([_tax(22, charge_type="On Net Total", rate=22)]),
			({"imponibile_22": 100, "imposta_22": 22}, 0),
		)


class TestRigheIva(UnitTestCase):
	def setUp(self):
		super().setUp()
		finto = patch.object(frappe, "get_cached_value", return_value=CONTO_IVA)
		finto.start()
		self.addCleanup(finto.stop)

	def test_ogni_aliquota_sul_conto_della_societa_con_aliquota_e_imponibile(self):
		taxes = prepare_invoice_taxes(
			[
				{"aliquota_iva": "22.00", "imponibile_importo": "100.00", "imposta": "22.00"},
				{"aliquota_iva": "10.00", "imponibile_importo": "50.00", "imposta": "5.00", "esigibilita_iva": "S"},
				{"aliquota_iva": "0.00", "natura": "N2.2", "imponibile_importo": "30.00", "imposta": "0.00"},
				{"aliquota_iva": "0.00", "imponibile_importo": "0.00", "imposta": "0.00"},
			],
			"Società di prova",
		)
		self.assertEqual(
			[(t["account_head"], t["tax_amount"], t["custom_aliquota_iva"], t["custom_imponibile"], t["description"]) for t in taxes],
			[
				(CONTO_IVA, "22.00", 22.0, "100.00", "IVA 22.0%"),
				(CONTO_IVA, "5.00", 10.0, "50.00", "IVA 10.0% (Split Payment)"),
				(CONTO_IVA, "0.00", 0.0, "30.00", "Natura N2.2"),
			],
		)

	def test_inversione_contabile_credito_aggiunto_debito_tolto(self):
		taxes = prepare_invoice_taxes([{"aliquota_iva": "0.00", "natura": "N6.3", "imponibile_importo": "100.00", "imposta": "0.00"}], "Società di prova")
		self.assertEqual(
			[(t["add_deduct_tax"], t["tax_amount"], t.get("custom_aliquota_iva"), t.get("custom_imponibile")) for t in taxes],
			[("Add", 22.0, 22.0, 100.0), ("Deduct", 22.0, None, None)],
		)

	def test_nota_di_credito_inverte_i_segni(self):
		[tax] = prepare_invoice_taxes([{"aliquota_iva": "22.00", "imponibile_importo": "100.00", "imposta": "22.00"}], "Società di prova", is_return=True)
		self.assertEqual((tax["tax_amount"], tax["custom_imponibile"]), (-22.0, -100.0))

	def test_senza_conto_iva_della_societa_si_ferma(self):
		with patch.object(frappe, "get_cached_value", return_value=None):
			with self.assertRaisesRegex(frappe.ValidationError, "custom_account_iva_acquisti"):
				prepare_invoice_taxes([{"aliquota_iva": "22.00", "imponibile_importo": "100.00", "imposta": "22.00"}], "Società di prova")


class TestAbbinamento(UnitTestCase):
	def _riga(self, name, tax_amount, add_deduct_tax="Add", aliquota=0):
		return frappe._dict(name=name, tax_amount=tax_amount, add_deduct_tax=add_deduct_tax, custom_aliquota_iva=aliquota, custom_imponibile=0)

	def test_ogni_voce_sulla_riga_con_la_stessa_imposta(self):
		riepiloghi = [
			{"aliquota_iva": "10.00", "imponibile_importo": "50.00", "imposta": "5.00"},
			{"aliquota_iva": "22.00", "imponibile_importo": "100.00", "imposta": "22.00"},
			{"aliquota_iva": "0.00", "natura": "N4", "imponibile_importo": "30.00", "imposta": "0.00"},
		]
		righe = [self._riga("a", 22), self._riga("b", 5), self._riga("c", 0), self._riga("r", 20, add_deduct_tax="Deduct")]
		self.assertEqual(
			abbina(riepiloghi, righe, is_return=False),
			(
				{
					"b": {"custom_aliquota_iva": 10.0, "custom_imponibile": 50.0},
					"a": {"custom_aliquota_iva": 22.0, "custom_imponibile": 100.0},
					"c": {"custom_aliquota_iva": 0.0, "custom_imponibile": 30.0},
				},
				[],
			),
		)

	def test_righe_divise_a_mano_e_righe_gia_complete_restano_fuori(self):
		riepiloghi = [{"aliquota_iva": "22.00", "imponibile_importo": "100.00", "imposta": "22.00"}]
		self.assertEqual(abbina(riepiloghi, [self._riga("a", 11), self._riga("b", 11)], False), ({}, ["22% imposta 22.00"]))
		self.assertEqual(abbina(riepiloghi, [self._riga("a", 22, aliquota=22)], False), ({}, ["22% imposta 22.00"]))

	def test_nota_di_credito(self):
		riepiloghi = [{"aliquota_iva": "22.00", "imponibile_importo": "100.00", "imposta": "22.00"}]
		self.assertEqual(
			abbina(riepiloghi, [self._riga("a", -22)], is_return=True),
			({"a": {"custom_aliquota_iva": 22.0, "custom_imponibile": -100.0}}, []),
		)
