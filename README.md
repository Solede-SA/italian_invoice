# Italian Invoice

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Frappe](https://img.shields.io/badge/Frappe-v15+-blue.svg)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-v15+-green.svg)](https://erpnext.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

App Frappe/ERPNext completa per la gestione della **Fatturazione Elettronica Italiana** conforme allo standard **FatturaPA** e al **Sistema di Interscambio (SDI)**.

## 📋 Panoramica

Italian Invoice trasforma ERPNext in una soluzione completa per la fatturazione elettronica italiana, gestendo l'intero ciclo di vita delle fatture attive e passive con conformità allo standard SDI.

### 💡 Caratteristiche Principali

- ✅ **~4,700 linee di codice Python** produzione-ready
- ✅ **8 Custom DocTypes** per gestione completa workflow
- ✅ **80+ Custom Fields** integrati seamlessly con ERPNext
- ✅ **Validazione XML multi-livello** con messaggi user-friendly
- ✅ **Architettura provider pluggabile** per diversi servizi SDI
- ✅ **Auto-link intelligente** fatture passive con Purchase Invoices
- ✅ **Arrotondamento pagamenti automatico** con audit trail completo
- ✅ **Supporto lettera d'intento** con esenzione IVA automatica
- ✅ **Delivery Note billing gap management** per DDT
- ✅ **Zero dipendenze esterne** (provider Manual built-in)

### 🎯 Cosa Risolve

**Per Fatturazione Attiva**:
- Generazione XML FatturaPA v1.2 conformi allo standard SDI
- Validazione automatica con feedback chiari su errori
- Invio automatico o manuale tramite provider configurabili
- Tracking completo stato transazioni con notifiche SDI
- Gestione Credit/Debit Notes, autofatture, split payment

**Per Fatturazione Passiva**:
- Import automatico XML fornitori via webhook o upload
- Parsing intelligente dati fornitore e righe fattura
- Auto-link con Purchase Orders/Receipts aperti
- Creazione Purchase Invoice con un click da PO/PR esistenti
- Sincronizzazione automatica stato fattura SDI ↔ Purchase Invoice
- Matching fornitore basato su P.IVA con fallback su nome

**Per Gestione Pagamenti**:
- Arrotondamento automatico differenze entro soglia configurabile
- Gestione `unallocated_amount` e `difference_amount` trasparente
- Creazione automatica righe deduction con account configurato
- Payment Rounding Log per audit e compliance
- Messaggi chiari informativi e warning durante workflow

**Per Compliance e Audit**:
- Audit trail completo di tutte le transazioni SDI
- Log arrotondamenti pagamenti tracciabili
- Validazione business rules secondo normativa italiana
- Gestione regimi fiscali speciali (forfettario, semplificato, etc.)
- Supporto esenzioni IVA con codici normativi (N1-N7)

## 🚀 Funzionalità

### Fatturazione Attiva
- ✅ **Generazione XML** fatture elettroniche conformi allo standard SDI
- ✅ **Validazione avanzata** con messaggi di errore chiari e percorsi XML
- ✅ **Supporto documenti** Sales Invoice, Credit Note, Debit Note
- ✅ **Tracking transazioni** con stato invio e notifiche SDI

### Fatturazione Passiva
- ✅ **Importazione automatica** fatture fornitori da XML
- ✅ **Creazione Supplier** automatica o matching esistenti
- ✅ **Mapping articoli** personalizzabile per linea fattura
- ✅ **Gestione IVA** con riconoscimento automatico aliquote
- ✅ **Auto-link intelligente** Purchase Invoice ↔ Fattura SDI basato su bill_no + tax_id
- ✅ **Integrazione PO/PR** con visualizzazione documenti aperti e creazione diretta fatture
- ✅ **Sincronizzazione stato** automatica tra Purchase Invoice e Fattura SDI
- ✅ **UI ottimizzata** per importazione manuale con preview prodotti formattata

### Gestione Documenti di Trasporto (DDT)
- ✅ **Monitoraggio billing gap** per differenze di fatturazione
- ✅ **Force billing completion** per piccole differenze (< 1 EUR)
- ✅ **Audit log** completo per tracciabilità modifiche
- ✅ **Reversibilità** delle operazioni di aggiustamento

### Arrotondamento Pagamenti
- ✅ **Arrotondamento automatico** per piccole differenze entro soglia configurabile
- ✅ **Gestione deduzioni** con creazione automatica righe di arrotondamento
- ✅ **Validazione submit** blocca se differenza supera soglia
- ✅ **Audit trail** completo con Payment Rounding Log
- ✅ **Configurazione per Company** con payment_rounding_threshold personalizzabile
- ✅ **Messaggi chiari** informativi durante salvataggio e warning se soglia superata

### Supporto Lettera d'Intento
- ✅ **Rilevamento automatico** clienti con lettera d'intento attiva
- ✅ **Esenzione IVA automatica** con codice N3.5 per articoli a tasso zero
- ✅ **Bollo virtuale** abilitato automaticamente per fatture con lettera d'intento

### Sistema Provider
- ✅ **Architettura pluggabile** per diversi servizi SDI
- ✅ **Provider Manual** per test e sviluppo locale
- ✅ **Provider OpenAPI** per invio automatico (richiede app openapi)
- ✅ **Support multi-company** con configurazioni separate

## 📦 Installazione

### Requisiti
- Frappe Framework v15+
- ERPNext v15+
- Python 3.10+

### Installazione Base

```bash
# Ottieni l'app
bench get-app italian_invoice

# Installa nell'ambiente
bench --site [nome-sito] install-app italian_invoice

# Applica le modifiche
bench --site [nome-sito] migrate
```

## 🔧 Configurazione

### 1. Configurazione Company

Dopo l'installazione, configura la tua Company:

1. Vai in **Company** → Seleziona la tua azienda
2. Compila i campi nella sezione **Tax**:
   - **Tax ID**: Partita IVA (senza IT)
   - **Fiscal Code**: Codice Fiscale
   - **Fiscal Regime**: Regime fiscale
   - **Codice Sistema Interscambio**: Il tuo codice SDI

### 2. Selezione Provider SDI

Nel campo **Provider SDI** della Company, scegli:

- **Manual** (default): Salva XML localmente, ideale per test
- **OpenAPI**: Richiede app `openapi` installata (invio automatico)
- **Custom**: Per provider personalizzati

## 🔗 Integrazione con ERPNext

Italian Invoice si integra perfettamente con ERPNext estendendo le funzionalità native:

### Documenti Estesi
- **Sales Invoice** → Fattura Elettronica B2B/B2C/PA
- **Purchase Invoice** → Importazione fatture passive e autofatture
- **Customer/Supplier** → Dati fiscali italiani (P.IVA, Codice Fiscale, PEC, SDI)
- **Company** → Configurazione regime fiscale e dati SDI

### Workflow Fatturazione Attiva
1. **Creazione Fattura** → Standard ERPNext workflow
2. **Submit Documento** → Validazione dati fiscali
3. **Generazione XML** → Click su "Genera e-Invoice"
4. **Invio SDI** → Automatico con provider configurato
5. **Tracking** → Notifiche SDI in "Transazione SDI"

### Workflow Fatturazione Passiva

#### Flusso Standard
1. **Ricezione XML** → Via webhook o upload manuale in Fattura Fornitori SDI
2. **Parsing automatico** → Estrazione dati da XML (numero, importo, fornitore, righe)
3. **Visualizzazione PO/PR aperti** → Se esistono documenti aperti per il fornitore
4. **Creazione Purchase Invoice** → Manuale o da PO/PR esistente
5. **Auto-link e sincronizzazione** → Collegamento automatico tramite bill_no + tax_id
6. **Aggiornamento stato** → Fattura SDI passa a "Importata" automaticamente

#### Creazione da PO/PR (Opzionale)
Quando apri una Fattura SDI con stato "Da importare":
- Il sistema mostra automaticamente eventuali **Purchase Orders** e **Purchase Receipts** aperti per quel fornitore
- Puoi creare la Purchase Invoice direttamente dal documento con un click
- I dati della fattura (bill_no, bill_date) vengono auto-popolati dalla Fattura SDI
- Gli articoli vengono precompilati dal PO/PR selezionato

#### Auto-link Intelligente
Quando effettui il submit di una Purchase Invoice:
- Il sistema cerca automaticamente una Fattura SDI con stesso `bill_no` per quel fornitore (tramite tax_id)
- Se trovata, la Purchase Invoice viene collegata alla Fattura SDI
- Lo stato della Fattura SDI passa automaticamente a "Importata"
- In caso di cancellazione della PI, il link viene rimosso e lo stato torna a "Da importare"

## 📝 Utilizzo

### Generazione Fattura Elettronica (Attiva)

#### Sales Invoice
1. Crea una **Sales Invoice** in ERPNext
2. Compila i dati standard (Customer, Items, etc.)
3. Seleziona **Tipo di Documento** (es. TD01 per fattura normale)
4. Dopo il Submit, clicca **"Genera e-Invoice"**
5. L'XML viene generato, validato e inviato secondo il provider configurato

#### Note di Credito/Debito
1. Crea una **Sales Invoice** con importo negativo (Credit Note) o positivo (Debit Note)
2. Seleziona il tipo documento appropriato (TD04, TD05)
3. Collega alla fattura originale se richiesto
4. Procedi con generazione XML

### Importazione Fatture Passive

#### Via UI (Manuale)
1. Vai in **Fattura Fornitori SDI** → Nuovo
2. Carica il file XML della fattura
3. Il sistema estrae automaticamente:
   - Partita IVA e denominazione fornitore
   - Numero fattura e importo totale
   - Righe prodotti/servizi con importi
4. **Se esistono PO/PR aperti** per il fornitore, vengono mostrati in una tabella con:
   - Numero documento e importo
   - Pulsante "Crea Fattura" per creazione diretta
5. **Importazione Manuale**: Clicca "Importa Fattura" per:
   - Creare/selezionare il fornitore
   - Mappare manualmente gli articoli con preview formattata
   - Creare la Purchase Invoice

#### Importazione da PO/PR Esistenti
1. Dalla Fattura SDI, clicca "Crea Fattura" sul PO/PR desiderato
2. Il sistema crea automaticamente la Purchase Invoice con:
   - Righe precompilate dal documento origine
   - Bill No e Bill Date dalla Fattura SDI
3. Completa eventuali dati mancanti e fai il submit
4. L'auto-link collega automaticamente la PI alla Fattura SDI

#### Via API (Automatico con OpenAPI)
```python
# Le fatture arrivano automaticamente via webhook
# e vengono processate in background
```

#### UI Migliorata per Mapping Prodotti
Durante l'importazione manuale, ogni prodotto viene mostrato con:
- **Titolo**: "Prodotto presente in Fattura"
- **Descrizione**: Nome del prodotto in grassetto
- **Importo**: Formattato con colori (verde = normale, giallo = valore zero)
- **Campi di selezione**: Item e Conto di costo con auto-completamento
- **Pulsante**: "Crea Nuovo Item" per articoli non esistenti

### Provider Manual (Default)

Con il provider Manual:
- Gli XML sono salvati in `sites/[nome-sito]/private/files/sdi_manual/`
- Ogni fattura genera un UUID univoco per testing
- Nessun servizio esterno richiesto
- Ideale per sviluppo e test

### Provider OpenAPI

Se hai installato anche l'app `openapi`:

```bash
bench get-app openapi
bench --site [nome-sito] install-app openapi
```

Poi:
1. Imposta **Provider SDI** = "OpenAPI" nella Company
2. Configura token e webhook nel tab aggiuntivo
3. Le fatture vengono inviate automaticamente al SDI

## 🔌 Sistema Provider

### Architettura

```
italian_invoice/
├── providers/
│   ├── base.py           # Interfaccia SDIProvider
│   ├── manual_provider.py # Provider locale/test
│   └── openapi_provider.py # Provider servizi OpenAPI
```

### Creare un Provider Custom

1. Crea una classe che eredita da `SDIProvider`:

```python
from italian_invoice.providers.base import SDIProvider

class MyCustomProvider(SDIProvider):
    def send_invoice(self, xml_content, doc, company):
        # Implementa invio
        pass

    def download_invoice(self, uuid, format, company):
        # Implementa download
        pass

    # ... altri metodi richiesti
```

2. Registra nel factory method o usa campo JSON config

## 📊 DocTypes e Struttura Dati

### DocTypes Principali (8 Custom DocTypes)

#### 1. Transazione SDI
Traccia lo stato di ogni fattura inviata al SDI:
- **UUID**: Identificativo univoco transazione
- **Stato Invio**: Stato corrente (Inviata, Consegnata, Scartata, etc.)
- **Fattura**: Link al documento ERPNext originale
- **Notifiche**: Tabella child con storico notifiche SDI
- **Ultima Notifica**: JSON con dettagli ultima notifica
- **File Path**: Percorso XML generato
- **Creation/Modified**: Timestamp automatici per audit trail

#### 2. Fattura Fornitori SDI
Buffer per fatture passive ricevute con gestione stato automatica:
- **Dati Fattura**: JSON completo del XML parseato
- **P.IVA/Denominazione**: Dati fornitore per matching automatico
- **Numero Fattura**: Auto-estratto dal JSON (read-only, visibile in list view)
- **Importo Totale**: Somma imponibili auto-calcolata (read-only)
- **Stato**: Da importare/Importata (read-only, gestito via hooks)
- **Documenti Aperti**: Campo HTML dinamico che mostra PO/PR aperti con pulsanti azione
- **UUID**: Identificativo SDI della fattura
- **Purchase Invoice**: Link auto-popolato durante on_submit della PI collegata
- **File Attachment**: XML originale allegato al documento

#### 3. Stato Fattura Elettronica
Master data degli stati SDI con codifiche ufficiali:
- Stati supportati: "Inviata", "Consegnata", "Scartata", "MC - Mancata Consegna", "RC - Ricevuta Consegna", "NS - Notifica Scarto", "EC - Esito Committente"
- Utilizzato per normalizzazione stato nelle Transazioni SDI
- Personalizzabile per aggiungere stati custom

#### 4. Tipologia di documento e-Invoice
Master data dei tipi documento FatturaPA con validazioni business:
- **TD01**: Fattura
- **TD02**: Acconto/Anticipo su fattura
- **TD03**: Acconto/Anticipo su parcella
- **TD04**: Nota di Credito
- **TD05**: Nota di Debito
- **TD06**: Parcella
- Campi: Codice, Descrizione, Note
- Validazioni automatiche per Credit/Debit Notes

#### 5. Motivo esenzione IVA
Codifiche ufficiali per esenzioni IVA con riferimenti normativi (N1-N7):
- **N1**: Escluse ex art. 15
- **N2**: Non soggette
- **N3**: Non imponibili (con 5 sotto-codici)
  - **N3.1**: Non imponibili - esportazioni
  - **N3.2**: Non imponibili - cessioni intracomunitarie
  - **N3.3**: Non imponibili - cessioni verso San Marino
  - **N3.4**: Non imponibili - operazioni assimilate alle cessioni all'esportazione
  - **N3.5**: Non imponibili - a seguito di dichiarazioni d'intento (lettera d'intento)
  - **N3.6**: Non imponibili - altre operazioni che non concorrono alla formazione del plafond
