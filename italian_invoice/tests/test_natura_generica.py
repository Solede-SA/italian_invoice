"""Natura N2, N3 e N6 senza sottocodice → scarto SdI 00445 (dal 1/1/2021)."""

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.validation.natura import righe_con_natura_generica


def _doc(items=(), taxes=()):
	return frappe._dict(
		items=[frappe._dict(idx=i, **r) for i, r in enumerate(items, 1)],
		taxes=[frappe._dict(idx=i, **r) for i, r in enumerate(taxes, 1)],
	)


class TestNaturaGenerica(UnitTestCase):
	def test_natura_generica_bloccata(self):
		doc = _doc(
			items=[{"custom_motivo_esenzione_iva": "N3.2"}, {"custom_motivo_esenzione_iva": "N3"}],
			taxes=[{"custom_motivo_esenzione_iva": "N6"}],
		)
		self.assertEqual(righe_con_natura_generica(doc), ["articolo riga 2 (N3)", "tasse riga 1 (N6)"])

	def test_sottocodici_e_altri_codici_ammessi(self):
		for natura in ("N1", "N2.1", "N3.5", "N4", "N5", "N6.3", "N7", "", None):
			doc = _doc(items=[{"custom_motivo_esenzione_iva": natura}], taxes=[{"custom_motivo_esenzione_iva": natura}])
			self.assertEqual(righe_con_natura_generica(doc), [], natura)

	def test_vecchio_campo_ignorato(self):
		# Documenti esistenti: il Select nascosto tax_exemption_reason resta pieno ma non va nell'XML.
		for motivo in ("N3.5", "", None):
			doc = _doc(taxes=[{"tax_exemption_reason": "N6-Inversione Contabile", "custom_motivo_esenzione_iva": motivo}])
			self.assertEqual(righe_con_natura_generica(doc), [], motivo)
