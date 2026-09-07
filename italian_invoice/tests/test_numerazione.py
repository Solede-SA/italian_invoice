"""Numero fattura assegnato alla conferma (Company.custom_numero_alla_conferma)."""

import frappe
from erpnext.accounts.utils import get_fiscal_years
from frappe.model.dynamic_links import invalidate_distinct_link_doctypes
from frappe.model.naming import NamingSeries
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, today

from italian_invoice.crud_events.sales_invoice.numerazione import PREFISSO_BOZZA
from italian_invoice.tests.fixtures import TEST_COMPANY as COMPANY, ensure_test_company
from italian_invoice.utilities.fatture import get_unamended_name, get_xml

CUSTOMER = "_Test Numerazione Cliente"
ITEM = "_Test Numerazione Servizio"


def _anagrafica(doctype, nome, **campi):
	if not frappe.db.exists(doctype, nome):
		frappe.get_doc({"doctype": doctype, **campi}).insert(ignore_permissions=True)


def _crea_anagrafiche():
	ensure_test_company()
	if not get_fiscal_years(today(), company=COMPANY, raise_on_missing=False):
		anno = today()[:4]
		_anagrafica(
			"Fiscal Year", f"_Test Numerazione {anno}",
			year=f"_Test Numerazione {anno}", year_start_date=f"{anno}-01-01", year_end_date=f"{anno}-12-31",
			companies=[{"company": COMPANY}],
		)
	_anagrafica("Customer Group", "_Test Numerazione Gruppo Clienti", customer_group_name="_Test Numerazione Gruppo Clienti", parent_customer_group="All Customer Groups")
	_anagrafica("Territory", "_Test Numerazione Territorio", territory_name="_Test Numerazione Territorio", parent_territory="All Territories")
	_anagrafica("Item Group", "_Test Numerazione Gruppo Articoli", item_group_name="_Test Numerazione Gruppo Articoli", parent_item_group="All Item Groups")
	_anagrafica(
		"Customer", {"customer_name": CUSTOMER},
		customer_name=CUSTOMER, customer_type="Company",
		customer_group="_Test Numerazione Gruppo Clienti", territory="_Test Numerazione Territorio",
	)
	_anagrafica(
		"Item", ITEM,
		item_code=ITEM, item_name=ITEM, item_group="_Test Numerazione Gruppo Articoli", stock_uom="Nos", is_stock_item=0,
	)


def _serie_corrente(naming_series="SINV/.YY./"):
	serie = NamingSeries(naming_series)
	return serie.get_prefix(), serie.get_current_value()


def _prossimo(naming_series="SINV/.YY./"):
	prefisso, corrente = _serie_corrente(naming_series)
	return f"{prefisso}{corrente + 1:05d}"


