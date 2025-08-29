# Piano di Refactoring Italian Invoice - Progetto Opensource

## Obiettivo
Rendere l'app `italian_invoice` un progetto opensource mantenendo la piena retrocompatibilità con le installazioni esistenti che utilizzano l'integrazione OpenAPI.

## Analisi del Sistema Attuale

### Dipendenze Identificate
1. **Import diretto**: `openapi/api/sdi/fatture.py` importa `italian_invoice.utilities.fatture`
2. **Custom fields condivisi**: Alcuni campi sono marcati con module "Openapi" 
3. **Servizi API**: Invio fatture tramite OpenAPI Services configurato in Company
4. **Token e configurazioni**: `custom_open_api_token` e URL servizi specifici
5. **Sistema Webhook**: Gestione notifiche SDI tramite webhook configurati in Company:
   - `custom_webhook_url`: URL base per i webhook
   - `custom_auth_header`: Header di autenticazione
   - `custom_elenco_webhook`: Lista di webhook (child table OpenApi WebHook)
   - Endpoints callback: `supplier_invoice`, `customer_notification`, `legal_storage_receipt`, etc.

### File Principali Coinvolti
- `italian_invoice/utilities/fatture.py` - Generazione XML e utilities
- `openapi/api/sdi/fatture.py` - Integrazione con servizio SDI OpenAPI
- `openapi/api/sdi/callback.py` - Gestione callback/webhook da SDI
- `openapi/api/sdi/configurazione.py` - Configurazione business register e webhook
- `openapi/tools/common_data.py` - Helper per ottenere URL servizi
- `openapi/openapi/doctype/openapi_webhook/` - DocType per configurazione webhook
- Custom fields in Company per token e configurazioni

## Architettura Proposta

### 1. Sistema Provider SDI Pluggabile

```
italian_invoice/
├── providers/
│   ├── __init__.py
│   ├── base.py                    # Classe astratta SDIProvider
│   ├── openapi_provider.py        # Provider OpenAPI (estratto dal codice esistente)
│   ├── manual_provider.py         # Provider manuale per test/sviluppo
│   └── README.md                  # Guida implementazione nuovi provider
```

### 2. Interfaccia Base SDIProvider

```python
# providers/base.py
class SDIProvider:
    """Interfaccia base per provider SDI"""
    
    def send_invoice(self, xml_content: str, doc, company) -> dict:
        """Invia fattura al SDI"""
        raise NotImplementedError
    
    def download_invoice(self, uuid: str, format: str, company) -> bytes:
        """Scarica fattura dal SDI"""
        raise NotImplementedError
    
    def get_invoice_status(self, uuid: str, company) -> dict:
        """Ottiene stato fattura"""
        raise NotImplementedError
    
    def handle_notification(self, notification_data: dict) -> dict:
        """Gestisce notifiche SDI"""
        raise NotImplementedError
    
    def configure_webhooks(self, company) -> dict:
        """Configura webhook per notifiche SDI"""
        raise NotImplementedError
    
    def handle_webhook(self, endpoint: str, data: dict) -> dict:
        """Gestisce chiamate webhook in arrivo"""
        raise NotImplementedError
    
    def setup_business_register(self, company, config: dict) -> dict:
        """Configura il business register presso il provider"""
        raise NotImplementedError
```

## Implementazione Step-by-Step

### Step 1: Creare Struttura Provider
1. Creare directory `italian_invoice/providers/`
2. Implementare `base.py` con classe astratta SDIProvider (include metodi webhook)
3. Creare `README.md` con documentazione per sviluppatori

### Step 2: Estrarre Provider OpenAPI
1. Creare `italian_invoice/providers/openapi_provider.py`
2. Spostare logica da `openapi/api/sdi/`:
   - `fatture.py`: invio e download fatture
   - `callback.py`: gestione webhook/callback
   - `configurazione.py`: setup business register e webhook
3. La classe deve:
   - Ereditare da SDIProvider
   - Implementare tutti i metodi base
   - Gestire token e configurazioni OpenAPI
   - Mantenere compatibilità con webhook esistenti

### Step 3: Factory Provider con Gestione Webhook
Creare in `italian_invoice/utilities/fatture.py`:

