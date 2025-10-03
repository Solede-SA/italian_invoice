# Copyright (c) 2024, Solede SA and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document


class FatturaFornitoriSDI(Document):
    def validate(self):
        # Validazioni di sicurezza per produzione
        if not frappe.conf.get('developer_mode'):
            if self.is_new() and not self.get('via_webhook'):
                frappe.throw('In production mode, new records can only be created via webhook')

            if not self.is_new() and (self.has_value_changed('dati_fattura') or self.has_value_changed('uuid')):
                frappe.throw('In production mode, invoice data cannot be modified directly')

        # Autofatture non devono essere segnate come "Da importare"
        if self.is_new() and self.dati_fattura:
            tipo_documento = self._get_tipo_documento()
            if tipo_documento in ["TD17", "TD18", "TD19", "TD20"]:
                self.stato = "Importata"

    def _get_tipo_documento(self):
        """Estrae il tipo documento dai dati fattura"""
        if not self.dati_fattura:
            return None

        try:
            dati = json.loads(self.dati_fattura) if isinstance(self.dati_fattura, str) else self.dati_fattura

            # Percorsi possibili per trovare il tipo documento
            paths = [
                ["data", "invoice", "payload", "fattura_elettronica_body"],
                ["invoice", "payload", "fattura_elettronica_body"],
                ["invoice", "fattura_elettronica_body"],
                ["fattura_elettronica_body"]
            ]

            for path in paths:
                obj = dati
                for key in path:
                    obj = obj.get(key, {})
                    if not obj:
                        break

                if obj and len(obj) > 0:
                    tipo_doc = obj[0].get("dati_generali", {}).get("dati_generali_documento", {}).get("tipo_documento")
                    if tipo_doc:
                        return tipo_doc

            return None
        except:
            return None