- **N4**: Esenti
- **N5**: Regime del margine / IVA non esposta in fattura
- **N6**: Inversione contabile
- **N7**: IVA assolta in altro stato UE
- Usato per mapping automatico esigibilità IVA

#### 6. Payment Rounding Log
Audit trail per arrotondamenti automatici nei pagamenti:
- **Payment Entry**: Link al documento pagamento
- **Reference Invoice**: Fattura originale (Sales/Purchase Invoice)
- **Reference Type**: Tipo documento di riferimento
- **Original Amount**: Importo originale allocato
- **Rounded Amount**: Importo effettivamente pagato
- **Difference**: Differenza arrotondata (sempre ≤ soglia configurata)
- **Creation**: Timestamp automatico per tracciabilità
- Creato automaticamente durante submit del Payment Entry se presente arrotondamento

#### 7. Delivery Note Billing Gap
Gestione differenze di fatturazione nei DDT:
- **Delivery Note**: Link al DDT originale
- **Item**: Articolo con differenza
- **Billed Qty**: Quantità fatturata
- **Delivered Qty**: Quantità consegnata
- **Gap Amount**: Differenza in valore
- **Status**: Draft/Completed/Cancelled
- **Force Completed**: Flag per chiusura forzata (se gap < 1 EUR)
- **Reason**: Motivazione della differenza
- Integrato con workflow Sales Invoice → Delivery Note

