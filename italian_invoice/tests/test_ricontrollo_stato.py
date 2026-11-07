"""Ricontrollo dello stato presso OpenAPI: lo stato è l'ultima notifica del Sistema di Interscambio. Risposta nello stesso
formato di quella vera (SDI/26/00003 di erp.solede.com, 07/11/2026), ridotta ai campi che contano."""

import frappe
from frappe.tests import IntegrationTestCase

from italian_invoice.providers.openapi_provider import OpenAPIProvider

stato = OpenAPIProvider._stato_dalle_notifiche


def _risposta(*notifiche):
	return {"uuid": "019d161d-819d-705e-b776-ad431e41be8e", "type": 0, "marking": "delivered", "notifications": list(notifiche)}


class TestStatoDalleNotifiche(IntegrationTestCase):
	def test_consegnata(self):
		self.assertEqual(stato(_risposta({"type": "RC", "created_at": "2026-03-22T15:16:04+00:00"})), "RC")

	def test_vale_l_ultima_per_data(self):
		risposta = _risposta(
			{"type": "MC", "created_at": "2026-05-22T15:27:00+00:00"},
			{"type": "NS", "created_at": "2026-05-22T15:20:00+00:00"},
		)
		self.assertEqual(stato(risposta), "MC")

	def test_senza_notifiche_lo_stato_non_cambia(self):
		self.assertIsNone(stato(_risposta()))

	def test_esito_del_committente_non_si_indovina(self):
		with self.assertRaises(frappe.ValidationError):
			stato(_risposta({"type": "RC", "created_at": "2026-03-22T15:16:04+00:00"}, {"type": "NE", "created_at": "2026-03-25T10:00:00+00:00"}))
