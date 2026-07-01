"""
Provider OpenAPI per integrazione SDI
Estratto dal codice esistente in openapi/api/sdi/
"""

import json
import logging

import frappe
import pytz
import requests
from dateutil.parser import parse

from italian_invoice.providers.base import SDIProvider

# Configurazione logger
logger = logging.getLogger("italian_invoice.openapi_provider")


class OpenAPIProvider(SDIProvider):
	"""Provider per servizi SDI tramite OpenAPI"""

	def __init__(self):
		self.logger = logger

	def get_service_url(self, service_name, endpoint):
		"""Ottiene URL del servizio OpenAPI"""
		url = frappe.get_value("OpenApi Services", service_name, "url")
		return f"{url}/{endpoint}"

	def get_invoice_service_name(self, company):
		"""Determina il nome del servizio in base alle configurazioni company"""
		name = "invoices"
		if hasattr(company, "custom_apply_signature") and company.custom_apply_signature:
			name += "_signature"
		if hasattr(company, "custom_apply_legal_storage") and company.custom_apply_legal_storage:
			name += "_legal_storage"
		return name

	def send_invoice(self, xml_content: str, doc, company) -> dict:
		"""
		Invia fattura al SDI tramite OpenAPI

		Args:
		    xml_content: XML della fattura
		    doc: Documento fattura
		    company: Documento Company

		Returns:
		    dict: Risultato con uuid e messaggio
		"""
		try:
			service_name = self.get_invoice_service_name(company)
			url = self.get_service_url("SDI", service_name)

			headers = {
				"Authorization": company.custom_open_api_token,
				"Content-Type": "application/xml",
			}

			response = requests.post(url, headers=headers, data=xml_content)

			if response.status_code == 200:
				uuid = response.json()["data"]["uuid"]

				# Crea transazione SDI
				transazione_sdi = frappe.new_doc("Transazione SDI")
				transazione_sdi.tipo_fattura = doc.doctype
				transazione_sdi.fattura = doc.name
				transazione_sdi.stato_invio = "Inviata"
				transazione_sdi.uuid = uuid
				transazione_sdi.insert()

				# Aggiorna documento con riferimento transazione
				doc.custom_transazione_sdi = transazione_sdi.name
				doc.save()

				return {
					"success": True,
					"uuid": uuid,
					"message": f"Fattura inviata: {response.json()['data']}",
				}
			else:
				message = response.json().get("message", response.content)
				return {
					"success": False,
					"message": f"Errore nella richiesta: {message}",
				}

		except Exception as e:
			self.logger.exception(f"Errore invio fattura: {str(e)}")
			return {"success": False, "message": f"Errore invio fattura: {str(e)}"}

	def download_invoice(self, uuid: str, format: str, company) -> bytes:
		"""
		Scarica fattura dal SDI

		Args:
		    uuid: UUID fattura
		    format: Formato (xml, pdf, etc)
		    company: Documento Company

		Returns:
		    bytes: Contenuto file
		"""
		try:
			url = self.get_service_url("SDI", "invoices_download")
			url += f"/{uuid}"

			headers = {
				"Authorization": company.custom_open_api_token,
				"Accept": f"application/{format}",
			}

			response = requests.get(url, headers=headers)

			if response.status_code == 200:
				return response.content
			else:
				message = response.json().get("message", response.content)
				frappe.throw(f"Errore download: {message}")

		except Exception as e:
			self.logger.exception(f"Errore download fattura: {str(e)}")
			frappe.throw(f"Errore download fattura: {str(e)}")

	def get_invoice_status(self, uuid: str, company) -> dict:
		"""
		Ottiene stato fattura dal SDI

		Args:
		    uuid: UUID fattura
		    company: Documento Company

		Returns:
		    dict: Stato fattura
		"""
		try:
			url = self.get_service_url("SDI", f"invoices/{uuid}/status")

			headers = {
				"Authorization": company.custom_open_api_token,
			}

			response = requests.get(url, headers=headers)

			if response.status_code == 200:
				return response.json()["data"]
			else:
				message = response.json().get("message", response.content)
				return {"error": f"Errore stato: {message}"}

		except Exception as e:
			self.logger.exception(f"Errore recupero stato: {str(e)}")
			return {"error": f"Errore recupero stato: {str(e)}"}

	def _to_rome_str(self, dt) -> str:
		"""Formatta un datetime come stringa nel fuso Europe/Rome"""
		rome_tz = pytz.timezone("Europe/Rome")
		return dt.astimezone(rome_tz).strftime("%Y-%m-%d %H:%M:%S")

	def _apply_status_update(self, transazione, event, stato, data_notifica, raw_data, fattura=None):
		"""
		Applica un aggiornamento di stato a una Transazione SDI: accoda la notifica,
		aggiorna ultima_notifica/stato_invio e salva transazione + fattura collegata.
		Condiviso tra handle_notification() (webhook) e reconcile_status() (riconciliazione manuale).

		Args:
		    transazione: Documento Transazione SDI
		    event: Nome evento/notifica (es. "customer-notification", "manual-reconcile")
		    stato: Nuovo codice stato, o None per non cambiare stato
		    data_notifica: Timestamp formattato "%Y-%m-%d %H:%M:%S" (Europe/Rome)
		    raw_data: Payload grezzo da salvare in notifiche_sdi/ultima_notifica
		    fattura: Documento fattura già caricato, se disponibile (evita un get_doc extra)
		"""
		formatted_original_data = json.dumps(raw_data, indent=2)
		transazione.append(
			"notifiche_sdi",
			{
				"notifica": event,
				"data": formatted_original_data,
				"data_notifica": data_notifica,
				"uuid": transazione.uuid,
			},
		)

		# Aggiorna ultima_notifica solo se non è legal-storage-receipt
		if event != "legal-storage-receipt":
			transazione.ultima_notifica = formatted_original_data

		# Aggiorna stato solo se presente (escluso legal-storage-receipt)
		if stato:
			transazione.stato_invio = stato

		transazione.save()

		# Aggiorna Sales Invoice solo se lo stato è cambiato
		if stato:
			fattura = fattura or frappe.get_doc(transazione.tipo_fattura, transazione.fattura)
			fattura.save()

	def reconcile_status(self, transazione_sdi_name: str) -> dict:
		"""
		Interroga OpenAPI per lo stato reale di una transazione già inviata.
		Procedura di emergenza: usata quando una notifica SDI non ha mai
		aggiornato il documento (es. webhook non arrivato/non processato).

		Args:
		    transazione_sdi_name: Nome del documento Transazione SDI

		Returns:
		    dict: stato_precedente, stato_nuovo, raw (risposta grezza di OpenAPI)
		"""
		transazione = frappe.get_doc("Transazione SDI", transazione_sdi_name)
		fattura = frappe.get_doc(transazione.tipo_fattura, transazione.fattura)
		company = frappe.get_doc("Company", fattura.company)

		remote_status = self.get_invoice_status(transazione.uuid, company)

		if remote_status.get("error"):
			frappe.throw(remote_status["error"])

		stato_precedente = transazione.stato_invio
		data_notifica = self._to_rome_str(frappe.utils.now_datetime())

		self._apply_status_update(
			transazione,
			"manual-reconcile",
			remote_status.get("status"),
			data_notifica,
			remote_status,
			fattura=fattura,
		)

		return {
			"stato_precedente": stato_precedente,
			"stato_nuovo": transazione.stato_invio,
			"raw": remote_status,
		}

	def handle_notification(self, notification_data: dict) -> dict:
		"""
		Gestisce notifiche SDI

		Args:
		    notification_data: Dati notifica

		Returns:
		    dict: Risultato elaborazione
		"""
		try:
			event = notification_data.get("event")
			data = notification_data.get("data")

			# Estrai informazioni base
			uuid = None
			stato = None
			data_notifica = None

			if event == "customer-notification":
				# I dati potrebbero essere avvolti in "data" o essere diretti
				notification_data = data.get("data", data)
				uuid = notification_data["notification"]["invoice_uuid"]
				data_notifica = notification_data["notification"]["created_at"]
				stato = notification_data["notification"]["type"]
				if stato == "NE":
					stato = notification_data["notification"]["message"]["esito_committente"]["esito"]

			elif event == "customer-invoice":
				# I dati potrebbero essere avvolti in "data" o essere diretti
				invoice_data = data.get("data", data)
				uuid = invoice_data["invoice"]["uuid"]
				data_notifica = invoice_data["invoice"]["created_at"]
				stato = "Inviata"

			elif event == "legal-storage-receipt":
				# I dati potrebbero essere avvolti in "data" o essere diretti
				receipt_data = data.get("data", data)
				uuid = receipt_data["object_id"]
				data_notifica = receipt_data.get("receipt_received_at", receipt_data["updated_at"])
				stato = None  # Non cambiare stato per ricevute conservazione

			# Trova e aggiorna transazione
			if uuid:
				lista_transazioni = frappe.get_list(
					"Transazione SDI",
					filters={"uuid": uuid},
					fields=["name"],
				)

				if lista_transazioni:
					transazione = frappe.get_doc("Transazione SDI", lista_transazioni[0]["name"])

					# Converti data
					formatted_data_notifica = self._to_rome_str(parse(data_notifica))

					self._apply_status_update(
						transazione, event, stato, formatted_data_notifica, notification_data
					)

					return {"success": True, "message": f"Notifica {event} elaborata"}

			return {"success": False, "message": "UUID non trovato"}

		except Exception as e:
			self.logger.exception(f"Errore gestione notifica: {str(e)}")
			return {"success": False, "message": f"Errore: {str(e)}"}

	def configure_webhooks(self, company) -> dict:
		"""
		Configura webhook per notifiche SDI

		Args:
		    company: Documento Company

		Returns:
		    dict: Risultato configurazione
		"""
		try:
			fiscal_id = company.tax_id
			callbacks = []

			# Prepara callbacks dai webhook configurati
			if hasattr(company, "custom_elenco_webhook"):
				for webhook in company.custom_elenco_webhook:
					callback = {
						"event": webhook.event,
						"url": company.custom_webhook_url + webhook.url,
						"auth_header": company.custom_auth_header,
					}
					callbacks.append(callback)

			configuration = {"fiscal_id": fiscal_id, "callbacks": callbacks}

			url = self.get_service_url("SDI", "api_configurations")
			headers = {
				"Authorization": company.custom_open_api_token,
				"Content-Type": "application/json",
			}

			response = requests.post(url, headers=headers, json=configuration)

			if response.status_code == 200:
				return response.json()["data"]
			else:
				message = response.json().get("message", response.content)
				frappe.throw(f"Errore configurazione webhook: {message}")

		except Exception as e:
			self.logger.exception(f"Errore configurazione webhook: {str(e)}")
			frappe.throw(f"Errore configurazione webhook: {str(e)}")

	def handle_webhook(self, endpoint: str, data: dict) -> dict:
		"""
		Gestisce chiamate webhook in arrivo

		Args:
		    endpoint: Nome endpoint webhook
		    data: Dati ricevuti

		Returns:
		    dict: Risultato elaborazione
		"""
		try:
			# Router per diversi endpoint
			if endpoint == "supplier_invoice":
				return self._handle_supplier_invoice(data)
			elif endpoint == "customer_notification":
				return self.handle_notification({"event": "customer-notification", "data": data})
			elif endpoint == "customer_invoice":
				return self.handle_notification({"event": "customer-invoice", "data": data})
			elif endpoint == "legal_storage_receipt":
				return self.handle_notification({"event": "legal-storage-receipt", "data": data})
			elif endpoint == "invoice_status_quarantena":
				self.logger.info(f"Quarantena webhook: {data}")
				return {"success": True, "message": "OK from invoice_status_quarantena"}
			elif endpoint == "invoice_status_invoice_error":
				self.logger.info(f"Invoice error webhook: {data}")
				return {
					"success": True,
					"message": "OK from invoice_status_invoice_error",
				}
			else:
				return {
					"success": False,
					"message": f"Endpoint non riconosciuto: {endpoint}",
				}

		except Exception as e:
			self.logger.exception(f"Errore gestione webhook {endpoint}: {str(e)}")
			return {"success": False, "message": f"Errore: {str(e)}"}

	def _handle_supplier_invoice(self, data):
		"""Gestisce fattura fornitore ricevuta via webhook"""
		try:
			# Estrai dati dalla fattura
			partita_iva_company = self._search_value_in_json(
				data, "cessionario_committente.dati_anagrafici.id_fiscale_iva.id_codice"
			)
			partita_iva_fornitore = self._search_value_in_json(
				data, "cedente_prestatore.dati_anagrafici.id_fiscale_iva.id_codice"
			)
			denominazione_fornitore = self._search_value_in_json(
				data, "cedente_prestatore.dati_anagrafici.anagrafica.denominazione"
			)
			uuid = self._search_value_in_json(data, "invoice.uuid")

			# Trova company
			company_list = frappe.get_list("Company", filters={"tax_id": partita_iva_company})
			if not company_list:
				frappe.throw(f"Company non trovata: {partita_iva_company}")

			company = company_list[0]["name"]

			# Crea documento fattura fornitore
			fattura_fornitore = frappe.new_doc("Fattura Fornitori SDI")
			fattura_fornitore.dati_fattura = json.dumps({"event": "supplier-invoice", "data": data}, indent=2)
			fattura_fornitore.uuid = uuid
			fattura_fornitore.company = company
			fattura_fornitore.partita_iva_fornitore = partita_iva_fornitore
			fattura_fornitore.denominazione_fornitore = denominazione_fornitore
			fattura_fornitore.via_webhook = 1
			fattura_fornitore.insert()

			return {"success": True, "message": "Fattura fornitore salvata"}

		except Exception as e:
			self.logger.exception(f"Errore gestione fattura fornitore: {str(e)}")
			frappe.log_error(str(e), "Supplier Invoice Error")
			raise

	def _search_value_in_json(self, data, target_key):
		"""Cerca ricorsivamente un valore in JSON"""
		keys = target_key.split(".")

		def search(data, keys):
			if not keys:
				yield data
				return

			current_key = keys[0]
			remaining_keys = keys[1:]

			if isinstance(data, dict):
				for key, value in data.items():
					if key == current_key:
						yield from search(value, remaining_keys)
					if isinstance(value, (dict, list)):
						yield from search(value, keys)
			elif isinstance(data, list):
				for item in data:
					yield from search(item, keys)

		results = list(search(data, keys))
		if len(results) == 1:
			return results[0]
		return results

	def update_business_register(self, company, config: dict) -> dict:
		"""
		Aggiorna configurazione business register esistente presso OpenAPI.
		L'API non supporta PATCH, quindi fa DELETE + POST.

		Args:
		    company: Documento Company
		    config: Configurazione completa da ricreare

		Returns:
		    dict: Risultato configurazione
		"""
		fiscal_id = config.get("fiscal_id") or company.tax_id
		base_url = self.get_service_url("SDI", f"business_registry_configurations/{fiscal_id}")
		headers = {
			"Authorization": company.custom_open_api_token,
			"Content-Type": "application/json",
		}

		# DELETE configurazione esistente
		response = requests.delete(base_url, headers=headers)
		if response.status_code != 200:
			frappe.throw(f"Errore cancellazione business register: HTTP {response.status_code} - {response.text}")

		# POST nuova configurazione
		return self.setup_business_register(company, config)

	def setup_business_register(self, company, config: dict) -> dict:
		"""
		Configura business register presso OpenAPI

		Args:
		    company: Documento Company
		    config: Configurazione business register

		Returns:
		    dict: Risultato configurazione
		"""
		try:
			# Prepara dati
			config["apply_legal_storage"] = bool(config.get("apply_legal_storage", False))
			config["apply_signature"] = bool(config.get("apply_signature", False))

			url = self.get_service_url("SDI", "business_registry_configurations")
			headers = {
				"Authorization": company.custom_open_api_token,
				"Content-Type": "application/json",
			}

			response = requests.post(url, headers=headers, json=config)

			if response.status_code == 200:
				return response.json()["data"]
			else:
				frappe.throw(f"Errore business register: HTTP {response.status_code} - {response.text}")

		except Exception as e:
			self.logger.exception(f"Errore setup business register: {str(e)}")
			frappe.throw(f"Errore setup business register: {str(e)}")
