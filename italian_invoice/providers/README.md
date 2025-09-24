# Provider SDI per Italian Invoice

## Panoramica

Il sistema provider permette di integrare diversi servizi SDI (Sistema di Interscambio) con Italian Invoice.
Ogni provider implementa l'interfaccia base `SDIProvider` definita in `base.py`.

## Implementare un Nuovo Provider

### 1. Creare una nuova classe

```python
from italian_invoice.providers.base import SDIProvider
import frappe

class MyCustomProvider(SDIProvider):
    """Provider custom per SDI"""

    def __init__(self):
        self.base_url = "https://api.myprovider.com"

    def send_invoice(self, xml_content: str, doc, company) -> dict:
        # Implementa invio fattura
        pass

    def download_invoice(self, uuid: str, format: str, company) -> bytes:
        # Implementa download
        pass

    # ... altri metodi richiesti
```

### 2. Registrare il Provider

Aggiungi il tuo provider nel factory method di `italian_invoice/utilities/fatture.py`:

```python
if provider_type == "MyCustom":
    from myapp.providers.my_custom_provider import MyCustomProvider
    provider = MyCustomProvider()
```

### 3. Configurazione Company

Imposta il campo `custom_sdi_provider` della Company al nome del tuo provider.

## Provider Disponibili

### OpenAPI Provider
- Provider ufficiale per servizi OpenAPI
- Richiede token di autenticazione
- Supporta webhook e notifiche real-time
- Configurazione business register

### Manual Provider
- Provider per sviluppo e test
- Salva XML localmente
- Non richiede servizi esterni
- Utile per debug

## Gestione Webhook

I provider che supportano webhook devono:

1. Implementare `configure_webhooks()` per setup iniziale
2. Implementare `handle_webhook()` per processare notifiche
3. Gestire autenticazione specifica del provider
4. Convertire notifiche nel formato standard

### Esempio Webhook

```python
def handle_webhook(self, endpoint: str, data: dict) -> dict:
    if endpoint == "invoice_received":
        # Processa fattura ricevuta
        return self.process_received_invoice(data)
    elif endpoint == "status_update":
        # Processa aggiornamento stato
        return self.process_status_update(data)
    else:
        frappe.throw(f"Endpoint webhook non riconosciuto: {endpoint}")
```

## Testing Provider

```python
# Test invio fattura
provider = get_sdi_provider("My Company")
result = provider.send_invoice(xml_content, doc, company)
print(f"Fattura inviata con UUID: {result['uuid']}")

# Test download
content = provider.download_invoice(uuid, "pdf", company)
with open("fattura.pdf", "wb") as f:
    f.write(content)
```

## Best Practices

1. **Gestione Errori**: Cattura e logga errori specifici del provider
2. **Retry Logic**: Implementa retry per operazioni di rete
3. **Caching**: Cache configurazioni per evitare query ripetute
4. **Logging**: Log dettagliato per debug
5. **Validazione**: Valida input prima di inviare al provider

## Migrazione da Versione Precedente

Se stai migrando da una versione precedente che usa solo OpenAPI:

1. Il sistema continuerà a funzionare senza modifiche
2. OpenAPI è il provider di default
3. Puoi switchare provider cambiando configurazione Company
4. Nessuna modifica richiesta al codice esistente