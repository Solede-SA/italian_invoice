# -*- coding: utf-8 -*-
"""
Validatore XML per fatture elettroniche italiane
"""

import frappe
import xmlschema
from lxml import etree
import logging
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger("italian_invoice.validation")


class XMLInvoiceValidator:
    """Validatore per fatture elettroniche con gestione errori migliorata"""

    def __init__(self):
        self.xsd_path = frappe.get_app_path("italian_invoice", "utilities/schema_vfpr12.xsd")
        self.schema = None
        self.errors = []
        self.warnings = []

    def validate(self, xml_content: str, doc=None) -> Tuple[bool, Dict]:
        """
        Valida XML fattura con report dettagliato

        Args:
            xml_content: Contenuto XML da validare
            doc: Documento Frappe opzionale per contesto

        Returns:
            Tuple (is_valid, validation_report)
        """
        self.errors = []
        self.warnings = []

        # Reset logger
        logger.info(f"Inizio validazione fattura {doc.name if doc else 'XML'}")

        # Validazione struttura XML base
        if not self._validate_xml_structure(xml_content):
            return False, self._create_report()

        # Validazione XSD
        if not self._validate_xsd_schema(xml_content):
            return False, self._create_report()

        # Validazioni business rules italiane
        self._validate_business_rules(xml_content, doc)

        # Crea report finale
        is_valid = len(self.errors) == 0
        report = self._create_report()

        if is_valid:
            logger.info("Validazione completata con successo")
        else:
            logger.error(f"Validazione fallita con {len(self.errors)} errori")

        return is_valid, report

    def _validate_xml_structure(self, xml_content: str) -> bool:
        """Valida struttura XML base"""
        try:
            etree.fromstring(xml_content.encode('utf-8'))
            logger.debug("Struttura XML valida")
            return True
        except etree.XMLSyntaxError as e:
            line_no = e.lineno if hasattr(e, 'lineno') else 0
            self.errors.append({
                'type': 'XML_SYNTAX',
                'severity': 'critical',
                'message': 'Errore sintassi XML',
                'details': str(e),
                'line': line_no,
                'field': None,
                'suggestion': 'Verifica che il file XML sia ben formato'
            })
            return False

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
            self.errors.append({
                'type': 'XSD_VALIDATION',
                'severity': 'critical',
                'message': 'Errore validazione XSD',
                'details': str(e),
                'line': None,
                'field': None,
                'suggestion': 'Contatta il supporto tecnico'
            })
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
            path_parts = xml_path.split('/')
            clean_parts = []
            for p in path_parts:
                if p:
                    # Rimuovi namespace {http://...}
                    p = re.sub(r'\{.*?\}', '', p)
                    # Rimuovi prefisso p:
                    p = re.sub(r'^\w+:', '', p)
                    clean_parts.append(p)

            # Path leggibile
            readable_path = ' → '.join(clean_parts) if clean_parts else xml_path

            # Prendi l'ultimo elemento come nome campo
            field_name = clean_parts[-1] if clean_parts else None

            if value and field_name:
                message = f'Il valore "{value}" non rispetta il formato richiesto nel campo {field_name} (percorso: {readable_path})'
            elif field_name:
                message = f'Errore nel campo {field_name} (percorso: {readable_path})'
            elif value:
                message = f'Il valore "{value}" non è valido (percorso: {readable_path})'
            else:
                message = f'Errore di validazione (percorso: {readable_path})'
        else:
            # Senza path
            if value:
                message = f'Il valore "{value}" non è valido'
            else:
                # Mantieni almeno parte dell'errore originale
                message = f'Errore validazione: {error_str[:150]}...' if len(error_str) > 150 else f'Errore validazione: {error_str}'

        # Suggerimento generico basato sul contenuto dell'errore
        suggestion = 'Verifica il formato secondo le specifiche FatturaPA'
        if 'pattern' in error_str.lower():
            suggestion = 'Verifica che il valore rispetti il formato richiesto'
        elif 'missing' in error_str.lower():
            suggestion = 'Aggiungi i campi obbligatori mancanti'
        elif 'not expected' in error_str.lower():
            suggestion = 'Rimuovi o correggi gli elementi non previsti'

        self.errors.append({
            'type': 'XSD_VALIDATION',
            'severity': 'error',
            'message': message,
            'details': error_str,
            'line': getattr(error, 'sourceline', None),
            'field': field_name if xml_path else None,
            'path': xml_path,
            'suggestion': suggestion
        })

    def _validate_business_rules(self, xml_content: str, doc=None):
        """Validazioni specifiche business italiane"""
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            ns = {'ns': 'http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2'}

            # Valida Partita IVA
            self._validate_vat_numbers(root, ns)

            # Valida Codici Fiscali
            self._validate_fiscal_codes(root, ns)

            # Valida date
            self._validate_dates(root, ns)

            # Valida importi e calcoli
            self._validate_amounts(root, ns)

            # Valida codice destinatario
            self._validate_recipient_code(root, ns)

        except Exception as e:
            logger.warning(f"Errore in validazioni business: {str(e)}")

    def _validate_vat_numbers(self, root, ns):
        """Valida partite IVA"""
        # Cedente/Prestatore
        vat_elements = root.xpath('//ns:CedentePrestatore//ns:IdCodice', namespaces=ns)
        for elem in vat_elements:
            vat = elem.text
            if vat and not self._is_valid_vat(vat):
                self.warnings.append({
                    'type': 'BUSINESS_RULE',
                    'severity': 'warning',
                    'message': f'Partita IVA potrebbe non essere valida: {vat}',
                    'field': 'IdCodice',
                    'suggestion': 'Verifica la correttezza della P.IVA (11 cifre)'
                })

    def _validate_fiscal_codes(self, root, ns):
        """Valida codici fiscali"""
        cf_elements = root.xpath('//ns:CodiceFiscale', namespaces=ns)
        for elem in cf_elements:
            cf = elem.text
            if cf and not self._is_valid_fiscal_code(cf):
                self.warnings.append({
                    'type': 'BUSINESS_RULE',
                    'severity': 'warning',
                    'message': f'Codice Fiscale potrebbe non essere valido: {cf}',
                    'field': 'CodiceFiscale',
                    'suggestion': 'Verifica formato CF (16 caratteri alfanumerici)'
                })

    def _validate_dates(self, root, ns):
        """Valida date documento"""
        from datetime import datetime, timedelta

        date_elements = root.xpath('//ns:Data', namespaces=ns)
        today = datetime.now().date()

        for elem in date_elements:
            try:
                date_str = elem.text
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Data futura
                if date_obj > today:
                    parent = elem.getparent().tag.split('}')[-1]
                    self.warnings.append({
                        'type': 'BUSINESS_RULE',
                        'severity': 'warning',
                        'message': f'Data futura in {parent}: {date_str}',
                        'field': parent,
                        'suggestion': 'Verifica che la data sia corretta'
                    })

                # Data troppo vecchia (> 1 anno)
                if date_obj < today - timedelta(days=365):
                    parent = elem.getparent().tag.split('}')[-1]
                    self.warnings.append({
                        'type': 'BUSINESS_RULE',
                        'severity': 'info',
                        'message': f'Data molto vecchia in {parent}: {date_str}',
                        'field': parent,
                        'suggestion': 'Verifica che la data sia corretta'
                    })

            except ValueError:
                pass  # Già gestito da XSD

    def _validate_amounts(self, root, ns):
        """Valida importi e calcoli"""
        # Verifica coerenza totali
        try:
            # Somma imponibili
            imponibili = root.xpath('//ns:ImponibileImporto', namespaces=ns)
            total_imponibile = sum(float(i.text) for i in imponibili if i.text)

            # Totale documento
            totale_elem = root.xpath('//ns:ImportoTotaleDocumento', namespaces=ns)
            if totale_elem and totale_elem[0].text:
                totale = float(totale_elem[0].text)

                # Tolleranza di 1 euro per arrotondamenti
                if abs(totale - total_imponibile) > 1 and total_imponibile > 0:
                    self.warnings.append({
                        'type': 'BUSINESS_RULE',
                        'severity': 'warning',
                        'message': f'Possibile discrepanza nei totali: imponibile={total_imponibile:.2f}, totale={totale:.2f}',
                        'field': 'ImportoTotaleDocumento',
                        'suggestion': 'Verifica il calcolo dei totali'
                    })
        except Exception:
            pass  # Non critico

    def _validate_recipient_code(self, root, ns):
        """Valida codice destinatario"""
        cod_dest = root.xpath('//ns:CodiceDestinatario', namespaces=ns)
        if cod_dest and cod_dest[0].text:
            code = cod_dest[0].text

            # Verifica formato (7 caratteri alfanumerici o 0000000)
            if not re.match(r'^[A-Z0-9]{7}$', code):
                self.errors.append({
                    'type': 'BUSINESS_RULE',
                    'severity': 'error',
                    'message': f'Codice Destinatario non valido: {code}',
                    'field': 'CodiceDestinatario',
                    'suggestion': 'Usa 7 caratteri alfanumerici o "0000000" per privati'
                })

            # Warning per codice generico
            if code == '0000000':
                self.warnings.append({
                    'type': 'BUSINESS_RULE',
                    'severity': 'info',
                    'message': 'Codice Destinatario generico (0000000)',
                    'field': 'CodiceDestinatario',
                    'suggestion': 'Assicurati che il cliente abbia fornito la PEC'
                })

    def _is_valid_vat(self, vat: str) -> bool:
        """Verifica base P.IVA italiana (11 cifre)"""
        if not vat or not vat.isdigit():
            return False
        return len(vat) == 11

    def _is_valid_fiscal_code(self, cf: str) -> bool:
        """Verifica base CF italiano (16 caratteri)"""
        if not cf:
            return False
        cf = cf.upper()
        if len(cf) != 16:
            return False
        # Pattern base CF
        pattern = r'^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$'
        return bool(re.match(pattern, cf))

    def _create_report(self) -> Dict:
        """Crea report di validazione"""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'summary': self._create_summary()
        }

    def _create_summary(self) -> str:
        """Crea sommario testuale degli errori"""
        if not self.errors and not self.warnings:
            return "✅ Validazione completata con successo"

        summary = []

        if self.errors:
            summary.append(f"❌ {len(self.errors)} errori trovati:")
            for err in self.errors[:3]:  # Primi 3 errori
                summary.append(f"  • {err['message']}")
            if len(self.errors) > 3:
                summary.append(f"  • ...e altri {len(self.errors) - 3} errori")

        if self.warnings:
            summary.append(f"⚠️ {len(self.warnings)} avvisi:")
            for warn in self.warnings[:2]:  # Primi 2 warning
                summary.append(f"  • {warn['message']}")
            if len(self.warnings) > 2:
                summary.append(f"  • ...e altri {len(self.warnings) - 2} avvisi")

        return "\n".join(summary)