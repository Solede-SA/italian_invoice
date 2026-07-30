import json
import unittest
from pathlib import Path

CUSTOM_DIR = Path(__file__).resolve().parents[1] / "italian_invoice" / "custom"
ALLOWED_MODULES = {None, "Italian Invoice"}

# I campi del flusso SDI sono di italian_invoice (i DocType Transazione SDI /
# Stato Fattura Elettronica e le scritture nei provider vivono qui): devono
# dichiarare il module esplicito, così l'uninstall di altre app non li cancella
# e l'export fixtures li include.
SDI_FIELDS = {
	("Sales Invoice", "custom_sdi"),
	("Sales Invoice", "custom_transazione_sdi"),
	("Sales Invoice", "custom_stato_invio"),
	("Sales Invoice", "custom_descrizione_stato"),
	("Sales Invoice", "custom_column_break_purnx"),
	("Sales Invoice", "custom_uuid"),
	("Purchase Invoice", "custom_sdi"),
	("Purchase Invoice", "custom_transazione_sdi"),
	("Purchase Invoice", "custom_stato_invio"),
	("Purchase Invoice", "custom_descrizione_stato"),
	("Purchase Invoice", "custom_column_break_c1jau"),
	("Purchase Invoice", "custom_uuid"),
}


class TestCustomExportHygiene(unittest.TestCase):
	"""Export Customizations su un sito multi-app ingloba anche campi e property
	setter di ALTRE app; con sync_on_migrate ogni migrate riscrive quelle copie
	sopra le definizioni canoniche delle app proprietarie (bug TD24). In
	custom/*.json possono vivere solo pezzi di modulo Italian Invoice o senza
	modulo. Limite noto: entry senza chiave "module" e links non sono coperti —
	all'export usare "Apply Module Export Filter" e fare l'audit a mano.
	"""

	def test_no_foreign_module_entries(self):
		for path in sorted(CUSTOM_DIR.glob("*.json")):
			data = json.loads(path.read_text())
			for section in ("custom_fields", "property_setters"):
				for entry in data.get(section) or []:
					self.assertIn(
						entry.get("module"),
						ALLOWED_MODULES,
						f"{path.name}: '{entry.get('fieldname') or entry.get('name')}' "
						f"({section}) appartiene al modulo {entry.get('module')!r} di "
						"un'altra app: va rimosso, la proprietaria lo risincronizza al migrate",
					)

	def test_sdi_fields_have_explicit_module(self):
		shipped = {}
		for path in sorted(CUSTOM_DIR.glob("*.json")):
			for entry in json.loads(path.read_text()).get("custom_fields") or []:
				shipped[(entry["dt"], entry["fieldname"])] = entry.get("module")
		for key in sorted(SDI_FIELDS):
			self.assertEqual(
				shipped.get(key),
				"Italian Invoice",
				f"{key}: il campo SDI deve essere spedito da custom/*.json con "
				'module "Italian Invoice" esplicito',
			)
