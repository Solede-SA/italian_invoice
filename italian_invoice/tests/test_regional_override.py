"""La copia di sales_invoice_validate in overrides/regional_italy.py segue l'originale di ERPNext.

L'override sostituisce la funzione di ERPNext (regional_overrides): se ERPNext la cambia, la copia
resta indietro in silenzio. È già successo con ERPNext 16.50 (numero SWIFT delle scadenze di
pagamento, fatture di apertura escluse). L'impronta qui sotto è quella dell'originale con cui la copia
è stata allineata: quando cambia, riallineare la copia (tranne il blocco SOLEDE) e aggiornarla.
"""

import hashlib
import inspect

from erpnext.regional.italy import utils
from frappe.tests import UnitTestCase

IMPRONTA_ORIGINALE_ALLINEATA = "609977fc932489bcc091afa0da3444249cd6ae8002e9953a9e6de96bab6ed2ec"


class TestRegionalOverride(UnitTestCase):
	def test_copia_allineata_all_originale_di_erpnext(self):
		impronta = hashlib.sha256(inspect.getsource(utils.sales_invoice_validate).encode()).hexdigest()
		self.assertEqual(
			impronta,
			IMPRONTA_ORIGINALE_ALLINEATA,
			"ERPNext ha cambiato erpnext.regional.italy.utils.sales_invoice_validate: riallineare la copia "
			"in italian_invoice/overrides/regional_italy.py (tranne il blocco SOLEDE) e aggiornare l'impronta.",
		)
