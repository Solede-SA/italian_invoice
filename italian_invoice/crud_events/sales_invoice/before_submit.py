import frappe
from frappe import _

from italian_invoice.utilities import codice_destinatario
from italian_invoice.validation.natura import righe_con_natura_generica


def execute(doc, method=None):
	"""Validazione fail-loud dei campi obbligatori per la fattura elettronica (SDI).

	Eseguita al SUBMIT (non al save): una bozza può essere incompleta, ma una fattura
	sottomessa/trasmissibile a SDI deve avere indirizzo cliente, P.IVA/Codice Fiscale e —
	per le Pubbliche Amministrazioni — il Codice Destinatario (codice univoco IPA).

	Centralizzata qui: copre TUTTE le Sales Invoice del bench (garemed, daeok, manuali),
	così la regola fiscale è una sola e non duplicata per app.

	Vale solo per le società italiane: la fattura elettronica (SDI) è un obbligo
	italiano — le fatture di società estere (es. svizzere) non passano da SDI.
	"""
	problemi = controlli(doc)
	if problemi:
		frappe.throw(problemi[0])


def controlli(doc):
	"""Tutti i problemi che fermerebbero la conferma, in lista: chi esamina una bozza (l'agente contabile) li
	mostra insieme invece di scoprirli uno alla volta."""
	if frappe.get_cached_value("Company", doc.company, "country") != "Italy":
		return []
	problemi = []

	# Il Tipo di Documento (TD01, TD24, …) finisce nell'XML: obbligatorio al submit.
	# Enforcement qui e non con reqd sul Custom Field, che bloccherebbe anche le
	# fatture delle società estere (il metadato non distingue il paese).
	if not doc.custom_tipo_di_documento:
		problemi.append(_("Sales Invoice {0}: Tipo di Documento mancante, obbligatorio per la fattura elettronica.").format(doc.name))

	if not doc.customer_address:
		problemi.append(_("Sales Invoice {0}: indirizzo di fatturazione mancante, obbligatorio per la fattura elettronica.").format(doc.name))

	customer = frappe.db.get_value(
		"Customer", doc.customer,
		["tax_id", "fiscal_code", "custom_codice_univoco", "is_public_administration"],
		as_dict=True,
	)
	if not customer:
		return [*problemi, _("Sales Invoice {0}: cliente {1} non trovato.").format(doc.name, doc.customer)]

	# B2B: Partita IVA (tax_id). B2C / privati: Codice Fiscale (fiscal_code). Per la fattura
	# elettronica ne basta uno dei due — i privati non hanno P.IVA.
	if not (customer.tax_id or customer.fiscal_code or doc.get("tax_id")):
		problemi.append(_("Cliente {0}: Partita IVA / Codice Fiscale mancante, obbligatorio per la fattura elettronica.").format(doc.customer))

	if customer.is_public_administration and not customer.custom_codice_univoco:
		problemi.append(_("Cliente PA {0}: Codice Destinatario (codice univoco IPA) mancante, obbligatorio per fatturare alla Pubblica Amministrazione.").format(doc.customer))
	# Un codice presente ma fuori formato (una minuscola) passerebbe la conferma e fermerebbe l'XML all'invio.
	errore_codice = codice_destinatario.errore(doc.customer, customer.custom_codice_univoco, customer.is_public_administration)
	if errore_codice:
		problemi.append(errore_codice)

	# Natura generica (N2, N3, N6) senza sottocodice: dal 1/1/2021 SdI scarta la fattura (00445).
	righe = righe_con_natura_generica(doc)
	if righe:
		problemi.append(
			_("Natura IVA generica non più ammessa da SdI (scarto 00445): {0}. Usare il sottocodice (es. N2.1, N3.2, N6.3).").format(
				", ".join(righe)
			)
		)
	return problemi