#### 8. Notifiche SDI (Child Table)
Storico notifiche ricevute dal Sistema di Interscambio:
- **Tipo Notifica**: RC, NS, MC, EC, etc.
- **Data Ricezione**: Timestamp notifica
- **Descrizione**: Dettagli notifica
- **Messaggio SDI**: Messaggio completo da SDI
- Parent: Transazione SDI

## 🔍 Campi Custom Aggiunti (via Fixtures)

L'app aggiunge numerosi campi custom ai DocTypes ERPNext esistenti tramite il sistema fixtures. Tutti i campi hanno `module: "Italian Invoice"` per gestione centralizzata.

### Company (Configurazione Fatturazione Elettronica)
- `custom_codice_sistema_interscambio`: Codice destinatario SDI (7 caratteri)
- `custom_sdi_provider`: Selezione provider (Manual/OpenAPI/Custom)
- `custom_sdi_provider_config`: Config JSON per provider personalizzati
- `custom_fiscal_regime`: Regime fiscale per FatturaPA
- `payment_rounding_threshold`: Soglia arrotondamento automatico pagamenti (Currency, default 0.50)

### Sales Invoice (Fatturazione Attiva)
- `custom_tipo_di_documento`: Link a "Tipologia di documento e-Invoice" (TD01, TD04, etc.)
- `custom_transazione_sdi`: Link a "Transazione SDI" per tracking
- `custom_uuid`: UUID fattura inviata al SDI
- `custom_causale`: Causale documento (testo libero)
- `custom_art73`: Flag per Art. 73 DPR 633/72
- `custom_codice_destinatario`: Override codice destinatario (per fattura specifica)
- `custom_pec_destinatario`: PEC destinatario alternativa

