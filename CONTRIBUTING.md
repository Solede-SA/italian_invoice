# Contributing to Italian Invoice

Grazie per il tuo interesse nel contribuire a Italian Invoice! 🎉

## 📋 Indice

- [Codice di Condotta](#codice-di-condotta)
- [Come Contribuire](#come-contribuire)
- [Setup Ambiente di Sviluppo](#setup-ambiente-di-sviluppo)
- [Convenzioni di Codice](#convenzioni-di-codice)
- [Testing](#testing)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Implementare Nuovi Provider SDI](#implementare-nuovi-provider-sdi)

## Codice di Condotta

Questo progetto segue il [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). Partecipando, ti aspettiamo che tu rispetti questo codice.

## Come Contribuire

Ci sono molti modi per contribuire:

- 🐛 Segnalare bug
- 💡 Proporre nuove funzionalità
- 📝 Migliorare la documentazione
- 🔧 Fixare bug
- ✨ Implementare nuove feature
- 🧪 Scrivere test
- 🌍 Tradurre in altre lingue
- 🔌 Implementare nuovi provider SDI

## Setup Ambiente di Sviluppo

### Prerequisiti

- Frappe Framework v15+
- ERPNext v15+
- Python 3.10+
- Node.js 18+

### Installazione

1. **Fork del repository**
   ```bash
   cd frappe-bench/apps
   git clone https://github.com/TUO-USERNAME/italian_invoice.git
   cd italian_invoice
   ```

2. **Installa l'app**
   ```bash
   bench --site your-site.local install-app italian_invoice
   ```

3. **Crea branch per la tua feature**
   ```bash
   git checkout -b feature/nome-feature
   ```

## Convenzioni di Codice

### Python

- Seguire **PEP 8**
- Usare **type hints** quando possibile
- Docstring in formato Google style
- Principio **DRY** (Don't Repeat Yourself)
- Principio **KISS** (Keep It Simple, Stupid)
- **NO fallback**: mostrare sempre errori all'utente

```python
def validate_partita_iva(partita_iva: str) -> bool:
    """Valida una Partita IVA italiana.

    Args:
        partita_iva: Partita IVA da validare (11 cifre)

    Returns:
        True se valida, False altrimenti

    Raises:
        frappe.ValidationError: Se formato non valido
    """
    if not partita_iva or len(partita_iva) != 11:
        frappe.throw("Partita IVA deve essere di 11 cifre")

    if not partita_iva.isdigit():
        frappe.throw("Partita IVA deve contenere solo numeri")

    return True
```

### JavaScript

- Usare ES6+ syntax
- Arrow functions quando possibile
- Nomi variabili descrittivi

```javascript
function refreshInvoiceStatus(frm) {
    frappe.call({
        method: "italian_invoice.api.sdi.get_invoice_status",
        args: { invoice_name: frm.doc.name },
        callback: (r) => {
            if (r.message) {
                frm.set_value("stato_fattura", r.message.status);
                frm.refresh();
            }
        }
    });
}
```

## Testing

### Scrivere Test

Tutti i nuovi features devono includere test:

```python
# italian_invoice/doctype/fattura_fornitori_sdi/test_fattura_fornitori_sdi.py
import frappe
from frappe.tests.utils import FrappeTestCase

class TestFatturaFornitoriSDI(FrappeTestCase):
    def test_parse_xml_fornitore(self):
        """Test parsing XML fattura fornitore"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>..."""

        doc = frappe.get_doc({
            "doctype": "Fattura Fornitori SDI",
            "xml_content": xml_content
        })
        doc.parse_xml()

        self.assertEqual(doc.partita_iva_fornitore, "12345678901")
        self.assertEqual(doc.totale_documento, 122.00)
```

### Eseguire Test

```bash
# Tutti i test
bench --site your-site.local run-tests --app italian_invoice

# Test specifico
bench --site your-site.local run-tests --app italian_invoice --doctype "Fattura Fornitori SDI"
```

## Commit Convention

Usa [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: Nuova funzionalità
- `fix`: Bug fix
- `docs`: Modifiche documentazione
- `style`: Formattazione (no logic changes)
- `refactor`: Refactoring codice
- `test`: Aggiunta/modifica test
- `chore`: Maintenance tasks

### Scope Suggeriti

- `sdi`: Sistema di Interscambio
- `fatture-attive`: Sales Invoices / Fatturazione attiva
- `fatture-passive`: Purchase Invoices / Fatturazione passiva
- `pagamenti`: Payment rounding e reconciliation
- `registri-iva`: Registri IVA vendite/acquisti
- `provider`: Sistema provider SDI
- `xml`: Generazione e validazione XML
- `docs`: Documentazione

### Esempi

```bash
feat(sdi): add support for PA (Pubblica Amministrazione) invoices

- Implement CodiceDestinatario validation for PA
- Add special Nature IVA handling for PA invoices
- Update XML generation for PA-specific fields

Closes #42

fix(pagamenti): resolve rounding issue for partial payments

The payment rounding was not correctly handling
amounts with more than 2 decimal places.

Fixes #38

docs(readme): update provider implementation guide

- Add step-by-step guide for custom provider
- Include code examples
- Add troubleshooting section
```

## Pull Request Process

1. **Update Documentation**
   - Aggiorna README.md se necessario
   - Aggiungi entry in CHANGELOG.md
   - Commenta il codice complesso

2. **Test Your Changes**
   ```bash
   bench --site your-site.local migrate
   bench restart
   ```

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

4. **Push to Fork**
   ```bash
   git push origin feature/nome-feature
   ```

5. **Create Pull Request**
   - Vai su GitHub
   - Clicca "New Pull Request"
   - Compila il template:
     - Descrizione chiara delle modifiche
     - Link alle issue correlate
     - Screenshots se UI changes
     - Checklist completata

6. **Code Review**
   - Rispondi ai commenti
   - Fai le modifiche richieste
   - Push aggiornamenti (stesso branch)

## Implementare Nuovi Provider SDI

Italian Invoice usa un'architettura pluggabile per i provider SDI. Puoi implementare il tuo provider per integrare servizi specifici.

### Struttura Provider

```python
# italian_invoice/providers/mio_provider.py
from italian_invoice.providers.base import SDIProvider

class MioProvider(SDIProvider):
    """Provider per Servizio XYZ"""

    def send_invoice(self, xml_content: str, doc, company) -> dict:
        """Invia fattura al SDI tramite servizio XYZ

        Args:
            xml_content: XML FatturaPA
            doc: Sales Invoice document
            company: Company name

        Returns:
            dict con status e transaction_id
        """
        # Implementazione invio
        pass

    def get_invoice_status(self, transaction_id: str, company) -> dict:
        """Recupera stato fattura da SDI

        Args:
            transaction_id: ID transazione
            company: Company name

        Returns:
            dict con status e dettagli
        """
        # Implementazione status
        pass
```

### Registrare Provider

Aggiungi il tuo provider in `hooks.py`:

```python
# hooks.py
sdi_providers = {
    "Manual": "italian_invoice.providers.manual_provider.ManualProvider",
    "MioProvider": "italian_invoice.providers.mio_provider.MioProvider"
}
```

### Testing Provider

Implementa test per il tuo provider:

```python
# test_mio_provider.py
def test_send_invoice():
    provider = MioProvider()
    result = provider.send_invoice(xml_content, doc, company)
    assert result["status"] == "success"
    assert "transaction_id" in result
```

## Segnalazione Bug

### Template Bug Report

```markdown
**Descrizione Bug**
Descrizione chiara del problema.

**Come Riprodurre**
1. Vai a '...'
2. Clicca su '...'
3. Vedi errore

**Comportamento Atteso**
Cosa ti aspettavi che succedesse.

**Screenshots**
Se applicabile, aggiungi screenshots.

**Ambiente:**
- Frappe Version: [es. v15.10.0]
- ERPNext Version: [es. v15.8.0]
- App Version: [es. v1.0.0]
- Python: [es. 3.10.12]

**Log di Errore**
```
Paste error log here
```

**File XML** (se applicabile)
```xml
<!-- Solo se il bug riguarda parsing XML -->
```
```

## Richiesta Feature

### Template Feature Request

```markdown
**La tua feature risolve un problema?**
Descrizione chiara del problema.

**Descrivi la soluzione che vorresti**
Cosa vorresti che succedesse.

**Use Case**
Scenario d'uso concreto.

**Conformità Normativa**
Se la feature riguarda aspetti normativi, fornisci riferimenti a:
- Specifiche tecniche SDI
- Normativa fiscale italiana
- Circolare Agenzia delle Entrate

**Contesto Aggiuntivo**
Screenshots, mockup, esempi XML.
```

## Licenza

Contribuendo a questo progetto, accetti che i tuoi contributi saranno rilasciati sotto la licenza **GNU Affero General Public License v3.0**.

Tutti i file devono includere l'header copyright:

```python
# Copyright (c) 2024-2025, Solede SA and contributors
# For license information, please see license.txt
# License: GNU Affero General Public License v3 or later (AGPLv3+)
# See https://www.gnu.org/licenses/agpl-3.0.html
```

## Domande?

- 💬 Apri una [Discussion su GitHub](https://github.com/Solede-SA/italian_invoice/discussions)
- 📧 Email: info@solede.com
- 🐛 Segnala bug: [GitHub Issues](https://github.com/Solede-SA/italian_invoice/issues)

## Grazie! 🙏

Ogni contributo, grande o piccolo, è apprezzato e aiuta a migliorare questo progetto per tutta la community italiana ERPNext!

---

Made with ❤️ by Solede SA and contributors
