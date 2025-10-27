# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-27

### Added

#### Fatturazione Attiva (Sales Invoices)
- Generazione XML FatturaPA v1.2.1 conforme allo standard SDI
- Validazione XML multi-livello con messaggi user-friendly
- Invio fatture tramite provider SDI configurabili (architettura pluggabile)
- Provider Manual built-in per test e sviluppo senza dipendenze esterne
- Tracking completo stato transazioni SDI con timeline
- Gestione automatica Credit Notes, Debit Notes, autofatture
- Supporto Split Payment con calcoli automatici
- Gestione Nature IVA (N1-N7) con esenzioni automatiche
- Sistema Lettera d'Intento con esenzione IVA configurabile

#### Fatturazione Passiva (Purchase Invoices)
- Import automatico XML fornitori via webhook o upload manuale
- Parsing intelligente dati fornitore (P.IVA, Codice Fiscale, anagrafica)
- Estrazione automatica righe fattura con tasse e descrizioni
- Auto-link con Purchase Orders e Purchase Receipts aperti
- Creazione Purchase Invoice con un click da PO/PR esistenti
- Matching fornitore basato su P.IVA con fallback su nome/codice fiscale
- Sincronizzazione bidirezionale stato fattura SDI ↔ Purchase Invoice
- Gestione completa ciclo passivo: ricevuta, accettata, rifiutata

#### Gestione Pagamenti
- Allocazione automatica intelligente per pagamenti parziali
- Sistema dual-stage: allocated_amount + difference_amount
- Arrotondamento automatico differenze entro soglia configurabile (default €0.50)
- Gestione trasparente unallocated_amount e write-off
- Audit trail completo con Payment Rounding Log
- Riconciliazione automatica con Bank Reconciliation
- Supporto pagamenti multipli parziali

#### Registri IVA e Reporting
- Registro IVA Vendite conforme normativa italiana
- Registro IVA Acquisti con totali e riepiloghi
- Export Excel con formattazione professionale
- Export CSV per import in software contabili
- Export PDF per archiviazione
- Filtri avanzati per periodo, company, modalità pagamento
- Calcoli automatici imponibile, IVA, totali per aliquota

#### Delivery Notes Management
- Gestione gap tra DDT e fattura (billing_gap_days)
- Validazione automatica ritardi fatturazione
- Warning per DDT non fatturati oltre soglia
- Integrazione seamless con Sales Invoice creation

#### Tipologie Documento e Configurazioni
- 8 Custom DocTypes per workflow completo
- 80+ Custom Fields integrati con ERPNext
- Configurazioni Nature IVA (N1-N7)
- Tipologie documento e-Invoice
- Motivi esenzione IVA
- Stati fattura elettronica SDI

### Security
- Zero dipendenze esterne (provider Manual built-in)
- Validazione input su tutti i campi
- Sanitizzazione XML per prevenire injection
- Gestione sicura file upload
- Audit trail completo per tutte le operazioni

### Documentation
- README completo (1411 righe) con:
  - Guida installazione passo-passo
  - Documentazione completa features
  - Esempi configurazione
  - Troubleshooting guide
  - Architettura sistema provider
  - API reference
- Documentazione inline nel codice
- Commenti Python con type hints
- Diagrammi workflow

### Developer Experience
- Architettura modulare e manutenibile
- ~4,700 linee di codice Python production-ready
- Sistema provider pluggabile per estensioni
- Principi DRY e KISS applicati rigorosamente
- Nessun fallback silenzioso - errori sempre espliciti
- Type annotations complete
- Test files structure (pronti per implementazione test)

### Compliance
- Conforme a specifiche tecniche FatturaPA v1.2.1
- Standard SDI (Sistema di Interscambio)
- Normativa italiana IVA e fatturazione
- Gestione corretta Nature IVA (N1-N7)
- Split Payment secondo normativa
- Registri IVA conformi obblighi fiscali

[1.0.0]: https://github.com/Solede-SA/italian_invoice/releases/tag/v1.0.0
