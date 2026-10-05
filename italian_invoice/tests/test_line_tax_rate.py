"""AliquotaIVA e Natura di riga dai dettagli per articolo di ERPNext v16.

Bug di partenza: sulle autofatture TD17 la riga usciva a 0 (tax_rate della
Purchase Invoice Item mai compilato in v16) mentre il riepilogo diceva 22 →
scarti SdI 00443/00400/00422.
"""

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.utilities.fatture import (
	check_invisible_chars,
	set_line_exemption_reasons,
	set_line_tax_rates,
)


def _tax(name, rate, charge_type="On Net Total", add_deduct_tax="Add", **campi):
	return frappe._dict(name=name, rate=rate, charge_type=charge_type, add_deduct_tax=add_deduct_tax, **campi)


def _item(name, idx, tax_rate=0.0, **campi):
	return frappe._dict(name=name, idx=idx, item_code=f"ART-{idx}", tax_rate=tax_rate, **campi)


def _doc(taxes, details):
	return frappe._dict(
		taxes=taxes,
		item_wise_tax_details=[
			frappe._dict(item_row=item_row, tax_row=tax_row, rate=rate) for item_row, tax_row, rate in details
		],
	)


class TestLineTaxRate(UnitTestCase):
	def test_autofattura_reverse_charge_prende_la_riga_add(self):
		# TD17 "IVA acquisti CEE al 22%": +22 Add e -22 Deduct; tax_rate salvato a 0
		doc = _doc(
			[_tax("t1", 22), _tax("t2", 22, add_deduct_tax="Deduct")],
			[("i1", "t1", 22), ("i1", "t2", 22)],
		)
		items = [_item("i1", 1)]
		set_line_tax_rates(doc, items)
		self.assertEqual(items[0].tax_rate, 22)

	def test_aliquote_diverse_per_riga(self):
		# Righe tassa per aliquota, Item Tax Template azzera le altre
		doc = _doc(
			[_tax("t22", 22), _tax("t10", 10)],
			[("i1", "t22", 22), ("i1", "t10", 0), ("i2", "t22", 0), ("i2", "t10", 10)],
		)
		items = [_item("i1", 1), _item("i2", 2)]
		set_line_tax_rates(doc, items)
		self.assertEqual([item.tax_rate for item in items], [22, 10])

	def test_bollo_ignorato(self):
		doc = _doc([_tax("t1", 22), _tax("bollo", 2, charge_type="Actual")], [("i1", "t1", 22), ("i1", "bollo", 2)])
		items = [_item("i1", 1)]
		set_line_tax_rates(doc, items)
		self.assertEqual(items[0].tax_rate, 22)

	def test_due_aliquote_sulla_stessa_riga_errore(self):
		doc = _doc([_tax("t1", 22), _tax("t2", 10)], [("i1", "t1", 22), ("i1", "t2", 10)])
		with self.assertRaises(frappe.ValidationError):
			set_line_tax_rates(doc, [_item("i1", 1)])

	def test_riga_esente_prende_la_natura_del_riepilogo(self):
		doc = _doc([_tax("t1", 0)], [("i1", "t1", 0)])
		items = [_item("i1", 1, tax_rate=22)]
		set_line_tax_rates(doc, items)
		set_line_exemption_reasons(items, {"0.0": {"tax_exemption_reason": "N3.5"}})
		self.assertEqual(items[0].tax_rate, 0)
		self.assertEqual(items[0].custom_motivo_esenzione_iva, "N3.5")

	def test_natura_della_riga_non_sovrascritta(self):
		items = [_item("i1", 1, custom_motivo_esenzione_iva="N2.2")]
		set_line_exemption_reasons(items, {"0.0": {"tax_exemption_reason": "N3.5"}})
		self.assertEqual(items[0].custom_motivo_esenzione_iva, "N2.2")

	def test_riga_esente_senza_natura_errore(self):
		with self.assertRaises(frappe.ValidationError):
			set_line_exemption_reasons([_item("i1", 1)], {"0.0": {"tax_exemption_reason": None}})

	def test_partita_iva_con_trattino_morbido_errore(self):
		supplier = frappe.new_doc("Supplier")
		supplier.tax_id = "CHE­148775838"
		with self.assertRaises(frappe.ValidationError):
			check_invisible_chars(supplier)

		supplier.tax_id = "CHE148775838"
		check_invisible_chars(supplier)
