# -*- coding: utf-8 -*-
"""
Interfaccia base per provider SDI
Tutti i provider devono ereditare da questa classe
"""

from abc import ABC, abstractmethod


class SDIProvider(ABC):
    """Interfaccia base per provider SDI"""

    @abstractmethod
    def send_invoice(self, xml_content: str, doc, company) -> dict:
        """
        Invia fattura al SDI

        Args:
            xml_content: Contenuto XML della fattura
            doc: Documento fattura (Sales/Purchase Invoice)
            company: Documento Company

        Returns:
            dict: Risultato invio con uuid e stato
        """
        raise NotImplementedError

    @abstractmethod
    def download_invoice(self, uuid: str, format: str, company) -> bytes:
        """
        Scarica fattura dal SDI

        Args:
            uuid: Identificativo fattura
            format: Formato richiesto (xml, pdf, etc)
            company: Documento Company

        Returns:
            bytes: Contenuto del file
        """
        raise NotImplementedError

    @abstractmethod
    def get_invoice_status(self, uuid: str, company) -> dict:
        """
        Ottiene stato fattura

        Args:
            uuid: Identificativo fattura
            company: Documento Company

        Returns:
            dict: Stato fattura
        """
        raise NotImplementedError

    @abstractmethod
    def handle_notification(self, notification_data: dict) -> dict:
        """
        Gestisce notifiche SDI

        Args:
            notification_data: Dati notifica

        Returns:
            dict: Risultato elaborazione
        """
        raise NotImplementedError

    @abstractmethod
    def configure_webhooks(self, company) -> dict:
        """
        Configura webhook per notifiche SDI

        Args:
            company: Documento Company

        Returns:
            dict: Risultato configurazione
        """
        raise NotImplementedError

    @abstractmethod
    def handle_webhook(self, endpoint: str, data: dict) -> dict:
        """
        Gestisce chiamate webhook in arrivo

        Args:
            endpoint: Nome endpoint webhook
            data: Dati ricevuti

        Returns:
            dict: Risultato elaborazione
        """
        raise NotImplementedError

    @abstractmethod
    def setup_business_register(self, company, config: dict) -> dict:
        """
        Configura il business register presso il provider

        Args:
            company: Documento Company
            config: Configurazione business register

        Returns:
            dict: Risultato configurazione
        """
        raise NotImplementedError