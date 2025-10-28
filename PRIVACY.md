# Privacy Policy - Italian Invoice (Fatturazione Elettronica Italiana)

**Effective Date:** January 27, 2025
**Last Updated:** January 27, 2025

## 1. Introduction

This Privacy Policy describes how Italian Invoice ("the App", "we", "our") handles data when installed and used within your ERPNext instance. Italian Invoice is an open-source app licensed under AGPLv3, developed and maintained by Solede SA.

**Important:** This app operates entirely within your ERPNext installation. All data processed by the app remains in your own database under your control.

## 2. Data Controller

When you use Italian Invoice, **you are the data controller**. The app does not transmit any data to Solede SA or third parties, except when you explicitly configure external integrations (see Section 5).

## 3. What Data the App Processes

Italian Invoice processes the following types of data within your ERPNext instance:

### 3.1 Invoice Data
- Sales Invoice and Purchase Invoice documents
- Invoice line items, taxes, and totals
- Customer and Supplier information (names, addresses, tax IDs)
- Electronic invoice XML files (Fattura Elettronica format)
- SDI (Sistema di Interscambio) transaction records
- Invoice status and notification history

### 3.2 Company Data
- Company name, tax ID (Partita IVA), and fiscal information
- Company address and contact details
- SDI provider configuration (OpenAPI credentials or manual settings)

### 3.3 Technical Data
- Webhook logs from SDI notifications
- XML validation logs
- Payment reconciliation data
- Error logs for troubleshooting

## 4. How Data is Stored

All data processed by Italian Invoice is stored **exclusively in your ERPNext database**. The app does not:

- ❌ Store data on external servers controlled by Solede SA
- ❌ Transmit data to third parties without your explicit configuration
- ❌ Create backups outside your ERPNext instance
- ❌ Share data with analytics services

**You have complete control** over where your data is stored based on your ERPNext hosting choice (Frappe Cloud, self-hosted, or other hosting provider).

## 5. External Integrations

Italian Invoice supports optional integrations with external services. These integrations are **disabled by default** and only activate when you explicitly configure them.

### 5.1 OpenAPI Provider (docs.openapi.it)

If you configure the OpenAPI provider for SDI integration:

**Data Transmitted to OpenAPI:**
- Electronic invoice XML files (when sending invoices to SDI)
- Company tax ID (Partita IVA)
- Authentication credentials (API token)

**Purpose:** To transmit electronic invoices to the Italian Revenue Agency (Agenzia delle Entrate) via Sistema di Interscambio (SDI).

**Privacy Policy:** https://docs.openapi.it/privacy-policy
**Data Location:** OpenAPI servers (Italy/EU)

**Your Responsibilities:**
- You must accept OpenAPI's terms of service and privacy policy
- You control what invoices are transmitted
- You can revoke integration at any time

### 5.2 Manual Provider

If you select "Manual" provider, no data is transmitted to external services. You manage SDI submissions independently.

### 5.3 Custom Providers

If you develop custom SDI providers, you are responsible for:
- Complying with applicable data protection laws (GDPR, etc.)
- Documenting what data your provider transmits
- Obtaining necessary consents from your users

## 6. Data Access and Permissions

Access to data processed by Italian Invoice is controlled by ERPNext's built-in role-based permission system:

- **Accounts Manager**: Full access to invoice management and SDI integration
- **Sales User / Purchase User**: Limited access based on ERPNext permissions
- **System Manager**: Full system access including configuration

**No external parties** (including Solede SA) have access to your data unless you explicitly grant it (e.g., by sharing database credentials for support purposes).

## 7. Data Retention

Italian Invoice does not enforce any specific data retention policies. Data retention is governed by:

1. **Your ERPNext instance settings**
2. **Italian legal requirements** for invoice retention (typically 10 years)
3. **Your company's data retention policies**

You can delete invoice records and related data at any time through ERPNext's standard deletion features, subject to ERPNext's deletion rules and your legal obligations.

## 8. Data Security

Italian Invoice inherits security features from the ERPNext framework:

- ✅ Role-based access control
- ✅ Encrypted HTTPS connections (when properly configured)
- ✅ Database-level security provided by ERPNext
- ✅ Audit trails for document changes

**Your Responsibilities:**
- Maintain secure ERPNext hosting
- Keep ERPNext and the app updated
- Configure proper firewall and access controls
- Implement backup procedures

## 9. GDPR Compliance

If you operate in the European Union or process data of EU citizens:

**Data Subject Rights:** You must honor data subject requests (access, rectification, erasure, etc.) using ERPNext's built-in features and your own procedures.

