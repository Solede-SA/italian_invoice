"""Codici Natura generici N2, N3 e N6.

Dal 1° gennaio 2021 (specifiche tecniche 1.6.1) SdI scarta le fatture con Natura N2, N3 o N6
senza sottocodice (errore 00445). Lo schema XSD li ammette ancora, quindi la validazione XSD
da sola non basta. I record restano in «Motivo esenzione IVA» perché servono per importare
fatture passive emesse prima del 2021.
"""

NATURE_GENERICHE = frozenset({"N2", "N3", "N6"})


def codice_natura(valore):
	"""«N3-Non Imponibili» o «N3» → «N3»; vuoto → None."""
	if not valore:
		return None
	return str(valore).split("-", 1)[0].strip().upper() or None


def is_natura_generica(valore):
	return codice_natura(valore) in NATURE_GENERICHE


def righe_con_natura_generica(doc):
	"""Righe articolo e righe tasse con Natura generica, come testo per il messaggio."""
	righe = []
	for item in doc.get("items") or []:
		valore = item.get("custom_motivo_esenzione_iva")
		if is_natura_generica(valore):
			righe.append(f"articolo riga {item.idx} ({codice_natura(valore)})")
	for tax in doc.get("taxes") or []:
		for campo in ("custom_motivo_esenzione_iva", "tax_exemption_reason"):
			valore = tax.get(campo)
			if is_natura_generica(valore):
				righe.append(f"tasse riga {tax.idx} ({codice_natura(valore)})")
				break
	return righe
