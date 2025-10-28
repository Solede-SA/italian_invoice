# Terms of Service - Italian Invoice (Fatturazione Elettronica Italiana)

**Effective Date:** January 27, 2025
**Last Updated:** January 27, 2025

## 1. Introduction

These Terms of Service ("Terms") govern your use of Italian Invoice ("the App", "Software"), an open-source ERPNext application for Italian electronic invoicing (Fatturazione Elettronica) developed by Solede SA ("we", "us", "our").

**By installing and using this App, you agree to these Terms.**

## 2. License and Open Source

### 2.1 AGPLv3 License

Italian Invoice is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**:

- ✅ You can **use** the software freely for any purpose
- ✅ You can **study** how the software works (source code available)
- ✅ You can **modify** the software to suit your needs
- ✅ You can **distribute** copies of the original or modified software

**AGPL Requirements:**
- 🔒 If you modify and use this software as a **network service** (SaaS, web service), you **must** release your modified source code under AGPLv3
- 🔒 You must preserve copyright notices and license information
- 🔒 You must provide access to the complete source code

**Full License:** [LICENSE](LICENSE) file or https://www.gnu.org/licenses/agpl-3.0.html

### 2.2 No Warranty

This software is provided **"AS IS"** without warranty of any kind. See Section 11 for details.

## 3. Scope of Service

### 3.1 What the App Does

Italian Invoice provides:
- ✅ Generation of Italian electronic invoices (Fatturazione Elettronica XML)
- ✅ Integration with Sistema di Interscambio (SDI) via supported providers
- ✅ Invoice validation according to Italian specifications
- ✅ Management of SDI notifications (acceptance, rejection, delivery)
- ✅ Support for B2B and B2C invoicing
- ✅ XML import/export functionality

### 3.2 What the App Does NOT Do

Italian Invoice does **not**:
- ❌ Provide legal or tax advice
- ❌ Guarantee compliance with all Italian tax laws
- ❌ Replace your commercialista (accountant)
- ❌ Automatically transmit invoices without your action
- ❌ Store data on Solede SA servers
- ❌ Provide customer support beyond community channels

## 4. Your Responsibilities

### 4.1 Compliance

You are responsible for:
- ✅ **Legal Compliance:** Ensuring your use complies with Italian tax laws, GDPR, and other applicable regulations
- ✅ **Data Accuracy:** Verifying that invoice data is correct before submission to SDI
- ✅ **Tax Obligations:** Meeting all deadlines and requirements set by Agenzia delle Entrate
- ✅ **Professional Advice:** Consulting with qualified tax professionals (commercialisti)

### 4.2 Proper Use

You agree to:
- ✅ Use the App only for lawful purposes
- ✅ Not use the App to create fraudulent or false invoices
- ✅ Not attempt to circumvent Italian tax laws using this software
- ✅ Keep the App updated to maintain compatibility and security

### 4.3 ERPNext Instance

You are responsible for:
- ✅ Maintaining a properly configured ERPNext installation
- ✅ Ensuring ERPNext version compatibility (v15+)
- ✅ Database backups and disaster recovery
- ✅ Server security and access controls
- ✅ HTTPS configuration for secure connections

## 5. External Integrations

### 5.1 SDI Providers

Italian Invoice supports integration with external SDI providers (OpenAPI, custom providers):

**Your Responsibilities:**
- You must separately agree to the provider's terms of service
- You are responsible for API credentials security
- You must monitor API usage and costs
- You must comply with the provider's acceptable use policies

**OpenAPI Integration:**
- Provider: docs.openapi.it
- Terms: https://docs.openapi.it/terms
- Privacy: https://docs.openapi.it/privacy
- **We are not responsible** for OpenAPI service availability, costs, or data handling

### 5.2 Custom Providers

If you develop custom SDI provider integrations:
- You are solely responsible for their functionality
- You must ensure they comply with applicable laws
- You assume all liability for any issues they cause
- You should open-source them under compatible licenses (AGPLv3 recommended)

## 6. Fees and Payment

### 6.1 No Fees from Solede SA

Italian Invoice itself is **free and open source**. Solede SA does not charge for:
- ❌ Downloading the software
- ❌ Installing the software
- ❌ Using the software
- ❌ Receiving updates

### 6.2 Third-Party Costs

You may incur costs from:
- **ERPNext Hosting:** Frappe Cloud, self-hosting infrastructure, or other hosting providers
- **SDI Providers:** OpenAPI or other providers may charge for API usage
- **Professional Services:** If you hire consultants for customization or support

**These costs are separate and not controlled by Solede SA.**

## 7. Intellectual Property

### 7.1 Ownership