**Legal Basis for Processing:**
- Contract performance (B2B invoicing)
- Legal obligation (tax compliance, SDI requirements)
- Legitimate interests (business operations)

**Data Transfers:** If you use external SDI providers like OpenAPI, verify they comply with GDPR for any data transfers outside the EU.

## 10. Webhooks and Notifications

Italian Invoice can receive webhooks from SDI providers (when configured):

**Webhook Data Received:**
- Invoice status updates (accepted, rejected, delivered)
- Notification events from Sistema di Interscambio
- Error messages and delivery receipts

**Webhook Logs:** Webhook payloads are logged in your ERPNext database for troubleshooting. These logs may contain sensitive invoice data.

**Security:** Webhooks should be configured to use HTTPS endpoints with proper authentication. Refer to your SDI provider's security documentation.

## 11. Open Source and Code Transparency

Italian Invoice is open source (AGPLv3 license):

- ✅ Source code available at: https://github.com/Solede-SA/italian_invoice
- ✅ No hidden data collection
- ✅ Community-auditable code
- ✅ Freedom to modify and inspect

You can review the entire codebase to verify how data is processed.

## 12. Third-Party Dependencies

Italian Invoice uses the following third-party libraries:

- **ERPNext** (framework): https://erpnext.com
- **Frappe Framework**: https://frappeframework.com
- **Python standard libraries** (json, xml, requests, etc.)

These dependencies have their own licenses and privacy considerations.

## 13. Children's Privacy

Italian Invoice is a business application not intended for use by individuals under 18 years of age. We do not knowingly collect data from children.

## 14. International Data Transfers

Data location depends on your ERPNext hosting:

- **Frappe Cloud**: Data stored in regions you select (India, US, EU, etc.)
- **Self-hosted**: Data stored on your chosen infrastructure
- **Other Hosting**: Depends on your hosting provider

If you use external SDI providers, they may transfer data internationally. Review their privacy policies.

## 15. Changes to This Privacy Policy

We may update this Privacy Policy from time to time. Changes will be:

- Published in the GitHub repository: https://github.com/Solede-SA/italian_invoice/blob/main/PRIVACY.md
- Noted in the CHANGELOG.md file
- Tagged with version releases

**Your continued use of the app after changes constitutes acceptance of the updated policy.**

## 16. Your Rights and Choices

You have the right to:

- ✅ **Access**: Export your invoice data using ERPNext's data export features
- ✅ **Rectification**: Modify invoice data directly in ERPNext
- ✅ **Erasure**: Delete invoices and related records (subject to legal retention requirements)
- ✅ **Portability**: Export data in JSON, CSV, or XML formats
- ✅ **Restrict Processing**: Disable the app or specific features
- ✅ **Object**: Uninstall the app at any time

## 17. Data Breach Notification

In the unlikely event of a data breach:

- **Your ERPNext Instance:** You are responsible for breach notification under applicable laws
- **App Vulnerabilities:** We will disclose security issues via GitHub Security Advisories
- **Provider Breaches:** If OpenAPI or other providers suffer breaches, they will notify you directly

Report security vulnerabilities to: **info@solede.com**

## 18. Cookies and Tracking

Italian Invoice does not use cookies or tracking technologies. All session management is handled by ERPNext's built-in authentication system.

## 19. Contact Information

**App Developer:** Solede SA
**Email:** info@solede.com
**GitHub Issues:** https://github.com/Solede-SA/italian_invoice/issues
**Website:** https://solede.com

**For Data Protection Inquiries:**
If you have questions about how your data is processed by this app, contact us at info@solede.com.

**For General Support:**
- GitHub Discussions: https://github.com/Solede-SA/italian_invoice/discussions
- Frappe Forum: https://discuss.frappe.io/

## 20. Disclaimer

This Privacy Policy describes how the Italian Invoice app processes data. It does not cover:

- **ERPNext Core:** See https://erpnext.com/privacy
- **Frappe Cloud:** See https://frappecloud.com/privacy
- **Third-party Apps:** Other ERPNext apps have separate privacy policies
- **Your Company's Practices:** You must maintain your own privacy policy for your customers

## 21. Legal Compliance

This app helps you comply with Italian electronic invoicing requirements (Fatturazione Elettronica). However:

- ❌ We are not legal or tax advisors
- ❌ This app does not guarantee legal compliance
- ❌ You remain responsible for meeting all legal obligations

Consult your accountant (commercialista) and legal advisors for compliance guidance.

---

**License:** This Privacy Policy is provided under Creative Commons Attribution 4.0 International (CC BY 4.0)

**Last Updated:** January 27, 2025
**Version:** 1.0.0
