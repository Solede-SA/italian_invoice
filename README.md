# Italian Invoice

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Frappe](https://img.shields.io/badge/Frappe-v15+-blue.svg)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-v15+-green.svg)](https://erpnext.com)

App Frappe/ERPNext per la gestione della **Fatturazione Elettronica Italiana** conforme allo standard **FatturaPA** e al **Sistema di Interscambio (SDI)**.

## 💡 Caratteristiche

- ✅ Generazione XML FatturaPA v1.2.1 conforme allo standard SDI
- ✅ Validazione XML multi-livello con messaggi user-friendly
- ✅ Import automatico fatture fornitori via webhook o upload
- ✅ Auto-link intelligente fatture passive con Purchase Orders/Receipts
- ✅ Arrotondamento pagamenti automatico con audit trail
- ✅ Registri IVA vendite/acquisti conformi normativa italiana
- ✅ Architettura provider pluggabile per diversi servizi SDI
- ✅ Provider Manual built-in (zero dipendenze esterne)
- ✅ Supporto Split Payment, Lettera d'Intento, Nature IVA (N1-N7)
- ✅ ~4,700 linee di codice Python production-ready

## 📦 Installazione

```bash
# Ottieni l'app
bench get-app italian_invoice

# Installa nel sito
bench --site [nome-sito] install-app italian_invoice

# Applica modifiche
bench --site [nome-sito] migrate
```

**Requisiti**: Frappe v15+, ERPNext v15+, Python 3.10+

## 🔧 Configurazione Rapida

### 1. Setup Company

Vai in **Company** → Seleziona la tua azienda e compila:

- **Tax ID**: Partita IVA (senza IT)
- **Fiscal Code**: Codice Fiscale
- **Fiscal Regime**: Regime fiscale (es. RF01)
- **Codice Sistema Interscambio**: Codice SDI (7 caratteri)
- **Provider SDI**: Seleziona "Manual" per iniziare

### 2. Configura Customers/Suppliers

Per ogni cliente/fornitore aggiungi:

- **Tax ID**: Partita IVA (P.IVA)
- **Fiscal Code**: Codice Fiscale
- **Codice Destinatario**: Codice SDI (B2B) o PEC
- Per clienti: **Tipo Fattura Elettronica** (B2B/B2C/PA)

## 🚀 Utilizzo Base

### Fatturazione Attiva

1. Crea una **Sales Invoice** normalmente in ERPNext
2. Seleziona **Tipo di Documento** (es. TD01 per fattura)
3. Dopo il Submit, clicca **"Genera e-Invoice"**
4. L'XML viene generato, validato e salvato

### Fatturazione Passiva

#### Importazione Manuale
1. Vai in **Fattura Fornitori SDI** → Nuovo
2. Carica il file XML della fattura
3. Il sistema estrae automaticamente dati fornitore e righe
4. Clicca **"Importa Fattura"** per creare Purchase Invoice

#### Creazione da PO/PR
1. Apri una Fattura SDI con stato "Da importare"
2. Se esistono Purchase Orders o Receipts aperti, vengono mostrati
3. Clicca **"Crea Fattura"** sul documento desiderato
4. La Purchase Invoice viene creata automaticamente e collegata

### Registri IVA

1. Vai in **Reports** → **Registro IVA Vendite** (o Acquisti)
2. Seleziona Company e periodo (From Date / To Date)
3. Clicca **Refresh**
4. Esporta in Excel, PDF o CSV

## 🔌 Sistema Provider

Italian Invoice supporta diversi provider SDI tramite architettura pluggabile:

- **Manual** (default): Salva XML localmente in `private/files/sdi_manual/`
- **OpenAPI**: Richiede app `openapi` per invio automatico
- **Custom**: Implementa il tuo provider estendendo `SDIProvider`

### Provider Manual (Test e Sviluppo)

Perfetto per test senza dipendenze esterne:
- XML salvati localmente
- UUID generato per ogni fattura
- Nessun servizio esterno richiesto

### Provider OpenAPI

Per invio automatico al SDI:

```bash
bench get-app openapi
bench --site [nome-sito] install-app openapi
```

Poi imposta Provider SDI = "OpenAPI" in Company.

## 📊 Struttura Dati

### DocTypes Principali

- **Transazione SDI**: Tracking stato fatture inviate al SDI
- **Fattura Fornitori SDI**: Buffer fatture passive ricevute
- **Payment Rounding Log**: Audit trail arrotondamenti pagamenti
- **Stato Fattura Elettronica**: Master data stati SDI
- **Tipologia di documento e-Invoice**: Tipi documento (TD01-TD06)
- **Motivo esenzione IVA**: Codici N1-N7 con sotto-codici

### Custom Fields

L'app aggiunge ~80 campi custom a DocTypes ERPNext esistenti:

- **Company**: Codice SDI, Provider, Regime Fiscale, Payment Rounding Threshold
- **Sales Invoice**: Tipo documento, UUID, Causale, Codice Destinatario
- **Purchase Invoice**: UUID, Link Fattura SDI, Bollo virtuale
- **Customer**: Codice SDI, PEC, Lettera d'Intento
- **Supplier**: Fiscal Code, VAT Number
- **Invoice Items**: Natura IVA, CIG, CUP, Ritenuta

## 🛠️ Arrotondamento Pagamenti

Sistema automatico dual-stage per gestire differenze minime nei pagamenti:

**Esempio**: Pagamento 200,490€ per fattura 200,495€
1. Sistema alloca automaticamente 200,495€ (importo completo fattura)
2. Gestisce differenza di 0,005€ con riga deduction automatica
3. Crea log in Payment Rounding Log per audit trail

**Configurazione richiesta**:
- `payment_rounding_threshold` in Company (default 0.50€)
- `round_off_account` configurato

## 📝 Validazione XML

Sistema multi-livello con feedback chiaro:

- ✅ Validazione struttura XML
- ✅ Conformità schema XSD FatturaPA v1.2.1
- ✅ Business rules (P.IVA, Codice Fiscale, importi)
- ✅ Messaggi di errore user-friendly con percorsi XML

Invece di errori tecnici XSD, ricevi messaggi chiari:
```
❌ Il valore "COMO" non rispetta il formato richiesto nel campo Provincia
   (percorso: FatturaElettronicaHeader → CessionarioCommittente → Sede → Provincia)
💡 Verifica che il valore rispetti il formato richiesto
```

## 🔍 API Reference

### Fatturazione Attiva

```python
# Genera XML fattura
xml = frappe.call("italian_invoice.utilities.fatture.get_xml",
                  invoice_name="SINV-00001",
                  doctype="Sales Invoice")

# Invia al SDI
result = frappe.call("italian_invoice.utilities.fatture.send_to_sdi",
                     invoice_name="SINV-00001",
                     doctype="Sales Invoice")
```

### Fatturazione Passiva

```python
# Parse XML fattura fornitore
from italian_invoice.utilities import fatture_passive

invoice_data = fatture_passive.parse_xml_invoice(xml_content)

# Crea Purchase Invoice
result = fatture_passive.process_supplier_invoice(
    invoice_data=json.dumps(invoice_data),
    fattura_fornitori_sdi="FATT-SDI-00001"
)
```

## 🐛 Troubleshooting

### Errori Comuni

**"Round Off Account non trovato"**
- Configura `round_off_account` in Company
- Crea account arrotondamenti se non esiste

**"Fattura SDI non si collega a Purchase Invoice"**
- Verifica che `bill_no` nella PI corrisponda al numero fattura SDI
- Controlla che Tax ID del fornitore sia corretto

**"Validazione XML fallisce"**
- Provincia: codice 2 caratteri (es. "MI" non "Milano")
- CAP: esattamente 5 cifre
- P.IVA: 11 cifre per Italia
- Codice SDI: esattamente 7 caratteri

### Debug Mode

```bash
# Abilita developer mode
bench --site [sito] set-config developer_mode 1
bench --site [sito] clear-cache
bench restart
```

Log utili:
- `logs/[sito]/error.log`
- `logs/[sito]/background_jobs.log`

## 🤝 Contribuire

Contribuzioni benvenute! Leggi [CONTRIBUTING.md](CONTRIBUTING.md) per:

- Setup ambiente di sviluppo
- Convenzioni di codice (Python PEP 8, type hints, DRY, KISS)
- Testing e commit conventions
- Come implementare nuovi provider SDI

### Quick Start Contribuzioni

```bash
# Fork e clone
git clone https://github.com/[your-username]/italian_invoice.git
cd italian_invoice

# Crea branch
git checkout -b feature/AmazingFeature

# Sviluppa e testa
bench --site [test-site] run-tests --app italian_invoice

# Commit
git commit -m "feat(scope): description"

# Push e Pull Request
git push origin feature/AmazingFeature
```

## 📚 Risorse

- [Specifiche SDI](https://www.fatturapa.gov.it/it/norme-e-regole/documentazione-fattura-elettronica/)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe Framework](https://frappeframework.com)
- [CONTRIBUTING.md](CONTRIBUTING.md) - Guida completa per sviluppatori

## 🔒 Privacy & Terms

- **[Privacy Policy](PRIVACY.md)** - Come gestiamo i tuoi dati
- **[Terms of Service](TERMS.md)** - Condizioni d'uso dell'app

**Privacy in breve:**
- ✅ Tutti i dati rimangono nel tuo database ERPNext
- ✅ Nessun dato inviato a Solede SA
- ✅ Integrazioni esterne solo se configurate da te
- ✅ Codice open source e verificabile

**Terms in breve:**
- ✅ Software gratuito e open source (AGPLv3)
- ✅ Fornito "AS IS" senza garanzie
- ✅ Sei responsabile della conformità fiscale
- ✅ Supporto tramite community GitHub

## 📄 License

GNU Affero General Public License v3.0 - vedi [LICENSE](LICENSE)

Copyright (C) 2024-2025 Solede SA and contributors

Puoi usare, modificare e distribuire liberamente. Se offri come servizio web/SaaS, DEVI condividere il codice sorgente modificato.

---

**Sviluppato da Solede SA** | [GitHub Issues](https://github.com/Solede-SA/italian_invoice/issues) | info@solede.com