### Purchase Invoice (Fatturazione Passiva)
- `custom_tipo_di_documento`: Tipo documento ricevuto
- `custom_uuid`: UUID fattura SDI ricevuta
- `custom_fattura_fornitore_sdi`: Link a "Fattura Fornitori SDI" (auto-popolato)
- `custom_protocollo_generale`: Numero protocollo generale
- `custom_bollo_virtuale`: Importo bollo virtuale applicato

### Customer (Dati Fiscali e Configurazione)
- `custom_tipo_fattura_elettronica`: Tipo fattura default (B2B/B2C/PA)
- `custom_vat_collectability`: Esigibilità IVA (I=Immediata, D=Differita, S=Scissione)
- `custom_codice_destinatario`: Codice SDI cliente (7 caratteri)
- `custom_pec`: PEC del cliente
- `custom_fiscal_code`: Codice Fiscale (per PA e privati)
- **Campi Lettera d'Intento**:
  - `custom_has_letter_of_intent`: Flag attivazione lettera d'intento
  - `custom_letter_of_intent_number`: Numero protocollo lettera
  - `custom_letter_of_intent_date`: Data emissione
  - `custom_letter_of_intent_amount`: Importo plafond
  - `custom_letter_of_intent_expiry`: Data scadenza

### Supplier (Dati Fiscali)
- `custom_fiscal_code`: Codice Fiscale fornitore
- `custom_vat_number`: P.IVA (separata da tax_id per formattazione)
- `custom_sdi_code`: Codice SDI fornitore (per fatturazione attiva ciclo passivo)

### Delivery Note (Gestione DDT)
- `custom_billing_gap_detected`: Flag rilevamento gap fatturazione
- `custom_billing_gap_amount`: Importo totale gap (Currency, read-only)
- `custom_force_billing_complete`: Flag chiusura forzata billing
- Integrazione con DocType "Delivery Note Billing Gap"

### Sales Invoice Item / Purchase Invoice Item (Righe Fattura)
- `custom_natura_iva`: Link a "Motivo esenzione IVA" (N1-N7)
- `custom_riferimento_amministrazione`: Riferimento PA (per Pubblica Amministrazione)
- `custom_codice_cig`: CIG (Codice Identificativo Gara)
- `custom_codice_cup`: CUP (Codice Unitario Progetto)
- `custom_ritenuta`: Flag ritenuta applicata
- `custom_aliquota_ritenuta`: Aliquota ritenuta (Percent)
- `custom_causale_ritenuta`: Causale ritenuta (testo)

### Payment Entry (Arrotondamento Automatico)
- Campi gestiti via hooks, non custom fields
- Utilizza tabella nativa `deductions` per arrotondamenti
- Collegamento automatico a "Payment Rounding Log" per audit

### Quotation (Preventivi)
- `custom_tipo_documento`: Tipo documento preventivo
- JavaScript custom per UI enhancements
- File: `italian_invoice/public/js/custom_quotation.js`

### Item (Articoli)
- `custom_codice_tipo_servizio`: Codice tipo servizio per fatture PA
- `custom_natura_default`: Natura IVA default per articolo

### Address (Indirizzi)
- Validazioni automatiche per formato italiano
- Provincia con codice a 2 caratteri (es. "MI", "RM")
- CAP con formato 5 cifre

## 🧪 Testing e Debug

### Test Generazione XML

```python
# Dal bench console
import frappe

# Test generazione XML
doc = frappe.get_doc("Sales Invoice", "SINV-00001")
doc.custom_tipo_di_documento = "TD01"
doc.save()

# Genera e valida XML (la validazione avviene automaticamente)
xml = frappe.call("italian_invoice.utilities.fatture.get_xml",
                  "SINV-00001", "Sales Invoice")
print(xml[:500])  # Prime 500 caratteri

# La validazione XSD è automatica durante la generazione
# Se l'XML non è valido, verrà sollevata un'eccezione
```

### Test Import Fatture Passive

```python
# Test parsing XML fattura fornitore
from italian_invoice.utilities import fatture_passive

# Con XML di esempio
with open("fattura_esempio.xml", "r") as f:
    xml_content = f.read()

# Parse XML
invoice_data = fatture_passive.parse_xml_invoice(xml_content)
print(f"Fornitore: {invoice_data['supplier']['name']}")
print(f"Totale: {invoice_data['summary']['total']}")

# Test creazione Purchase Invoice
result = fatture_passive.process_supplier_invoice(
    json.dumps(invoice_data),
    fattura_fornitori_sdi="TEST-001"
)
print(f"Purchase Invoice creata: {result['name']}")
```

### Sistema di Validazione

Il sistema di validazione XML è stato completamente riprogettato per fornire feedback chiaro e utile:

#### Validazione Multi-livello
- **Struttura XML**: Verifica che il file sia XML valido
- **Schema XSD**: Conformità allo standard FatturaPA v1.2
- **Business Rules**: Controlli specifici (P.IVA, CF, date, importi)

#### Messaggi di Errore Migliorati
Invece di errori tecnici XSD, ora ricevi messaggi chiari:
```
❌ Il valore "COMO" non rispetta il formato richiesto nel campo Provincia
   (percorso: FatturaElettronicaHeader → CessionarioCommittente → Sede → Provincia)
💡 Verifica che il valore rispetti il formato richiesto
```

#### Architettura Validazione
- `italian_invoice/validation/xml_validator.py`: Classe XMLInvoiceValidator
- `italian_invoice/validation/error_formatter.py`: Formattazione errori user-friendly
- Report dettagliati con errori critici e warning non bloccanti
- Logging strutturato per debug

## 🛠️ Architettura Tecnica

