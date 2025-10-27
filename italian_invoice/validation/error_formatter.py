# -*- coding: utf-8 -*-
"""
Formattatore di errori per validazione fatture elettroniche
"""

import frappe
from typing import Dict


class ValidationErrorFormatter:
    """Formatta errori di validazione in messaggi user-friendly"""

    # Mapping campi tecnici -> nomi user-friendly
    FIELD_NAMES = {
        "IdCodice": "Partita IVA",
        "CodiceFiscale": "Codice Fiscale",
        "CodiceDestinatario": "Codice Destinatario SDI",
        "PECDestinatario": "PEC Destinatario",
        "Denominazione": "Ragione Sociale",
        "Nome": "Nome",
        "Cognome": "Cognome",
        "NumeroREA": "Numero REA",
        "CapitaleSociale": "Capitale Sociale",
        "SocioUnico": "Socio Unico",
        "StatoLiquidazione": "Stato Liquidazione",
        "Indirizzo": "Indirizzo",
        "NumeroCivico": "Numero Civico",
        "CAP": "CAP",
        "Comune": "Comune",
        "Provincia": "Provincia",
        "Nazione": "Nazione",
        "Data": "Data Documento",
        "Numero": "Numero Documento",
        "ImportoTotaleDocumento": "Totale Documento",
        "Causale": "Causale",
        "NumeroLinea": "Numero Linea",
        "Descrizione": "Descrizione",
        "Quantita": "Quantità",
        "PrezzoUnitario": "Prezzo Unitario",
        "AliquotaIVA": "Aliquota IVA",
        "Natura": "Natura Esenzione IVA",
        "RiferimentoNormativo": "Riferimento Normativo",
    }

    # Messaggi di errore specifici
    ERROR_MESSAGES = {
        "XML_SYNTAX": "Il file XML non è formattato correttamente",
        "XSD_VALIDATION": "Il documento non rispetta lo schema FatturaPA",
        "BUSINESS_RULE": "Violazione regole di business",
        "MISSING_FIELD": "Campo obbligatorio mancante",
        "INVALID_FORMAT": "Formato dati non valido",
        "INVALID_VALUE": "Valore non ammesso",
    }

    @classmethod
    def format_validation_report(cls, report: Dict, format_type: str = "html") -> str:
        """
        Formatta report di validazione

        Args:
            report: Report da XMLInvoiceValidator
            format_type: 'html', 'text', o 'json'

        Returns:
            Report formattato
        """
        if format_type == "html":
            return cls._format_html(report)
        elif format_type == "text":
            return cls._format_text(report)
        else:
            return str(report)

    @classmethod
    def _format_html(cls, report: Dict) -> str:
        """Formatta report in HTML per UI Frappe"""
        html = []

        # Header con stato
        if report["valid"]:
            html.append('<div class="alert alert-success">')
            html.append("<h4>✅ Validazione Completata</h4>")
            html.append("<p>Il documento è valido e pronto per l'invio al SDI.</p>")
        else:
            html.append('<div class="alert alert-danger">')
            html.append("<h4>❌ Validazione Fallita</h4>")
            html.append(
                f"<p>Trovati {report['error_count']} errori che devono essere corretti.</p>"
            )

        html.append("</div>")

        # Errori
        if report["errors"]:
            html.append('<div class="validation-errors">')
            html.append("<h5>Errori da correggere:</h5>")
            html.append('<ul class="list-unstyled">')

            for error in report["errors"]:
                html.append(
                    '<li class="alert alert-danger" style="padding: 10px; margin: 5px 0;">'
                )

                # Icona e messaggio principale
                html.append(
                    f"<strong>🚫 {cls._get_friendly_message(error)}</strong><br>"
                )

                # Campo interessato
                if error.get("field"):
                    field_name = cls.FIELD_NAMES.get(error["field"], error["field"])
                    html.append(
                        f'<span class="text-muted">Campo: {field_name}</span><br>'
                    )

                # Suggerimento
                if error.get("suggestion"):
                    html.append(
                        f'<span class="text-info">💡 {error["suggestion"]}</span><br>'
                    )

                # Dettagli tecnici (collassabili)
                if error.get("details"):
                    html.append('<details style="margin-top: 5px;">')
                    html.append(
                        '<summary style="cursor: pointer; color: #666;">Dettagli tecnici</summary>'
                    )
                    html.append(
                        f'<code style="font-size: 0.85em;">{error["details"][:200]}</code>'
                    )
                    html.append("</details>")

                html.append("</li>")

            html.append("</ul>")
            html.append("</div>")

        # Avvisi
        if report["warnings"]:
            html.append('<div class="validation-warnings" style="margin-top: 20px;">')
            html.append("<h5>Avvisi (non bloccanti):</h5>")
            html.append('<ul class="list-unstyled">')

            for warning in report["warnings"]:
                html.append(
                    '<li class="alert alert-warning" style="padding: 8px; margin: 3px 0;">'
                )
                html.append(f"<strong>⚠️ {cls._get_friendly_message(warning)}</strong>")

                if warning.get("suggestion"):
                    html.append(
                        f' - <span class="text-muted">{warning["suggestion"]}</span>'
                    )

                html.append("</li>")

            html.append("</ul>")
            html.append("</div>")

        # Sommario azioni
        if not report["valid"]:
            html.append('<div class="alert alert-info" style="margin-top: 20px;">')
            html.append("<h5>📋 Prossimi passi:</h5>")
            html.append("<ol>")
            html.append("<li>Correggi gli errori indicati sopra</li>")
            html.append("<li>Salva le modifiche al documento</li>")
            html.append("<li>Rigenera il file XML</li>")
            html.append("<li>La validazione verrà eseguita automaticamente</li>")
            html.append("</ol>")
            html.append("</div>")

        return "".join(html)

    @classmethod
    def _format_text(cls, report: Dict) -> str:
        """Formatta report in testo semplice"""
        lines = []

        # Header
        if report["valid"]:
            lines.append("✅ VALIDAZIONE COMPLETATA CON SUCCESSO")
            lines.append("=" * 50)
        else:
            lines.append("❌ VALIDAZIONE FALLITA")
            lines.append("=" * 50)
            lines.append(
                f"Errori: {report['error_count']} | Avvisi: {report['warning_count']}"
            )

        lines.append("")

        # Errori
        if report["errors"]:
            lines.append("ERRORI DA CORREGGERE:")
            lines.append("-" * 30)
            for i, error in enumerate(report["errors"], 1):
                lines.append(f"{i}. {cls._get_friendly_message(error)}")
                if error.get("field"):
                    field_name = cls.FIELD_NAMES.get(error["field"], error["field"])
                    lines.append(f"   Campo: {field_name}")
                if error.get("suggestion"):
                    lines.append(f"   → {error['suggestion']}")
                lines.append("")

        # Avvisi
        if report["warnings"]:
            lines.append("AVVISI:")
            lines.append("-" * 30)
            for warning in report["warnings"]:
                lines.append(f"⚠ {cls._get_friendly_message(warning)}")
                if warning.get("suggestion"):
                    lines.append(f"  → {warning['suggestion']}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def _get_friendly_message(cls, error: Dict) -> str:
        """Converte messaggio tecnico in user-friendly"""
        message = error.get("message", "")

        # Sostituisci termini tecnici
        replacements = {
            "Element": "Campo",
            "Missing": "Mancante",
            "Invalid": "Non valido",
            "Expected": "Richiesto",
            "pattern": "formato",
            "enumeration": "valore ammesso",
        }

        for old, new in replacements.items():
            message = message.replace(old, new)

        # Traduci nomi campi
        for tech_name, friendly_name in cls.FIELD_NAMES.items():
            message = message.replace(tech_name, friendly_name)

        return message

    @classmethod
    def show_validation_dialog(cls, report: Dict):
        """Mostra dialogo Frappe con errori di validazione"""
        if report["valid"]:
            frappe.msgprint(
                title="Validazione Completata",
                msg="Il documento è valido e pronto per l'invio al SDI.",
                indicator="green",
            )
        else:
            # Prepara messaggio HTML
            msg = cls.format_validation_report(report, "html")

            # Mostra dialogo
            frappe.msgprint(
                title="Errori di Validazione",
                msg=msg,
                indicator="red",
                wide=True,
                as_list=False,
            )

    @classmethod
    def log_validation_errors(cls, report: Dict, doc_name: str = None):
        """Logga errori di validazione nel sistema"""
        if not report["valid"]:
            error_details = cls.format_validation_report(report, "text")

            frappe.log_error(
                message=error_details,
                title=f"Validazione Fattura Fallita: {doc_name or 'N/A'}",
            )

            # Log anche nel logger Python
            import logging

            logger = logging.getLogger("italian_invoice.validation")
            logger.error(f"Validation failed for {doc_name}: {report['summary']}")