```python
_provider_cache = {}

def get_sdi_provider(company_name):
    """
    Ottiene il provider SDI configurato per la company
    Con cache per evitare istanze multiple (DRY)
    """
    if company_name in _provider_cache:
        return _provider_cache[company_name]
    
    company = frappe.get_doc("Company", company_name)
    provider_type = company.get("custom_sdi_provider", "OpenAPI")
    
    if provider_type == "OpenAPI":
        from italian_invoice.providers.openapi_provider import OpenAPIProvider
        provider = OpenAPIProvider()
    elif provider_type == "Manual":
        from italian_invoice.providers.manual_provider import ManualProvider
        provider = ManualProvider()
    else:
        # Provider custom
        provider_class = frappe.get_attr(provider_type)
        provider = provider_class()
    
    _provider_cache[company_name] = provider
    return provider

def handle_sdi_webhook(endpoint, data):
    """
    Router centrale per webhook SDI
    Identifica la company dal contenuto e delega al provider
    """
    # Logica per identificare company da partita IVA o altri dati
    company = identify_company_from_webhook_data(data)
    provider = get_sdi_provider(company.name)
    return provider.handle_webhook(endpoint, data)
```

### Step 4: Refactoring openapi/api/sdi/
Mantenere le funzioni esistenti come wrapper (retrocompatibilità):

#### fatture.py
```python
@frappe.whitelist()
def invia_fattura(docname, doctype):
    """Wrapper per retrocompatibilità - usa il provider configurato"""
    doc = frappe.get_doc(doctype, docname)
    provider = italian_invoice.utilities.fatture.get_sdi_provider(doc.company)
    xml = italian_invoice.utilities.fatture.get_xml(docname, doctype)
    return provider.send_invoice(xml, doc, doc.company)
```

#### callback.py
```python
@frappe.whitelist(allow_guest=True)
def supplier_invoice():
    """Wrapper per retrocompatibilità - delega al provider"""
    return italian_invoice.utilities.fatture.handle_sdi_webhook(
        "supplier_invoice", 
        frappe.request.data
    )

@frappe.whitelist(allow_guest=False)
def customer_notification():
    """Wrapper per retrocompatibilità"""
    return italian_invoice.utilities.fatture.handle_sdi_webhook(
        "customer_notification",
        frappe.request.data
    )
```

#### configurazione.py
```python
@frappe.whitelist()
def send_configuration(data):
    """Wrapper per retrocompatibilità"""
    data = prepare_data(data)
    company = frappe.get_doc("Company", data["name"])
    provider = italian_invoice.utilities.fatture.get_sdi_provider(company.name)
    return provider.configure_webhooks(company)
```

### Step 5: Custom Fields in Company
Aggiungere tramite fixtures:

1. **custom_sdi_provider** (Select)
   - Label: "Provider SDI"
   - Options: "OpenAPI\nManual\nCustom"
   - Default: "OpenAPI"
   - Description: "Seleziona il provider per l'invio fatture elettroniche"

2. **custom_sdi_provider_config** (JSON)
   - Label: "Configurazione Provider SDI"
   - Description: "Configurazione specifica del provider (JSON)"
   - Hidden unless: custom_sdi_provider=="Custom"

3. **Mantenere campi esistenti** per OpenAPI provider:
   - `custom_webhook_url`
   - `custom_auth_header`
   - `custom_elenco_webhook`
   - `custom_open_api_token`
   - Altri campi OpenAPI specifici

### Step 6: Provider Manuale per Test
Creare `manual_provider.py` per sviluppo/test:
- Salva XML in locale
- Genera UUID fittizio
- Simula webhook con notifiche locali
- Log dettagliato per debug
- Utile per test senza servizio esterno

### Step 7: Documentazione
Creare documentazione completa:
1. `README.md` principale con setup e configurazione
2. `providers/README.md` con:
   - Guida implementazione provider
   - Gestione webhook e callback
   - Esempi di configurazione business register
3. Esempi di configurazione per diversi provider
4. Migration guide per passare da versione attuale
5. Documentazione API webhook per ogni provider

## Testing e Validazione

### Test di Retrocompatibilità
1. Verificare che installazioni esistenti funzionino senza modifiche
2. Test invio fattura con configurazione attuale
3. Test download e notifiche
4. **Test webhook esistenti**:
   - supplier_invoice (allow_guest=True)
   - customer_notification
   - legal_storage_receipt
   - Verificare autenticazione e routing
