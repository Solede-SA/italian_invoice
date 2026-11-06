"""Il codice destinatario come lo vuole lo schema dell'XML (CodiceDestinatario): 7 caratteri fra lettere maiuscole
e cifre («0000000» per i privati), 6 per il codice IPA della Pubblica Amministrazione. Una sola regola per il
salvataggio del cliente, la conferma della fattura e l'agente contabile."""

import re

from frappe import _

FORMATO = {False: re.compile(r"^[A-Z0-9]{7}$"), True: re.compile(r"^[A-Z0-9]{6}$")}


def normalizza(codice):
	return (codice or "").strip().upper()


def errore(customer, codice, pubblica_amministrazione):
	"""Perché il codice del cliente non passerebbe lo schema, o None (il codice vuoto non è un errore di formato)."""
	if codice and not FORMATO[bool(pubblica_amministrazione)].match(codice):
		return _("Cliente {0}: codice destinatario «{1}» non valido (7 caratteri fra lettere maiuscole e cifre, 6 per la Pubblica Amministrazione; per i privati «0000000»).").format(customer, codice)
	return None
