"""<Descrizione> di riga nell'XML: la descrizione della riga, ripulita per lo schema.

Bug di partenza: NCINV/26/00009 (24/10/2026) è uscita con «canone noleggio dae» e il riferimento alla
fattura stornata, scritto nella descrizione di riga, non è arrivato al Sistema di Interscambio.
"""

import frappe
from frappe.tests import UnitTestCase

from italian_invoice.utilities.fatture import xml_line_description


def _item(description, item_name="Canone Noleggio DAE"):
	return frappe._dict(description=description, item_name=item_name)


class TestDescrizioneRigaXml(UnitTestCase):
	def test_html_entita_e_a_capo_tolti(self):
		riga = _item("<div>Storno totale fattura&nbsp;SINV/26/00244<br>\n  del 23/10/2026</div>")
		self.assertEqual(xml_line_description(riga), "Storno totale fattura SINV/26/00244 del 23/10/2026")

	def test_descrizione_vuota_usa_il_nome_articolo_con_le_maiuscole(self):
		self.assertEqual(xml_line_description(_item("<p><br></p>")), "Canone Noleggio DAE")
		self.assertEqual(xml_line_description(_item(None)), "Canone Noleggio DAE")

	def test_caratteri_fuori_latin1_sostituiti_o_tolti(self):
		riga = _item("Canone “base” – 29,90 € l’anno… ✓")
		self.assertEqual(xml_line_description(riga), 'Canone "base" - 29,90 EUR l\'anno...')

	def test_minore_e_maggiore_codificati_e_commerciale_lasciata_al_render(self):
		self.assertEqual(xml_line_description(_item("Vite &amp; dado &lt;M6&gt;")), "Vite & dado &lt;M6&gt;")

	def test_massimo_mille_caratteri(self):
		self.assertEqual(len(xml_line_description(_item("x" * 1200))), 1000)