### Struttura App (~4,700 linee Python)
```
italian_invoice/
├── italian_invoice/
│   ├── providers/              # Sistema provider pluggabile (~500 linee)
│   │   ├── __init__.py
│   │   ├── base.py            # Classe astratta SDIProvider
│   │   ├── manual_provider.py # Provider test/sviluppo
│   │   └── openapi_provider.py # Integrazione OpenAPI.it
│   │
│   ├── validation/             # Sistema validazione XML (~800 linee)
│   │   ├── __init__.py
│   │   ├── xml_validator.py   # Validatore multi-livello con XSD
│   │   └── error_formatter.py # Formattazione errori user-friendly
│   │
│   ├── utilities/              # Core business logic (~2,000 linee)
│   │   ├── __init__.py
│   │   ├── fatture.py         # Generazione XML attive (FatturaPA)
│   │   └── fatture_passive.py # Import, parsing, auto-link passive
│   │
│   ├── crud_events/            # Document lifecycle hooks (~400 linee)
│   │   ├── __init__.py
│   │   ├── sales_invoice.py   # before_save, validate, on_cancel
│   │   │   ├── before_save.py # Lettera d'intento, bollo virtuale
│   │   │   ├── validate.py    # Validazioni business
│   │   │   └── on_cancel.py   # Cleanup transazioni
│   │   └── payment_entry.py   # Payment rounding automation
│   │
│   ├── doctype/                # 8 Custom DocTypes + controllers
│   │   ├── transazione_sdi/
│   │   ├── fattura_fornitori_sdi/
│   │   ├── stato_fattura_elettronica/
│   │   ├── tipologia_di_documento_e_invoice/
│   │   ├── motivo_esenzione_iva/
│   │   ├── payment_rounding_log/
│   │   ├── delivery_note_billing_gap/
│   │   └── notifiche_sdi/
│   │
│   ├── fixtures/              # Custom fields e Property Setters
│   │   └── custom_field.json # ~80 campi custom
│   │
│   ├── public/                # Client-side JavaScript (~600 linee)
│   │   └── js/
│   │       ├── custom_sales_invoice.js
│   │       ├── custom_purchase_invoice.js
│   │       ├── custom_quotation.js
│   │       └── custom_delivery_note.js
│   │
│   └── hooks.py              # Event bindings e configurazione
│
├── README.md                  # Questo file
└── license.txt               # MIT License
```

### Metriche Codebase
- **Linee Python totali**: ~4,700
- **Custom DocTypes**: 8
- **Custom Fields**: ~80
- **Document Hooks**: 6 DocTypes estesi
- **API Endpoints**: 15+ whitelisted methods
- **JavaScript Client**: ~600 linee
- **Test Coverage**: Provider Manual incluso per testing

### Flusso Dati

#### Fatturazione Attiva
```
ERPNext Invoice → italian_invoice.get_xml() → XMLInvoiceValidator → Provider.send_invoice() → SDI
                                ↓                      ↓
                        Generazione XML        Validazione multi-livello
                                ↓                      ↓
                        File XML validato     Report errori user-friendly
                                ↓
                        Transazione SDI (tracking)
```

#### Fatturazione Passiva
```
SDI → Webhook/Upload → Fattura Fornitori SDI → Parse XML → Purchase Invoice
                                ↓                               ↓
                        PO/PR Detection                   on_submit hook
                                ↓                               ↓
                        UI: Crea Fattura                Auto-link by bill_no
                                                                ↓
                                                        Update Fattura SDI
                                                        stato → "Importata"
```

### Hooks e Auto-link

Il sistema utilizza hooks di Frappe per gestire automaticamente la sincronizzazione:

#### on_submit (Purchase Invoice)
```python
# italian_invoice/utilities/fatture_passive.py
def on_purchase_invoice_submit(doc, method):
    # Cerca Fattura SDI con stesso bill_no per questo fornitore
    # Basato su: bill_no + supplier.tax_id
    # Se trovata: collega PI e aggiorna stato a "Importata"
```

#### on_cancel (Purchase Invoice)
```python
def on_purchase_invoice_cancel(doc, method):
    # Rimuove il link dalla Fattura SDI
    # Riporta stato a "Da importare"
```

Questi hooks sono configurati in `hooks.py`:
```python
doc_events = {
    "Sales Invoice": {
        "before_save": "italian_invoice.crud_events.sales_invoice.before_save.execute",
        "validate": "italian_invoice.crud_events.sales_invoice.validate.execute",
        "on_cancel": "italian_invoice.crud_events.sales_invoice.on_cancel.execute",
    },
    "Payment Entry": {
        "validate": "italian_invoice.crud_events.payment_entry.handle_rounding",
        "before_submit": "italian_invoice.crud_events.payment_entry.validate_rounding_on_submit",
        "after_insert": "italian_invoice.crud_events.payment_entry.after_insert",
    },
    "Purchase Invoice": {
        "on_submit": "italian_invoice.utilities.fatture_passive.on_purchase_invoice_submit",
        "on_cancel": "italian_invoice.utilities.fatture_passive.on_purchase_invoice_cancel",
    },
}
```

## 🔌 API Reference

L'app espone diverse API whitelisted utilizzabili via Frappe RPC o REST.

### Fatturazione Attiva

#### `italian_invoice.utilities.fatture.get_xml`
Genera l'XML di una fattura elettronica.

**Parametri**:
- `invoice_name` (str): Nome del documento (es. "SINV-00001")
- `doctype` (str): Tipo documento ("Sales Invoice")

**Ritorna**: String XML FatturaPA validato

**Esempio**:
```python
xml = frappe.call("italian_invoice.utilities.fatture.get_xml",
                  invoice_name="SINV-00001",
                  doctype="Sales Invoice")
```

#### `italian_invoice.utilities.fatture.send_to_sdi`
Invia fattura al SDI tramite provider configurato.

**Parametri**:
- `invoice_name` (str): Nome fattura
- `doctype` (str): Tipo documento

**Ritorna**: Dict con UUID e stato transazione

**Esempio**:
```python
result = frappe.call("italian_invoice.utilities.fatture.send_to_sdi",
                     invoice_name="SINV-00001",
                     doctype="Sales Invoice")
# {'uuid': '...', 'status': 'Inviata', 'transazione': 'TRANS-SDI-00001'}
```

### Fatturazione Passiva

