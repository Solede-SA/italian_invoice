"""
Provider Manuale per test e sviluppo
Non richiede servizi esterni, salva tutto localmente
"""

import json
import os
import uuid as uuid_lib
from datetime import datetime

import frappe

from italian_invoice.providers.base import SDIProvider


class ManualProvider(SDIProvider):
	"""Provider manuale per test e sviluppo senza servizi esterni"""

	def __init__(self):
		self.storage_path = frappe.get_site_path("private", "files", "sdi_manual")
		# Crea directory se non esiste
		if not os.path.exists(self.storage_path):
			os.makedirs(self.storage_path)

	def send_invoice(self, xml_content: str, doc, company) -> dict:
		"""
		Simula invio fattura salvando XML localmente

		Args:
		    xml_content: XML della fattura
		    doc: Documento fattura
		    company: Documento Company

		Returns:
		    dict: Risultato simulato con uuid generato
		"""
		try:
			# Genera UUID fittizio
			uuid = str(uuid_lib.uuid4())

			# Salva XML su file
			filename = f"{doc.doctype}_{doc.name}_{uuid}.xml"
			filepath = os.path.join(self.storage_path, filename)

			with open(filepath, "w", encoding="utf-8") as f:
				f.write(xml_content)

			# Crea transazione SDI
			transazione_sdi = frappe.new_doc("Transazione SDI")
			transazione_sdi.tipo_fattura = doc.doctype
			transazione_sdi.fattura = doc.name
			transazione_sdi.stato_invio = "Inviata (Test)"
			transazione_sdi.uuid = uuid
			transazione_sdi.insert()

			# Aggiorna documento
			doc.custom_transazione_sdi = transazione_sdi.name
			doc.save()

			# Log per debug
			frappe.msgprint(
				f"Fattura salvata localmente: {filename}",
				title="Provider Manuale",
				indicator="green",
			)

			return {
				"success": True,
				"uuid": uuid,
				"message": f"Fattura salvata localmente con UUID: {uuid}",
				"file_path": filepath,
			}

		except Exception as e:
			frappe.log_error(f"Errore provider manuale: {str(e)}", "Manual Provider Error")
			return {
				"success": False,
				"message": f"Errore salvataggio: {str(e)}",
			}

	def download_invoice(self, uuid: str, format: str, company) -> bytes:
		"""
		Recupera fattura salvata localmente

		Args:
		    uuid: UUID fattura
		    format: Formato richiesto
		    company: Documento Company

		Returns:
		    bytes: Contenuto file
		"""
		try:
			# Cerca file con UUID
			for filename in os.listdir(self.storage_path):
				if uuid in filename:
					filepath = os.path.join(self.storage_path, filename)

					# Se richiesto PDF, ritorna messaggio placeholder
					if format.lower() == "pdf":
						return b"PDF generation not available in manual mode"

					# Ritorna XML
					with open(filepath, "rb") as f:
						return f.read()

			frappe.throw(f"File con UUID {uuid} non trovato")

		except Exception as e:
			frappe.log_error(f"Errore download manuale: {str(e)}", "Manual Provider Error")
			frappe.throw(f"Errore download: {str(e)}")

	def get_invoice_status(self, uuid: str, company) -> dict:
		"""
		Ritorna stato simulato

		Args:
		    uuid: UUID fattura
		    company: Documento Company

		Returns:
		    dict: Stato simulato
		"""
		# Cerca transazione
		transazioni = frappe.get_list(
			"Transazione SDI", filters={"uuid": uuid}, fields=["stato_invio", "name"]
		)

		if transazioni:
			return {
				"uuid": uuid,
				"stato": transazioni[0]["stato_invio"],
				"data_aggiornamento": datetime.now().isoformat(),
				"provider": "Manual",
			}

		return {"error": f"Transazione con UUID {uuid} non trovata"}

	def handle_notification(self, notification_data: dict) -> dict:
		"""
		Simula gestione notifica

		Args:
		    notification_data: Dati notifica

		Returns:
		    dict: Risultato elaborazione
		"""
		try:
			# Log notifica per debug
			log_file = os.path.join(self.storage_path, "notifications.log")
			with open(log_file, "a", encoding="utf-8") as f:
				f.write(f"\n--- {datetime.now()} ---\n")
				f.write(json.dumps(notification_data, indent=2))
				f.write("\n")

			return {
				"success": True,
				"message": "Notifica registrata nel log locale",
			}

		except Exception as e:
			return {
				"success": False,
				"message": f"Errore registrazione notifica: {str(e)}",
			}

	def configure_webhooks(self, company) -> dict:
		"""
		Simula configurazione webhook

		Args:
		    company: Documento Company

		Returns:
		    dict: Risultato configurazione
		"""
		# In modalità manuale non servono webhook reali
		config = {
			"company": company.name,
			"webhooks": "Non richiesti in modalità manuale",
			"timestamp": datetime.now().isoformat(),
		}

		# Salva configurazione
		config_file = os.path.join(self.storage_path, f"config_{company.name}.json")
		with open(config_file, "w", encoding="utf-8") as f:
			json.dump(config, f, indent=2)

		frappe.msgprint(
			"Configurazione webhook simulata salvata",
			title="Provider Manuale",
			indicator="blue",
		)

		return config

	def handle_webhook(self, endpoint: str, data: dict) -> dict:
		"""
		Gestisce webhook simulati

		Args:
		    endpoint: Nome endpoint
		    data: Dati webhook

		Returns:
		    dict: Risultato elaborazione
		"""
		try:
			# Log webhook per debug
			webhook_log = os.path.join(self.storage_path, f"webhook_{endpoint}.log")
			with open(webhook_log, "a", encoding="utf-8") as f:
				f.write(f"\n--- {datetime.now()} ---\n")
				f.write(f"Endpoint: {endpoint}\n")
				f.write(json.dumps(data, indent=2))
				f.write("\n")

			# Simula diverse risposte in base all'endpoint
			if endpoint == "supplier_invoice":
				return self._simulate_supplier_invoice(data)
			elif endpoint == "customer_notification":
				return self._simulate_customer_notification(data)
			else:
				return {
					"success": True,
					"message": f"Webhook {endpoint} registrato nel log",
				}

		except Exception as e:
			return {
				"success": False,
				"message": f"Errore gestione webhook: {str(e)}",
			}

	def _simulate_supplier_invoice(self, data):
		"""Simula ricezione fattura fornitore"""
		# Crea documento fittizio
		uuid = str(uuid_lib.uuid4())

		frappe.msgprint(
			f"Fattura fornitore simulata ricevuta con UUID: {uuid}",
			title="Provider Manuale - Test",
			indicator="orange",
		)

		return {
			"success": True,
			"message": "Fattura fornitore simulata elaborata",
			"uuid": uuid,
		}

	def _simulate_customer_notification(self, data):
		"""Simula notifica cliente"""
		return {
			"success": True,
			"message": "Notifica cliente simulata elaborata",
			"timestamp": datetime.now().isoformat(),
		}

	def setup_business_register(self, company, config: dict) -> dict:
		"""
		Simula setup business register

		Args:
		    company: Documento Company
		    config: Configurazione

		Returns:
		    dict: Risultato configurazione
		"""
		try:
			# Salva configurazione business register
			br_file = os.path.join(self.storage_path, f"business_register_{company.name}.json")

			config_data = {
				"company": company.name,
				"tax_id": company.tax_id,
				"config": config,
				"setup_date": datetime.now().isoformat(),
				"provider": "Manual",
			}

			with open(br_file, "w", encoding="utf-8") as f:
				json.dump(config_data, f, indent=2)

			frappe.msgprint(
				"Business Register configurato (simulato)",
				title="Provider Manuale",
				indicator="green",
			)

			return {
				"success": True,
				"message": "Business Register configurato in modalità test",
				"config": config_data,
			}

		except Exception as e:
			frappe.log_error(f"Errore setup business register: {str(e)}", "Manual Provider Error")
			return {
				"success": False,
				"message": f"Errore configurazione: {str(e)}",
			}