5. Test configurazione business register
6. Verificare che custom fields esistenti funzionino

### Test Nuova Architettura
1. Test switching tra provider
2. Validare XML generato identico
3. Test provider manuale con webhook simulati
4. Test configurazioni JSON custom
5. Test nuovo routing webhook centralizzato
6. Test identificazione company da dati webhook

## Gestione Webhook - Dettaglio

### Webhook Attuali OpenAPI
1. **supplier_invoice**: Riceve fatture fornitori (guest allowed)
2. **customer_notification**: Notifiche su fatture clienti
3. **legal_storage_receipt**: Ricevute conservazione sostitutiva
4. **invoice_status_quarantena**: Stato quarantena
5. **invoice_status_invoice_error**: Errori fattura

### Strategia Webhook per Provider
Ogni provider deve:
1. Definire propri endpoint webhook necessari
2. Gestire autenticazione specifica
3. Processare notifiche nel formato del provider
4. Convertire in formato standard per Italian Invoice
5. Salvare notifiche in "Transazione SDI" e "Notifiche SDI"

### Routing Webhook
```
Richiesta webhook → openapi/api/sdi/callback.py (wrapper)
                 ↓
    italian_invoice/utilities/fatture.handle_sdi_webhook()
                 ↓
         Identifica Company da dati
                 ↓
         Get Provider per Company
                 ↓
     provider.handle_webhook(endpoint, data)
```

## Principi Seguiti

### DRY (Don't Repeat Yourself)
- Factory pattern con cache per provider
- Classe base con logica comune
- Riuso codice esistente tramite wrapper
- Routing centralizzato webhook

### KISS (Keep It Simple, Stupid)
- Solo 7 metodi nell'interfaccia base
- Configurazione via UI standard Frappe
- Retrocompatibilità automatica
- Nessuna breaking change
- Webhook routing trasparente

## File da Modificare

1. **Nuovi file da creare:**
   - `italian_invoice/providers/__init__.py`
   - `italian_invoice/providers/base.py`
   - `italian_invoice/providers/openapi_provider.py`
   - `italian_invoice/providers/manual_provider.py`
   - `italian_invoice/providers/README.md`

2. **File da modificare:**
   - `italian_invoice/utilities/fatture.py` - Aggiungere get_sdi_provider() e handle_sdi_webhook()
   - `openapi/api/sdi/fatture.py` - Convertire in wrapper
   - `openapi/api/sdi/callback.py` - Convertire in wrapper per webhook
   - `openapi/api/sdi/configurazione.py` - Convertire in wrapper
   - `italian_invoice/fixtures/custom_field.json` - Aggiungere nuovi campi

3. **File da NON modificare (retrocompatibilità):**
   - Hooks esistenti
   - API pubbliche esistenti (mantenerle come wrapper)
   - Custom fields esistenti OpenAPI
   - Template XML
   - DocType OpenApi WebHook

## Note per l'Implementazione

1. **Ordine critico**: Seguire l'ordine degli step per evitare breaking changes
2. **Test continui**: Testare dopo ogni step che il sistema funzioni
3. **Backup**: Fare backup prima di iniziare modifiche
4. **Documentazione inline**: Commentare bene il codice per futuri contributori
5. **Versionamento**: Considerare versioning semantico per release
6. **Webhook security**: Mantenere validazione auth per webhook non-guest
7. **Logging**: Mantenere logging dettagliato per debug webhook

## Benefici Finali

1. **Per utenti esistenti**: Nessun cambiamento, tutto funziona come prima (inclusi webhook)
2. **Per nuovi utenti**: Possibilità di scegliere provider SDI
3. **Per sviluppatori**: Facile aggiungere nuovi provider con propri webhook
4. **Per community**: Codice opensource riutilizzabile
5. **Flessibilità**: Ogni provider può gestire webhook nel proprio formato

## Prossimi Passi

1. Review di questo piano aggiornato
2. Setup ambiente di test con webhook
3. Implementazione step-by-step
4. Testing completo inclusi webhook
5. Documentazione finale
6. Release su GitHub

---

*Documento creato il: 2025-08-28*
*Aggiornato con gestione webhook*
*Da utilizzare per implementazione futura*