#### `italian_invoice.utilities.fatture_passive.parse_xml_invoice`
Estrae dati strutturati da XML fattura fornitore.

**Parametri**:
- `xml_content` (str): Contenuto XML FatturaPA

**Ritorna**: Dict con struttura:
```python
{
    'supplier': {
        'name': 'Fornitore S.p.A.',
        'tax_id': '12345678901',
        'fiscal_code': 'ABC12345',
        'address': {...}
    },
    'invoice': {
        'number': 'FATT-2025-001',
        'date': '2025-01-15',
        'type': 'TD01'
    },
    'items': [
        {
            'description': 'Articolo 1',
            'quantity': 10,
            'unit_price': 50.00,
            'tax_rate': 22,
            'total': 500.00
        }
    ],
    'summary': {
        'subtotal': 500.00,
        'tax': 110.00,
        'total': 610.00
    }
}
```

#### `italian_invoice.utilities.fatture_passive.process_supplier_invoice`
Crea Purchase Invoice da dati fattura SDI.

**Parametri**:
- `invoice_data` (str/dict): Dati fattura (JSON string o dict)
- `fattura_fornitori_sdi` (str): Nome documento Fattura Fornitori SDI
- `supplier_name` (str, optional): Nome fornitore esistente
- `item_mapping` (dict, optional): Mapping articoli {idx: item_code}

**Ritorna**: Dict con Purchase Invoice creata

**Esempio**:
```python
result = frappe.call(
    "italian_invoice.utilities.fatture_passive.process_supplier_invoice",
    invoice_data=json.dumps(invoice_data),
    fattura_fornitori_sdi="FATT-SDI-00001",
    supplier_name="Fornitore Spa",
    item_mapping={0: "ITEM-001", 1: "ITEM-002"}
)
# {'name': 'PINV-00001', 'status': 'Draft'}
```

#### `italian_invoice.utilities.fatture_passive.get_open_documents_for_supplier`
Ottiene PO/PR aperti per un fornitore.

**Parametri**:
- `supplier_name` (str): Nome fornitore
- `company` (str): Company

**Ritorna**: Dict con liste di PO e PR aperti

**Esempio**:
```python
docs = frappe.call(
    "italian_invoice.utilities.fatture_passive.get_open_documents_for_supplier",
    supplier_name="Fornitore Spa",
    company="My Company"
)
# {
#   'purchase_orders': [{'name': 'PO-00001', 'grand_total': 1000}],
#   'purchase_receipts': [{'name': 'PR-00001', 'grand_total': 800}]
# }
```

#### `italian_invoice.utilities.fatture_passive.create_purchase_invoice_from_document`
Crea Purchase Invoice da PO/PR esistente con dati da Fattura SDI.

**Parametri**:
- `source_document` (str): Nome PO o PR
- `source_doctype` (str): "Purchase Order" o "Purchase Receipt"
- `fattura_fornitori_sdi` (str): Nome Fattura SDI per bill_no/date

**Ritorna**: Purchase Invoice document (dict)

### Validazione e Utility

#### `italian_invoice.validation.xml_validator.validate_invoice_xml`
Valida XML FatturaPA con XSD e business rules.

**Parametri**:
- `xml_content` (str): XML da validare

**Ritorna**: Dict con risultato validazione
```python
{
    'valid': True/False,
    'errors': [...],  # Lista errori critici
    'warnings': [...] # Lista warning non bloccanti
}
```

### Webhook Endpoints (per Provider OpenAPI)

#### `POST /api/method/italian_invoice.providers.openapi_provider.handle_webhook`
Riceve notifiche SDI dal provider OpenAPI.

**Headers**:
- `X-Webhook-Token`: Token autenticazione

**Body**: JSON notifica SDI

**Risposta**: 200 OK se processata

### Payment Entry Rounding (Auto-eseguito via Hooks)

Le funzioni di arrotondamento NON sono whitelist ma eseguite automaticamente via document hooks:

- `handle_rounding(doc, method)`: Eseguito durante `validate`
- `validate_rounding_on_submit(doc, method)`: Eseguito durante `before_submit`
- `after_insert(doc, method)`: Crea Payment Rounding Log

**Configurazione Company richiesta**:
- `payment_rounding_threshold`: Soglia (default 0.50 EUR)
- `round_off_account`: Account contabile arrotondamenti
- `cost_center`: Centro di costo default

## ⚙️ Best Practices e Configurazione

### Configurazione Iniziale Raccomandata

#### 1. Company Setup
```python
# Via bench console
from frappe import get_doc

company = get_doc("Company", "Your Company")
company.custom_codice_sistema_interscambio = "0000000"  # Codice SDI
company.custom_fiscal_regime = "RF01"  # Regime ordinario
company.custom_sdi_provider = "Manual"  # Inizia con Manual per test
company.payment_rounding_threshold = 0.50  # Soglia arrotondamento 50 centesimi
company.round_off_account = "ARROTONDAMENTI PASSIVI"  # Account arrotondamenti
company.save()
```

#### 2. Master Data Setup
- **Stati Fattura**: Auto-creati durante migrate
- **Tipi Documento**: TD01-TD06 pre-configurati
- **Motivi Esenzione IVA**: N1-N7 con sotto-codici
- Verifica con: `bench --site [sito] console` → `frappe.get_all("Stato Fattura Elettronica")`

#### 3. Customer Configuration
Per ogni cliente che riceve fatture elettroniche:
- **B2B**: P.IVA obbligatoria, Codice SDI o PEC
- **B2C**: Codice SDI "0000000" e PEC opzionale
- **PA**: Codice IPA (6 caratteri), Codice Fiscale obbligatorio

#### 4. Account Configuration
Assicurati di avere questi account nel piano dei conti:
- Account arrotondamenti (es. "ARROTONDAMENTI PASSIVI")
- Account bollo virtuale (se applicabile)
- Account IVA per diverse aliquote (0%, 4%, 10%, 22%)

### Workflow Consigliati

#### Fatturazione Attiva (Standard Flow)
1. **Test con Provider Manual**: Valida generazione XML
2. **Verifica XML generato**: Controlla in `sites/[sito]/private/files/sdi_manual/`
3. **Analizza errori**: Sistema fornisce messaggi dettagliati con percorsi XML
4. **Switch a Provider produzione**: Dopo test OK, passa a OpenAPI o custom

