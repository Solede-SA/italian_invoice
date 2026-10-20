"""Codici Natura generici N2, N3 e N6.

Dal 1° gennaio 2021 (specifiche tecniche 1.6.1) SdI scarta le fatture con Natura N2, N3 o N6
senza sottocodice (errore 00445). Lo schema XSD li ammette ancora, quindi la validazione XSD
da sola non basta. I record restano in «Motivo esenzione IVA» perché servono per importare
fatture passive emesse prima del 2021.

Si controlla solo custom_motivo_esenzione_iva: è il campo da cui il template prende la Natura.
Il vecchio Select tax_exemption_reason non finisce nell'XML e resta pieno sui documenti esistenti.
"""

NATURE_GENERICHE = frozenset({"N2", "N3", "N6"})


def righe_con_natura_generica(doc):
	"""Righe articolo e righe tasse con Natura generica, come testo per il messaggio."""
	righe = []
	for item in doc.get("items") or []:
		if item.get("custom_motivo_esenzione_iva") in NATURE_GENERICHE:
			righe.append(f"articolo riga {item.idx} ({item.custom_motivo_esenzione_iva})")
	for tax in doc.get("taxes") or []:
		if tax.get("custom_motivo_esenzione_iva") in NATURE_GENERICHE:
			righe.append(f"tasse riga {tax.idx} ({tax.custom_motivo_esenzione_iva})")
	return righe