- **Solede SA** retains copyright to the original Italian Invoice codebase
- **Contributors** retain copyright to their contributions (as noted in git history)
- **Trademarks:** "Italian Invoice" and "Solede" are trademarks of Solede SA

### 7.2 Your Modifications

Under AGPLv3, you may:
- Modify the source code
- Create derivative works
- Distribute your modifications

**But you must:**
- License your modifications under AGPLv3
- Provide source code if you run it as a network service
- Preserve copyright notices

### 7.3 Your Data

You retain all rights to:
- Your invoice data
- Your customer and supplier information
- Your company data
- Any content you create using the App

## 8. Privacy and Data Protection

Data privacy is governed by our separate [Privacy Policy](PRIVACY.md).

**Key Points:**
- All data stays in your ERPNext database
- You are the data controller
- No data is sent to Solede SA
- External integrations (if configured) have their own privacy policies

## 9. Support and Maintenance

### 9.1 Community Support

Support is provided through **community channels only**:
- GitHub Issues: https://github.com/Solede-SA/italian_invoice/issues
- GitHub Discussions: https://github.com/Solede-SA/italian_invoice/discussions
- Frappe Forum: https://discuss.frappe.io/

**We do not guarantee:**
- ❌ Response times
- ❌ Resolution of issues
- ❌ Availability of support personnel
- ❌ Support in languages other than English/Italian

### 9.2 Updates and Maintenance

We provide updates on a **best-effort basis**:
- ✅ Security patches when critical vulnerabilities are discovered
- ✅ Compatibility updates for new ERPNext versions (when feasible)
- ✅ Bug fixes for reported issues (at our discretion)

**We do not guarantee:**
- ❌ Regular update schedules
- ❌ Immediate bug fixes
- ❌ Feature requests will be implemented
- ❌ Backward compatibility in all cases

### 9.3 Professional Services

For guaranteed support, custom development, or consulting:
- Contact us at: info@solede.com
- Professional services are subject to separate commercial agreements
- Fees apply for professional services

## 10. Modifications to the App

### 10.1 Updates

We reserve the right to:
- Modify the App at any time
- Add or remove features
- Change APIs and interfaces
- Discontinue the project

**Updates do not automatically install.** You must manually update your installation.

### 10.2 Breaking Changes

We will make reasonable efforts to:
- Document breaking changes in CHANGELOG.md
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Provide migration guides when possible

**But we do not guarantee** backward compatibility.

## 11. Warranties and Disclaimers

### 11.1 NO WARRANTY

**THE APP IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF:**
- ❌ MERCHANTABILITY
- ❌ FITNESS FOR A PARTICULAR PURPOSE
- ❌ NON-INFRINGEMENT
- ❌ ACCURACY OR COMPLETENESS
- ❌ ERROR-FREE OPERATION

### 11.2 Specific Disclaimers

We specifically disclaim any warranty that:
- The App will meet your requirements
- The App will work with all ERPNext versions
- Generated invoices will be accepted by SDI
- The App complies with all Italian tax regulations
- The App is free from bugs or errors
- Operation will be uninterrupted or secure

### 11.3 Use at Your Own Risk

**YOU ASSUME ALL RISK** for:
- Accuracy of generated invoices
- Compliance with tax laws
- Data loss or corruption
- Business disruptions
- Financial losses

## 12. Limitation of Liability

### 12.1 Maximum Liability

**TO THE MAXIMUM EXTENT PERMITTED BY LAW, SOLEDE SA AND CONTRIBUTORS SHALL NOT BE LIABLE FOR:**

- ❌ Any indirect, incidental, special, consequential, or punitive damages
- ❌ Loss of profits, revenue, data, or business opportunities
- ❌ Incorrect tax filings or penalties from tax authorities
- ❌ Rejected invoices or SDI transmission failures
- ❌ Data breaches or security incidents
- ❌ Compatibility issues with ERPNext or third-party services

**EVEN IF WE HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.**

### 12.2 No Liability for Third-Party Services

We are not liable for:
- Issues with ERPNext core functionality
- SDI provider (OpenAPI, etc.) failures or errors
- Italian government systems (SDI, Agenzia delle Entrate)
- Hosting provider outages or data loss
- Third-party app conflicts

### 12.3 Maximum Monetary Liability

**IF LIABILITY CANNOT BE EXCLUDED:** Our total liability shall not exceed €100 (one hundred euros), regardless of the number of claims.

## 13. Indemnification

You agree to **indemnify and hold harmless** Solede SA, its contributors, and affiliates from any claims, damages, losses, or expenses (including legal fees) arising from:

- Your use or misuse of the App
- Your violation of these Terms
- Your violation of applicable laws (tax, GDPR, etc.)
- Incorrect invoices you generate or submit
- Your modifications to the App
- Third-party claims related to your use

## 14. Termination

### 14.1 By You