#### Fatturazione Passiva (Flusso Ottimale)
1. **Setup webhook** (se OpenAPI): Ricezione automatica fatture
2. **Controllo manuale**: Apri Fattura SDI, verifica dati
3. **Check PO/PR aperti**: Sistema mostra documenti collegabili
4. **Creazione PI**: Da PO/PR se disponibile, altrimenti importazione manuale
5. **Verifica auto-link**: Sistema collega automaticamente PI a Fattura SDI

### Performance e Scalabilità

#### Limiti e Raccomandazioni
- **XML generazione**: ~200ms per fattura media (10 righe)
- **Validazione XSD**: ~100ms aggiuntivi
- **Import fatture**: ~500ms per fattura (incluso parsing e creazione supplier)
- **Webhook processing**: Asincrono, non blocca request

#### Ottimizzazioni
```python
# Batch processing per import massivo
from italian_invoice.utilities import fatture_passive

for xml_file in xml_files:
    frappe.enqueue(
        fatture_passive.process_xml_from_file,
        xml_path=xml_file,
        queue='long'  # Usa queue long per evitare timeout
    )
```

### Sicurezza

#### Provider Manual
- File salvati in `private/files/` (non accessibili via web)
- UUID generati con `uuid.uuid4()` (crittograficamente sicuri)
- Nessuna trasmissione dati esterni

#### Provider OpenAPI
- Token autenticazione via webhook headers
- Validazione firma webhook (se supportata)
- HTTPS obbligatorio per webhook endpoint

#### Dati Sensibili
- P.IVA e Codici Fiscali: validati ma non criptati (come da standard ERPNext)
- XML fatture: Stored as file attachments (visibili solo con permessi)
- Log transazioni: Audit trail completo per compliance

## 🔄 Migrazione da Versioni Precedenti

### Da versione con modulo "openapi"

Se stai aggiornando da una versione che utilizzava `openapi` come modulo per i DocType:

1. **Backup del database** (IMPORTANTE!)
   ```bash
   bench --site [nome-sito] backup --with-files
   ```

2. **Aggiorna il codice**:
   ```bash
   cd apps/italian_invoice
   git pull origin main
   cd ../..
   bench --site [nome-sito] migrate
   ```

3. **Verifica moduli**:
   - I DocType verranno automaticamente migrati al modulo "Italian Invoice"
   - Custom Fields mantengono module = "Italian Invoice"

4. **Test completo**:
   - Apertura Sales Invoice esistenti
   - Generazione XML di test
   - Apertura Purchase Invoice con link a Fattura SDI
   - Verifica Transazioni SDI storiche

### Da installazione senza italian_invoice

Se stai installando per la prima volta su sistema esistente:

1. **Backup** prima dell'installazione
2. **Install app**: `bench --site [sito] install-app italian_invoice`
3. **Migrate**: Automatico durante install
4. **Configura Company**: Campi custom saranno aggiunti
5. **Import Master Data**: Stati e Tipi documento auto-creati (se fixture abilitati)

## 🐛 Troubleshooting

### Errori Comuni

#### "Round Off Account non trovato"
```
Errore: Imposta Round Off Account in Company per abilitare l'arrotondamento automatico
```
**Soluzione**:
- Vai in Company → round_off_account
- Seleziona account arrotondamenti dal piano dei conti
- Se non esiste, crealo: Account Type = "Expense", Parent = "Indirect Expenses"

#### "Deductions rimangono dopo submit"
Il sistema ora gestisce automaticamente la persistenza delle deductions. Se vedi duplicati:
1. Cancella il Payment Entry
2. Verifica `payment_rounding_threshold` in Company (deve essere > 0)
3. Ricrea il pagamento

#### "Fattura SDI non si collega a Purchase Invoice"
Auto-link richiede match esatto su:
- `bill_no` della PI = numero fattura in Fattura SDI
- Tax ID del fornitore deve corrispondere

**Debug**:
```python
# Via bench console
frappe.db.sql("""
    SELECT name, numero_fattura, partita_iva
    FROM `tabFattura Fornitori SDI`
    WHERE stato = 'Da importare'
""")

frappe.db.sql("""
    SELECT name, bill_no, supplier
    FROM `tabPurchase Invoice`
    WHERE docstatus = 1 AND bill_no IS NOT NULL
""")
```

#### "Validazione XML fallisce con errori criptici"
Il sistema ora fornisce errori chiari, ma se vedi errori XSD raw:
1. Controlla log: `tail -f logs/[sito]/error.log`
2. Verifica dati obbligatori: P.IVA, Codice Fiscale, Codice SDI
3. Testa con XML esempio: usa Sample Sales Invoice

**Dati comuni che causano errori**:
- Provincia: Deve essere codice 2 caratteri (es. "MI" non "Milano")
- CAP: Esattamente 5 cifre
- P.IVA: 11 cifre per Italia
- Codice SDI: Esattamente 7 caratteri (o PEC valida)

#### "Provider OpenAPI non funziona"
1. Verifica app `openapi` installata: `bench list-apps`
2. Controlla token configurato in Company
3. Test webhook: `curl -X POST [webhook-url] -H "X-Webhook-Token: [token]"`
4. Log: `tail -f logs/[sito]/openapi.log`

### Debug Mode

Abilita debug dettagliato:

```python
# In site_config.json
{
    "developer_mode": 1,
    "logging": 2
}
```

```bash
# Riavvia
bench --site [sito] clear-cache
bench restart
```

### Log Files Utili

- `logs/[sito]/error.log`: Errori applicazione
- `logs/[sito]/frappe.log`: Log generale Frappe
- `logs/[sito]/background_jobs.log`: Processi asincroni (webhook, import)
- `logs/[sito]/bench.log`: Comandi bench (migrate, console)

## 🤝 Contribuire

Contribuzioni benvenute! Italian Invoice è un progetto open-source e migliora grazie alla community.

### Come Contribuire

1. **Fork del repository**
   ```bash
   git clone https://github.com/[your-username]/italian_invoice.git
   cd italian_invoice
   ```

