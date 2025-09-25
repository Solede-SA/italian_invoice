# Italian Invoice

App Frappe/ERPNext per la gestione delle fatture elettroniche italiane secondo lo standard SDI (Sistema di Interscambio).

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
1. **Ricezione XML** → Via webhook o upload manuale
2. **Parsing automatico** → Estrazione dati da XML
3. **Creazione/Match Supplier** → Basato su P.IVA
4. **Creazione Purchase Invoice** → Con mapping articoli
5. **Contabilizzazione** → Standard ERPNext

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
3. Il sistema estrae automaticamente i dati
4. Clicca **"Importa in Purchase Invoice"**
5. Mappa gli articoli se necessario
6. Conferma la creazione

#### Via API (Automatico con OpenAPI)
```python
# Le fatture arrivano automaticamente via webhook
# e vengono processate in background
```

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

### DocTypes Principali

#### Transazione SDI
Traccia lo stato di ogni fattura inviata al SDI:
- **UUID**: Identificativo univoco transazione
- **Stato Invio**: Stato corrente (Inviata, Consegnata, Scartata, etc.)
- **Fattura**: Link al documento ERPNext originale
- **Notifiche**: Tabella child con storico notifiche SDI
- **Ultima Notifica**: JSON con dettagli ultima notifica

#### Fattura Fornitori SDI
Buffer per fatture passive ricevute:
- **Dati Fattura**: JSON completo del XML parseato
- **P.IVA/Denominazione**: Dati fornitore per matching
- **Stato**: Da importare/Importata
- **UUID**: Identificativo SDI della fattura

#### Stato Fattura Elettronica
Master data degli stati SDI (es. "Inviata", "Consegnata", "MC - Mancata Consegna")

#### Tipologia di documento e-Invoice
Master data dei tipi documento (TD01, TD04, etc.) con descrizioni e validazioni

#### Motivo esenzione IVA
Codifiche per esenzioni IVA con riferimenti normativi (N1-N7)

## 🔍 Campi Custom Aggiunti

### Company
- `custom_codice_sistema_interscambio`: Codice destinatario
- `custom_sdi_provider`: Selezione provider
- `custom_sdi_provider_config`: Config JSON per provider custom

### Sales/Purchase Invoice
- `custom_tipo_di_documento`: Tipo documento fattura
- `custom_transazione_sdi`: Link alla transazione
- `custom_uuid`: UUID fattura inviata

### Customer
- `custom_tipo_fattura_elettronica`: Tipo default
- `custom_vat_collectability`: Esigibilità IVA
- Campi per lettera d'intento

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

### Struttura App
```
italian_invoice/
├── providers/              # Sistema provider pluggabile
│   ├── base.py            # Classe astratta SDIProvider
│   ├── manual_provider.py # Provider test/sviluppo
│   └── openapi_provider.py # Integrazione OpenAPI.it
├── validation/             # Sistema validazione XML
│   ├── xml_validator.py   # Validatore multi-livello
│   └── error_formatter.py # Formattazione errori
├── utilities/
│   ├── fatture.py         # Generazione XML attive
│   └── fatture_passive.py # Import e processing passive
├── italian_invoice/doctype/  # DocTypes personalizzati
└── fixtures/              # Custom fields e configurazioni
```

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
                                                    ↓
                                            Supplier Creation/Match
                                                    ↓
                                              Item Mapping
```

## 🔄 Migrazione da Versioni Precedenti

Se stai aggiornando da una versione che utilizzava openapi per i DocType:

1. **Backup del database** (importante!)
2. **Aggiorna il codice**:
   ```bash
   bench get-app italian_invoice --branch main
   bench --site [nome-sito] migrate
   ```
3. **Verifica moduli**: I DocType verranno automaticamente migrati al modulo "Italian Invoice"
4. **Test**: Verifica che le fatture esistenti siano ancora accessibili

## 🤝 Contribuire

Contribuzioni benvenute! Per favore:

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push del branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

### Linee Guida
- Mantieni compatibilità con ERPNext v15
- Aggiungi test per nuove funzionalità
- Documenta le API pubbliche
- Segui PEP 8 per il codice Python

## 📚 Risorse

- [Specifiche tecniche SDI](https://www.fatturapa.gov.it/it/norme-e-regole/documentazione-fattura-elettronica/)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe Framework](https://frappeframework.com)

## 📄 License

MIT - Vedi file [LICENSE](LICENSE) per dettagli