class TestNumerazione(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		_crea_anagrafiche()
		cls.customer = frappe.db.get_value("Customer", {"customer_name": CUSTOMER}, "name")

	def setUp(self):
		self._flag(1)

	def _flag(self, valore):
		frappe.db.set_value("Company", COMPANY, "custom_numero_alla_conferma", valore)

	def _bozza(self, **valori):
		qty = -1 if valori.get("is_return") else 1
		doc = frappe.get_doc({
			"doctype": "Sales Invoice",
			"company": COMPANY,
			"customer": self.customer,
			"currency": "EUR",
			"items": [{"item_code": ITEM, "qty": qty, "rate": 100}],
			**valori,
		})
		return doc.insert(ignore_permissions=True)

	def test_bozza_nome_provvisorio_serie_intatta(self):
		prefisso, prima = _serie_corrente()
		bozza = self._bozza()
		self.assertTrue(bozza.name.startswith(PREFISSO_BOZZA + prefisso), bozza.name)
		self.assertEqual(_serie_corrente()[1], prima)

	def test_submit_assegna_numero_e_rinomina_tutto(self):
		bozza = self._bozza()
		vecchio = bozza.name
		bozza.add_comment("Comment", "nota sulla bozza")
		allegato = frappe.get_doc({
			"doctype": "File", "file_name": "nota.txt", "content": "x", "is_private": 1,
			"attached_to_doctype": "Sales Invoice", "attached_to_name": vecchio,
		}).insert(ignore_permissions=True)
		# La mappa dei link dinamici è in cache per 12 ore: senza reset il Comment non verrebbe rinominato.
		invalidate_distinct_link_doctypes("Comment", "reference_doctype", "Sales Invoice")
		atteso = _prossimo()

		bozza.submit()

		self.assertEqual(bozza.name, atteso)
		self.assertEqual(bozza.localname, vecchio)
		self.assertFalse(frappe.db.exists("Sales Invoice", vecchio))
		self.assertFalse(frappe.db.exists("Sales Invoice Item", {"parent": vecchio}))
		self.assertTrue(frappe.db.exists("Sales Invoice Item", {"parent": atteso}))
		self.assertEqual(frappe.db.get_value("File", allegato.name, "attached_to_name"), atteso)
		self.assertTrue(frappe.db.exists("GL Entry", {"voucher_no": atteso, "is_cancelled": 0}))
		commenti = frappe.get_all(
			"Comment", filters={"reference_doctype": "Sales Invoice", "reference_name": atteso}, pluck="content"
		)
		self.assertIn("nota sulla bozza", commenti)
		self.assertTrue(any(c.startswith("Numerata") for c in commenti), commenti)

	def _bozza_di_ieri(self):
		"""Bozza creata ieri (posting, scadenza e riga payment_schedule) e confermata oggi."""
		bozza = self._bozza()
		ieri = add_days(today(), -1)
		bozza.db_set({"posting_date": ieri, "due_date": ieri})
		bozza.payment_schedule[0].db_set("due_date", ieri)
		return bozza

	def test_bozza_confermata_giorni_dopo_scadenza_segue_la_data(self):
		bozza = self._bozza_di_ieri()
		bozza.submit()
		self.assertEqual(getdate(bozza.posting_date), getdate(today()))
		self.assertEqual(getdate(bozza.due_date), getdate(today()))
		self.assertEqual(getdate(bozza.payment_schedule[0].due_date), getdate(today()))

	def test_fattura_gia_numerata_conserva_validazione_scadenza(self):
		self._flag(0)
		fattura = self._bozza_di_ieri()
		with self.assertRaisesRegex(frappe.ValidationError, "Due Date"):
			fattura.submit()

	def test_bozza_eliminata_non_lascia_buchi(self):
		prima_bozza = self._bozza()
		seconda = self._bozza()
		atteso = _prossimo()
		prima_bozza.delete()
		seconda.submit()
		self.assertEqual(seconda.name, atteso)

	def test_nota_di_credito(self):
		nota = self._bozza(is_return=1)
		self.assertTrue(nota.name.startswith(PREFISSO_BOZZA + "NCINV/"), nota.name)
		atteso = _prossimo("NCINV/.YY./")
		nota.submit()
		self.assertEqual(nota.name, atteso)

	def test_flag_spento_numero_alla_creazione(self):
		self._flag(0)
		atteso = _prossimo()
		self.assertEqual(self._bozza().name, atteso)

	def test_emenda_conserva_il_numero(self):
		fattura = self._bozza()
		fattura.submit()
		fattura.cancel()
		emendata = frappe.copy_doc(fattura)
		emendata.amended_from = fattura.name
		emendata.docstatus = 0
		emendata.insert(ignore_permissions=True)
		self.assertEqual(emendata.name, f"{fattura.name}-1")
		self.assertEqual(get_unamended_name(emendata), fattura.name)
		emendata.submit()
		self.assertEqual(emendata.name, f"{fattura.name}-1")

	def test_invio_rifiuta_le_bozze(self):
		bozza = self._bozza()
		self.assertRaisesRegex(frappe.ValidationError, "confermata", get_xml, bozza.name, "Sales Invoice")