2. **Setup ambiente di sviluppo**
   ```bash
   # Installa in development mode
   bench get-app italian_invoice --branch develop
   bench --site [test-site] install-app italian_invoice
   ```

3. **Crea branch per la feature**
   ```bash
   git checkout -b feature/AmazingFeature
   # oppure
   git checkout -b fix/ImportantBugFix
   ```

4. **Sviluppa e testa**
   - Scrivi codice seguendo le linee guida (sotto)
   - Testa localmente con Provider Manual
   - Verifica backward compatibility

5. **Commit con messaggi chiari**
   ```bash
   git commit -m "Add: Supporto per Regime Forfettario

   - Aggiunto campo custom_regime_forfettario in Company
   - Implementata validazione per fatture regime semplificato
   - Gestione automatica esenzione IVA per forfettari
   - Test con XML samples forniti da AdE

   Fixes #123"
   ```

6. **Push e Pull Request**
   ```bash
   git push origin feature/AmazingFeature
   ```
   - Apri PR su GitHub
   - Descrivi le modifiche in dettaglio
   - Riferisci issue correlate

### Linee Guida Sviluppo

#### Code Style
- **Python**: Segui PEP 8
  ```bash
  # Usa black per formatting
  black italian_invoice/
  # Usa pylint per linting
  pylint italian_invoice/
  ```
- **JavaScript**: Standard JS style
- **Naming**: snake_case per Python, camelCase per JS
- **Docstrings**: Obbligatori per funzioni pubbliche

#### Architettura
- **DRY**: Non duplicare logica, usa helper functions
- **KISS**: Mantieni semplicità, no over-engineering
- **No fallback silenziosi**: Mostra sempre errori all'utente
- **Separation of Concerns**:
  - `utilities/`: Business logic pura
  - `crud_events/`: Document lifecycle hooks
  - `validation/`: Validazione e controlli
  - `providers/`: Integrazioni esterne

#### Testing
```python
# Crea test per nuove funzionalità
# italian_invoice/tests/test_payment_rounding.py

import frappe
from frappe.tests.utils import FrappeTestCase

class TestPaymentRounding(FrappeTestCase):
    def test_rounding_within_threshold(self):
        # Setup
        company = frappe.get_doc("Company", "_Test Company")
        company.payment_rounding_threshold = 0.50

        # Test logic
        # ...

        # Assertions
        self.assertEqual(...)
```

```bash
# Esegui test
bench --site [sito] run-tests --app italian_invoice
```

#### Compatibilità
- **Frappe Framework**: v15+
- **ERPNext**: v15+
- **Python**: 3.10+
- **Backward compatibility**: Mantieni compatibilità con versioni precedenti dell'app

#### Documentazione
- **README**: Aggiorna per nuove feature importanti
- **Docstrings**: Documenta parametri e return values
- **API Reference**: Aggiungi nuovi endpoint pubblici
- **Commenti inline**: Solo per logica complessa, non ovvietà

#### Commit Messages
Formato consigliato:
```
Tipo: Breve descrizione (max 72 caratteri)

Descrizione dettagliata del cambiamento:
- Punto 1
- Punto 2
- Punto 3

Motivazione tecnica e contesto se necessario.

Fixes #issue_number
Related to #other_issue
```

**Tipi commit**:
- `Add:` Nuova funzionalità
- `Fix:` Bug fix
- `Update:` Modifica feature esistente
- `Refactor:` Refactoring senza cambi funzionali
- `Docs:` Solo documentazione
- `Test:` Aggiunta/modifica test
- `Perf:` Performance improvement
- `Chore:` Manutenzione (deps, build, etc.)

### Aree di Contribuzione

#### 🎯 Feature Requests
- Nuovi provider SDI (Aruba, Infocert, etc.)
- Export formati aggiuntivi (CSV, Excel report)
- Dashboard analytics per fatturazione
- Integrazione con sistemi contabili esterni

#### 🐛 Bug Reports
Quando segnali un bug, includi:
1. **Versioni**: Frappe, ERPNext, italian_invoice
2. **Steps to reproduce**: Passaggi precisi
3. **Expected vs Actual**: Comportamento atteso vs reale
4. **Screenshots**: Se pertinente
5. **Logs**: Estratti da error.log (rimuovi dati sensibili!)
6. **Environment**: Produzione vs Development

Template issue:
```markdown
## Descrizione Bug
Breve descrizione del problema

## Ambiente
- Frappe: v15.x.x
- ERPNext: v15.x.x
- italian_invoice: vX.Y.Z
- Provider: Manual/OpenAPI
- Browser: Chrome 120

## Steps to Reproduce
1. Vai in...
2. Clicca su...
3. Vedi errore...

## Comportamento Atteso
Dovrebbe fare X

## Comportamento Reale
Invece fa Y

## Log Errori
```
[paste error logs here]
```

## Screenshots
[se disponibili]
```

#### 📚 Documentazione
- Traduzioni (EN, altre lingue)
- Tutorial video
- Case studies
- API examples più dettagliati

#### 🧪 Testing
- Unit tests per utilities
- Integration tests per workflow completi
- Performance benchmarks
- Test con XML edge cases

### Review Process

1. **Automated checks**: CI verifica syntax, tests, linting
2. **Code review**: Maintainer revisiona codice
3. **Testing**: Feature testata su ambiente staging
4. **Merge**: Se tutto OK, merge in develop
5. **Release**: Periodicamente merged in main con tag versione

### Community

- **Discussioni**: Usa GitHub Discussions per domande
- **Issues**: Usa GitHub Issues per bug e feature requests
- **Email**: info@solede.com per questioni private

### Codice di Condotta

- Rispetto reciproco
- Feedback costruttivo
- Focus su miglioramento del progetto
- Tolleranza zero per comportamenti inappropriati

## 📚 Risorse

- [Specifiche tecniche SDI](https://www.fatturapa.gov.it/it/norme-e-regole/documentazione-fattura-elettronica/)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe Framework](https://frappeframework.com)

## 📄 License

MIT - Vedi file [LICENSE](LICENSE) per dettagli