"""Numero fattura assegnato alla conferma (opzione per società).

Con `Company.custom_numero_alla_conferma` acceso le bozze ricevono un nome provvisorio
`BOZZA-<serie>` (contatore separato); il numero progressivo vero viene consumato solo al
submit, rinominando il documento. Le bozze eliminate non lasciano quindi buchi nella
numerazione trasmessa al Sistema di Interscambio e i numeri seguono l'ordine di conferma,
cioè l'ordine delle date.
"""

import frappe
from frappe import _
from frappe.model.naming import make_autoname, set_name_by_naming_series
from frappe.model.rename_doc import (
	get_link_fields,
	rename_dynamic_links,
	rename_parent_and_child,
	rename_versions,
	update_attachments,
)
from frappe.utils import getdate
from frappe.utils.global_search import delete_for_document

PREFISSO_BOZZA = "BOZZA-"


def autoname(doc, method=None):
	"""Hook `autoname`: gira dopo `before_naming` (serie già scelta) e solo per i documenti
	non emendati, perché Frappe assegna il suffisso -N prima di arrivare qui."""
	if not doc.company or not frappe.get_cached_value("Company", doc.company, "custom_numero_alla_conferma"):
		return
	doc.name = make_autoname(PREFISSO_BOZZA + doc.naming_series + ".#####", doc=doc)


def before_validate(doc, method=None):
	"""Bozza confermata in un giorno successivo: le scadenze seguono la data documento.

	ERPNext riporta posting_date a oggi ad ogni validate (set_posting_time=0), ma due_date e
	le righe payment_schedule restano al giorno della bozza → "Due Date cannot be before
	Posting Date" (es. pagamento Stripe riuscito al retry, conferma manuale dopo giorni).
	"""
	if not (doc.name or "").startswith(PREFISSO_BOZZA) or doc.get("set_posting_time"):
		return
	oggi = getdate()
	for riga in [doc, *doc.get("payment_schedule")]:
		if riga.due_date and getdate(riga.due_date) < oggi:
			riga.due_date = oggi


def before_submit(doc, method=None):
	"""Assegna il numero definitivo alla bozza provvisoria.

	Trigger sul nome e non sul flag: una bozza creata col flag acceso va numerata anche se
	nel frattempo lo si spegne; le bozze con numero vero non vengono toccate.
	"""
	if not doc.name.startswith(PREFISSO_BOZZA):
		return
	vecchio = doc.name
	# Stesso percorso del naming standard (lock FOR UPDATE su tabSeries: due conferme
	# simultanee ricevono numeri diversi); il documento in base dati si chiama ancora `vecchio`.
	set_name_by_naming_series(doc)
	_rinomina(doc, vecchio)


def _rinomina(doc, vecchio):
	"""Rinomina la riga `vecchio` nel nuovo `doc.name`: composizione di frappe.model.rename_doc
	senza i suoi effetti globali a ogni submit (frappe.clear_cache() dell'intero sito, rebuild
	della global search del DocType, msgprint)."""
	nuovo = doc.name
	if frappe.db.exists(doc.doctype, nuovo):
		frappe.throw(_("Esiste già una fattura {0}: numero non assegnabile.").format(nuovo))

	# La riga di global search col nome nuovo la scrive update_global_search dopo il salvataggio.
	delete_for_document(frappe._dict(doctype=doc.doctype, name=vecchio))
	rename_parent_and_child(doc.doctype, vecchio, nuovo, doc.meta)
	_aggiorna_campi_link(doc.doctype, vecchio, nuovo)
	rename_dynamic_links(doc.doctype, vecchio, nuovo)
	update_attachments(doc.doctype, vecchio, nuovo)
	rename_versions(doc.doctype, vecchio, nuovo)
	frappe.clear_document_cache(doc.doctype, vecchio)

	doc.set_parent_in_children()  # altrimenti update_children riscrive parent col nome vecchio
	# Frappe registra (doctype, nome) all'inizio del salvataggio: i db_set post-submit (status,
	# outstanding_amount) non toccano `modified` solo se ritrovano il nome corrente.
	frappe.flags.currently_saving.remove((doc.doctype, vecchio))
	frappe.flags.currently_saving.append((doc.doctype, nuovo))
	doc.localname = vecchio  # savedocs lo restituisce al client, che sposta il form sul nuovo nome
	doc.add_comment("Edit", _("Numerata: {0} → {1}").format(vecchio, nuovo))


def _aggiorna_campi_link(doctype, vecchio, nuovo):
	"""Come rename_doc.update_link_field_values, ma per documento: l'originale usa
	frappe.db.set_value con filtro a dict, che svuota la cache documenti dell'intero DocType
	con una scansione KEYS su Redis per ognuno dei ~20 campi Link verso Sales Invoice, a ogni
	submit, anche quando nessuna riga cambia."""
	for campo in get_link_fields(doctype):
		if campo["issingle"]:
			if frappe.db.get_single_value(campo["parent"], campo["fieldname"]) == vecchio:
				frappe.db.set_single_value(campo["parent"], campo["fieldname"], nuovo)
			continue
		for nome in frappe.get_all(campo["parent"], filters={campo["fieldname"]: vecchio}, pluck="name"):
			frappe.db.set_value(campo["parent"], nome, campo["fieldname"], nuovo, update_modified=False)