You may stop using the App at any time by:
- Uninstalling the App from ERPNext
- Deleting the App files
- No notice to us is required

### 14.2 By Us

We may discontinue the App at any time by:
- Archiving the GitHub repository
- Ceasing development and support
- Publishing a discontinuation notice

**We are not obligated to provide:**
- Advance notice of discontinuation
- Data migration assistance
- Alternative solutions

### 14.3 Effect of Termination

Upon termination:
- Your right to use the App ceases (unless you maintain your own fork)
- These Terms remain in effect for past usage
- Sections 11 (Warranties), 12 (Liability), 13 (Indemnification) survive

## 15. Changes to These Terms

### 15.1 Right to Modify

We reserve the right to modify these Terms at any time.

Changes will be:
- Published in the GitHub repository: https://github.com/Solede-SA/italian_invoice/blob/main/TERMS.md
- Noted in CHANGELOG.md
- Effective immediately upon publication

### 15.2 Your Acceptance

**Continued use of the App after changes constitutes acceptance of the modified Terms.**

If you do not agree with changes:
- You must stop using the App
- You may fork the codebase before changes (subject to AGPLv3)

## 16. Governing Law and Jurisdiction

### 16.1 Governing Law

These Terms are governed by the laws of **Switzerland**, without regard to conflict of law principles.

### 16.2 Jurisdiction

Any disputes shall be resolved exclusively in the courts of **Ticino, Switzerland**.

### 16.3 European Users

If you are in the European Union, you may also have rights under EU consumer protection laws.

## 17. Dispute Resolution

### 17.1 Informal Resolution

Before filing any legal action, you agree to:
1. Contact us at info@solede.com
2. Describe the issue in detail
3. Allow 30 days for good-faith resolution attempts

### 17.2 Arbitration

If informal resolution fails, disputes may be submitted to arbitration under Swiss arbitration rules.

### 17.3 Class Action Waiver

You agree to resolve disputes individually, not as part of any class or representative action.

## 18. Compliance with Italian Laws

### 18.1 Fatturazione Elettronica Requirements

While this App is designed to help with Italian electronic invoicing, **you remain responsible for:**
- Understanding current Italian tax regulations
- Ensuring invoices comply with technical specifications
- Meeting all legal deadlines
- Responding to SDI errors or rejections
- Maintaining proper records (typically 10 years)

### 18.2 Changes in Regulations

Italian regulations may change. **You are responsible for:**
- Monitoring regulatory changes
- Updating the App or your processes accordingly
- Consulting with tax professionals

**We will make reasonable efforts** to update the App for regulatory changes, but provide no guarantees.

## 19. Export Compliance

This software may be subject to export control laws. You agree to comply with all applicable export and import laws and regulations.

## 20. Entire Agreement

These Terms, together with:
- The Privacy Policy (PRIVACY.md)
- The AGPLv3 License (LICENSE)
- The Contributing Guidelines (CONTRIBUTING.md)

constitute the **entire agreement** between you and Solede SA regarding the App.

## 21. Severability

If any provision of these Terms is found to be unenforceable or invalid, that provision shall be limited or eliminated to the minimum extent necessary, and the remaining provisions shall remain in full force.

## 22. No Waiver

Our failure to enforce any provision of these Terms shall not constitute a waiver of that provision or any other provision.

## 23. Assignment

You may not assign or transfer these Terms without our written consent.

We may assign these Terms to any affiliate or successor entity.

## 24. Force Majeure

We are not liable for any failure or delay in performance due to circumstances beyond our reasonable control, including:
- Natural disasters
- War, terrorism, or civil unrest
- Government actions or regulations
- Internet or hosting provider failures
- Changes to Italian tax systems

## 25. Contact Information

**Solede SA**
- Email: info@solede.com
- GitHub: https://github.com/Solede-SA
- Issues: https://github.com/Solede-SA/italian_invoice/issues

**For Legal Inquiries:**
Contact info@solede.com with "Legal - Italian Invoice" in the subject line.

**For Security Issues:**
Report vulnerabilities to info@solede.com with "Security" in the subject line.

## 26. Acknowledgments

By using Italian Invoice, you acknowledge that:

1. ✅ You have read and understood these Terms
2. ✅ You accept these Terms in full
3. ✅ You understand the App is provided "as is" without warranty
4. ✅ You are responsible for compliance with Italian laws
5. ✅ You will not hold Solede SA liable for issues arising from use
6. ✅ You have the authority to agree to these Terms on behalf of your organization (if applicable)

---

**License:** These Terms of Service are provided under Creative Commons Attribution 4.0 International (CC BY 4.0)

**Last Updated:** January 27, 2025
**Version:** 1.0.0

**Questions?** Contact us at info@solede.com or open a GitHub Discussion.
