"""
Validatore XML per fatture elettroniche italiane
"""

import logging
import re
from typing import Dict, Tuple

import frappe
import xmlschema
from lxml import etree

logger = logging.getLogger("italian_invoice.validation")


class XMLInvoiceValidator:
	"""Validatore per fatture elettroniche con gestione errori migliorata"""

	def __init__(self):
		self.xsd_path = frappe.get_app_path("italian_invoice", "utilities/schema_vfpr12.xsd")
		self.schema = None
		self.errors = []

	def validate(self, xml_content: str, doc=None) -> tuple[bool, dict]:
		"""
		Valida XML fattura con report dettagliato

		Args:
		    xml_content: Contenuto XML da validare
		    doc: Documento Frappe opzionale per contesto

		Returns:
		    Tuple (is_valid, validation_report)
		"""
		self.errors = []

		# Reset logger
		logger.info(f"Inizio validazione fattura {doc.name if doc else 'XML'}")

		# Validazione struttura XML base
		root = self._validate_xml_structure(xml_content)
		if root is None:
			return False, self._create_report()

		# Validazione XSD
		if not self._validate_xsd_schema(xml_content):
			return False, self._create_report()

		# Natura generica N2/N3/N6 (scarto SdI 00445)
		self._validate_natura(root)

		# Crea report finale
		is_valid = len(self.errors) == 0
		report = self._create_report()

		if is_valid:
			logger.info("Validazione completata con successo")
		else:
			logger.error(f"Validazione fallita con {len(self.errors)} errori")

		return is_valid, report

	def _validate_xml_structure(self, xml_content: str):
		"""Valida struttura XML base: restituisce la radice, None se l'XML non è ben formato"""
		try:
			root = etree.fromstring(xml_content.encode("utf-8"))
			logger.debug("Struttura XML valida")
			return root
		except etree.XMLSyntaxError as e:
			line_no = e.lineno if hasattr(e, "lineno") else 0
			self.errors.append(
				{
					"type": "XML_SYNTAX",
					"severity": "critical",
					"message": "Errore sintassi XML",
					"details": str(e),
					"line": line_no,
					"field": None,
					"suggestion": "Verifica che il file XML sia ben formato",
				}
			)
			return None

	def _validate_xsd_schema(self, xml_content: str) -> bool:
		"""Valida contro schema XSD"""
		try:
			# Carica schema se non già caricato
			if not self.schema:
				self.schema = xmlschema.XMLSchema(self.xsd_path)

			# Valida
			self.schema.validate(xml_content)
			logger.debug("Validazione XSD superata")
			return True

		except xmlschema.XMLSchemaException as e:
			self._parse_xsd_error(e)
			return False
		except Exception as e:
			self.errors.append(
				{
					"type": "XSD_VALIDATION",
					"severity": "critical",
					"message": "Errore validazione XSD",
					"details": str(e),
					"line": None,
					"field": None,
					"suggestion": "Contatta il supporto tecnico",
				}
			)
			return False

	def _parse_xsd_error(self, error: xmlschema.XMLSchemaException):
		"""Interpreta errore XSD in formato user-friendly mantenendo dettagli"""
		error_str = str(error)

		# Estrai il path completo se disponibile
		path_match = re.search(r"Path: (.*?)(?:\n|$)", error_str)
		xml_path = path_match.group(1) if path_match else None

		# Approccio generico: estrai valore, campo e path direttamente dall'errore
		# Estrai valore problematico
		value_match = re.search(r"failed validating '(.*?)'", error_str)
		if not value_match:
			value_match = re.search(r"'(.*?)' is not accepted", error_str)
			if not value_match:
				value_match = re.search(r"'(.*?)' is not valid", error_str)
		value = value_match.group(1) if value_match else None

		# Costruisci messaggio generico ma informativo
		if xml_path:
			# Pulisci il path
			path_parts = xml_path.split("/")
			clean_parts = []
			for p in path_parts:
				if p:
					# Rimuovi namespace {http://...}
					p = re.sub(r"\{.*?\}", "", p)
					# Rimuovi prefisso p:
					p = re.sub(r"^\w+:", "", p)
					clean_parts.append(p)

			# Path leggibile
			readable_path = " → ".join(clean_parts) if clean_parts else xml_path

			# Prendi l'ultimo elemento come nome campo
			field_name = clean_parts[-1] if clean_parts else None

			if value and field_name:
				message = f'Il valore "{value}" non rispetta il formato richiesto nel campo {field_name} (percorso: {readable_path})'
			elif field_name:
				message = f"Errore nel campo {field_name} (percorso: {readable_path})"
			elif value:
				message = f'Il valore "{value}" non è valido (percorso: {readable_path})'
			else:
				message = f"Errore di validazione (percorso: {readable_path})"
		else:
			# Senza path
			if value:
				message = f'Il valore "{value}" non è valido'
			else:
				# Mantieni almeno parte dell'errore originale
				message = (
					f"Errore validazione: {error_str[:150]}..."
					if len(error_str) > 150
					else f"Errore validazione: {error_str}"
				)

		# Suggerimento generico basato sul contenuto dell'errore
		suggestion = "Verifica il formato secondo le specifiche FatturaPA"
		if "pattern" in error_str.lower():
			suggestion = "Verifica che il valore rispetti il formato richiesto"
		elif "missing" in error_str.lower():
			suggestion = "Aggiungi i campi obbligatori mancanti"
		elif "not expected" in error_str.lower():
			suggestion = "Rimuovi o correggi gli elementi non previsti"

		self.errors.append(
			{
				"type": "XSD_VALIDATION",
				"severity": "error",
				"message": message,
				"details": error_str,
				"line": getattr(error, "sourceline", None),
				"field": field_name if xml_path else None,
				"path": xml_path,
				"suggestion": suggestion,
			}
		)

	def _validate_natura(self, root):
		"""N2, N3 e N6 senza sottocodice: l'XSD li accetta, SdI li scarta (00445)"""
		from italian_invoice.validation.natura import NATURE_GENERICHE

		# Nel tracciato FatturaPA solo la radice ha il namespace: gli elementi figli no.
		for elem in root.xpath("//*[local-name()='Natura']"):
			natura = (elem.text or "").strip()
			if natura in NATURE_GENERICHE:
				self.errors.append(
					{
						"type": "BUSINESS_RULE",
						"severity": "error",
						"message": f"Natura {natura} generica: dal 1/1/2021 SdI scarta la fattura (errore 00445)",
						"field": "Natura",
						"path": elem.getparent().tag.split("}")[-1],
						"suggestion": "Usare il sottocodice (N2.1, N2.2, N3.1-N3.6, N6.1-N6.9) nel Motivo esenzione IVA",
					}
				)

	def _create_report(self) -> dict:
		"""Crea report di validazione"""
		return {
			"valid": len(self.errors) == 0,
			"errors": self.errors,
			"error_count": len(self.errors),
			"summary": self._create_summary(),
		}

	def _create_summary(self) -> str:
		"""Crea sommario testuale degli errori"""
		if not self.errors:
			return "✅ Validazione completata con successo"

		summary = [f"❌ {len(self.errors)} errori trovati:"]
		for err in self.errors[:3]:  # Primi 3 errori
			summary.append(f"  • {err['message']}")
		if len(self.errors) > 3:
			summary.append(f"  • ...e altri {len(self.errors) - 3} errori")

		return "\n".join(summary)
