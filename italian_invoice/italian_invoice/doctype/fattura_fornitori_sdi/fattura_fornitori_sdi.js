function format_currency(value) {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
    }).format(value);
}

frappe.ui.form.on("Fattura Fornitori SDI", {
    refresh(frm) {
        if (!frappe.boot.developer_mode) {
            frm.disable_save();
        } else {
            frm.enable_save();
        }

        frm.add_custom_button(__("Scarica PDF"), () => {
            window.location.href = `/api/method/openapi.api.sdi.fatture.download?doctype=Fattura Fornitori SDI&docname=${frm.doc.name}&type=pdf`;
        });

        frm.get_field('documenti_aperti').$wrapper.html('');

        if (frm.doc.stato === "Da importare") {
            frm.add_custom_button(__("Importa Fattura"), () => {
                frappe.call({
                    method: 'italian_invoice.utilities.fatture.get_supplier_vat_from_json',
                    args: { invoice_data: frm.doc.dati_fattura },
                    callback: (r) => {
                        const supplier_vat = r.message;
                        frappe.call({
                            method: "openapi.api.eInvoice.purchase_invoice.get_or_create_supplier",
                            args: {
                                supplier_vat_id: supplier_vat,
                                fattura_fornitori_sdi: frm.doc.name
                            },
                            callback: (r) => {
                                if (!r.message.success) {
                                    frappe.throw(r.message.error);
                                    return;
                                }
                                const supplier_data = r.message.supplier_data;
                                if (r.message.is_new) {
                                    frappe.show_alert({
                                        message: __(`Nuovo fornitore ${supplier_data.supplier_name} creato`),
                                        indicator: 'green'
                                    });
                                }
                                show_items_dialog(frm, supplier_data);
                            }
                        });
                    }
                });
            });

            if (frm.doc.partita_iva_fornitore) {
                check_open_purchase_documents(frm);
            }
        }
    }
});


function _get_codice_articolo(line) {
    const ca = line.codice_articolo;
    if (!ca) return null;
    if (Array.isArray(ca) && ca.length > 0) return ca[0].codice_valore || null;
    if (typeof ca === 'object') return ca.codice_valore || null;
    return null;
}


function show_items_dialog(frm, supplier_data) {
    frappe.call({
        method: 'italian_invoice.utilities.fatture.get_invoice_lines_from_json',
        args: { invoice_data: frm.doc.dati_fattura },
        callback: (r) => {
            const allLines = r.message;
            const invoice_lines = allLines.filter(line =>
                line.prezzo_totale != null || line.quantita != null
            );

            if (allLines.length !== invoice_lines.length) {
                const skippedCount = allLines.length - invoice_lines.length;
                frappe.show_alert({
                    message: __(`${skippedCount} righe con quantità zero ignorate`),
                    indicator: 'blue'
                }, 5);
            }

            // --- Build dialog fields: split left/right layout ---
            const dialog_fields = [
                {
                    fieldtype: 'HTML',
                    fieldname: 'supplier_info',
                    options: `<div style="margin-bottom: 10px;">
                        <strong>Fornitore:</strong> ${supplier_data.supplier_name}
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>P.IVA:</strong> ${supplier_data.tax_id}
                    </div>`
                }
            ];

            invoice_lines.forEach((line, idx) => {
                const isZeroValue = parseFloat(line.prezzo_totale || 0) === 0;
                const importo = format_currency(line.prezzo_totale);
                const iva = line.aliquota_iva ? `${line.aliquota_iva}%` : '0%';
                const natura = line.natura ? ` (${line.natura})` : '';
                const codice = _get_codice_articolo(line);
                const codiceHtml = codice
                    ? `<div style="font-size: 12px; color: #6c757d;">Cod. Art.: <code>${codice}</code></div>`
                    : '';

                const leftHtml = `
                    <div style="padding: 12px; background: #f8f9fa; border-radius: 6px; border-left: 3px solid ${isZeroValue ? '#ffc107' : '#5e64ff'}; min-height: 90px;">
                        <div style="font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #333;">
                            ${idx + 1}. ${line.descrizione}
                        </div>
                        <div style="font-size: 13px; color: #495057;">
                            Importo: <strong style="color: ${isZeroValue ? '#ffc107' : '#28a745'};">${importo}</strong>
                            &nbsp;&nbsp; IVA: <strong>${iva}${natura}</strong>
                        </div>
                        ${codiceHtml}
                        ${isZeroValue ? '<div style="font-size: 11px; color: #ffc107; margin-top: 4px;">(Opzionale)</div>' : ''}
                    </div>
                `;

                // Section Break per ogni riga
                dialog_fields.push({ fieldtype: 'Section Break' });
                // Colonna sinistra: dati fattura (readonly)
                dialog_fields.push({
                    fieldtype: 'HTML',
                    fieldname: `desc_${idx}`,
                    options: leftHtml
                });
                // Column Break
                dialog_fields.push({ fieldtype: 'Column Break' });
                // Colonna destra: campi di associazione
                dialog_fields.push({
                    label: 'Item',
                    fieldtype: 'Link',
                    options: 'Item',
                    fieldname: `item_${idx}`,
                    get_query: () => ({
                        query: 'italian_invoice.utilities.fatture_passive.get_items_by_supplier',
                        filters: { 'default_supplier': supplier_data.name }
                    }),
                    reqd: isZeroValue ? 0 : 1,
                    only_select: true
                });
                dialog_fields.push({
                    label: 'Conto di Costo',
                    fieldtype: 'Link',
                    options: 'Account',
                    fieldname: `account_${idx}`,
                    reqd: isZeroValue ? 0 : 1,
                    get_query: () => ({
                        filters: { 'is_group': 0, 'company': frm.doc.company }
                    })
                });
                dialog_fields.push({
                    label: 'Ricorda associazione',
                    fieldtype: 'Check',
                    fieldname: `remember_${idx}`,
                    default: 1
                });
                dialog_fields.push({
                    fieldtype: 'Button',
                    label: 'Crea Nuovo Item',
                    fieldname: `create_item_${idx}`,
                    click: () => {
                        _show_create_item_dialog(frm, d, supplier_data, line, idx);
                    }
                });
            });

            // --- Create dialog ---
            let d = new frappe.ui.Dialog({
                title: 'Associa Prodotti',
                fields: dialog_fields,
                size: 'extra-large',
                primary_action_label: 'Importa',
                primary_action(values) {
                    let item_mappings = {};
                    let remember_mappings = [];

                    invoice_lines.forEach((line, idx) => {
                        if (!values[`item_${idx}`]) return;

                        item_mappings[line.numero_linea] = {
                            item_code: values[`item_${idx}`],
                            account: values[`account_${idx}`],
                            description: line.descrizione,
                            qty: parseFloat(line.quantita) || 1,
                            rate: line.prezzo_unitario,
                            tax_rate: line.aliquota_iva,
                            tax_nature: line.natura
                        };

                        // Raccogli associazioni da ricordare
                        if (values[`remember_${idx}`]) {
                            const codice = _get_codice_articolo(line);
                            remember_mappings.push({
                                item_code: values[`item_${idx}`],
                                supplier_part_no: codice || line.descrizione
                            });
                        }
                    });

                    frappe.call({
                        method: "openapi.api.eInvoice.purchase_invoice.process_supplier_invoice",
                        args: {
                            json_data_string: frm.doc.dati_fattura,
                            fattura_fornitori_sdi: frm.doc.name,
                            item_mappings: item_mappings,
                            remember_mappings: remember_mappings
                        },
                        callback: (r) => {
                            if (r.message) {
                                d.hide();
                                frappe.set_route("Form", "Purchase Invoice", r.message);
                            }
                        }
                    });
                }
            });

            // Auto-fill account when item is selected
            invoice_lines.forEach((line, idx) => {
                d.fields_dict[`item_${idx}`].df.onchange = () => {
                    let item_code = d.get_value(`item_${idx}`);
                    if (item_code) {
                        frappe.db.get_doc('Item', item_code).then(item => {
                            if (item.item_defaults && item.item_defaults.length > 0) {
                                const def = item.item_defaults.find(
                                    dd => dd.company === frm.doc.company
                                );
                                if (def && def.expense_account) {
                                    d.set_value(`account_${idx}`, def.expense_account);
                                }
                            }
                        });
                    }
                };
            });

            // Auto-match items
            frappe.call({
                method: 'italian_invoice.utilities.fatture_passive.find_matching_items',
                args: {
                    supplier_name: supplier_data.name,
                    invoice_lines: invoice_lines
                },
                callback: (r) => {
                    if (r.message) {
                        invoice_lines.forEach((line, idx) => {
                            const match = r.message[line.numero_linea];
                            if (match) {
                                d.set_value(`item_${idx}`, match.item_code);
                                if (match.expense_account) {
                                    d.set_value(`account_${idx}`, match.expense_account);
                                }
                            }
                        });
                    }
                }
            });

            d.show();
        }
    });
}


function _show_create_item_dialog(frm, parent_dialog, supplier_data, line, idx) {
    const codice = _get_codice_articolo(line);

    let item_dialog = new frappe.ui.Dialog({
        title: 'Crea Nuovo Item',
        fields: [
            {
                label: 'Nome Item',
                fieldtype: 'Data',
                fieldname: 'item_name',
                default: (line.descrizione || '').trim().slice(0, 140),
                reqd: 1
            },
            {
                label: 'Item Group',
                fieldtype: 'Link',
                fieldname: 'item_group',
                options: 'Item Group',
                reqd: 1,
                default: 'Services'
            },
            {
                label: 'Unità di Misura',
                fieldtype: 'Link',
                fieldname: 'uom',
                options: 'UOM',
                reqd: 1,
                default: frappe.sys_defaults.stock_uom || 'Nos'
            },
            {
                label: 'Conto di Costo',
                fieldtype: 'Link',
                options: 'Account',
                fieldname: 'expense_account',
                reqd: 1,
                get_query: () => ({
                    filters: { 'is_group': 0, 'company': frm.doc.company }
                })
            }
        ],
        primary_action_label: 'Crea',
        primary_action(values) {
            frappe.call({
                method: 'italian_invoice.utilities.fatture_passive.create_supplier_item',
                args: {
                    item_name: values.item_name,
                    item_group: values.item_group,
                    uom: values.uom,
                    expense_account: values.expense_account,
                    company: frm.doc.company,
                    supplier: supplier_data.name,
                    supplier_part_no: codice || line.descrizione
                },
                callback: (r) => {
                    if (r.message) {
                        item_dialog.hide();
                        parent_dialog.set_value(`item_${idx}`, r.message);
                        parent_dialog.set_value(`account_${idx}`, values.expense_account);
                        frappe.show_alert({
                            message: __('Item creato con successo'),
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    });
    item_dialog.show();
}


function check_open_purchase_documents(frm) {
    frappe.call({
        method: 'italian_invoice.utilities.fatture.get_invoice_number_from_json',
        args: { invoice_data: frm.doc.dati_fattura },
        callback: (r) => {
            const bill_no = r.message;
            frappe.call({
                method: 'italian_invoice.utilities.fatture_passive.get_open_purchase_documents_summary',
                args: { supplier_vat: frm.doc.partita_iva_fornitore },
                callback: (r) => {
                    if (r.message) {
                        const pos = r.message.purchase_orders || [];
                        const prs = r.message.purchase_receipts || [];
                        if (pos.length + prs.length > 0) {
                            show_po_pr_in_form(frm, pos, prs, bill_no);
                        } else {
                            frm.get_field('documenti_aperti').$wrapper.html('');
                        }
                    }
                }
            });
        }
    });
}


function _build_doc_table(docs, label, bill_no) {
    if (!docs.length) return '';
    let rows = '';
    docs.forEach(doc => {
        rows += `<tr>
            <td>${doc.name}</td>
            <td style="text-align: right;">${format_currency(doc.grand_total)}</td>
            <td style="text-align: center;">
                <button class="btn btn-primary btn-sm btn-create-from-doc"
                    data-doc-name="${doc.name}" data-doctype="${label}" data-bill-no="${bill_no}">Crea Fattura</button>
            </td>
        </tr>`;
    });
    return `<div style="margin-bottom: 20px;">
        <b>${label} (${docs.length}):</b>
        <table class="table table-bordered" style="margin-top: 10px; background-color: white;">
            <thead><tr>
                <th style="width: 50%;">Documento</th>
                <th style="width: 30%; text-align: right;">Importo</th>
                <th style="width: 20%; text-align: center;">Azione</th>
            </tr></thead><tbody>${rows}</tbody>
        </table>
    </div>`;
}


function show_po_pr_in_form(frm, purchase_orders, purchase_receipts, bill_no) {
    const total = purchase_orders.length + purchase_receipts.length;
    const html = `
        <div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 15px; margin-bottom: 15px;">
            <h5 style="margin-top: 0; color: #856404;">
                <i class="fa fa-exclamation-triangle"></i>
                Attenzione! Ci sono <b>${total} documenti aperti</b> per questo fornitore
            </h5>
            ${_build_doc_table(purchase_orders, 'Purchase Order', bill_no)}
            ${_build_doc_table(purchase_receipts, 'Purchase Receipt', bill_no)}
        </div>`;

    const $wrapper = frm.get_field('documenti_aperti').$wrapper;
    $wrapper.html(html);

    // Event delegation: un solo handler, nessun leak globale
    $wrapper.off('click', '.btn-create-from-doc').on('click', '.btn-create-from-doc', function () {
        const $btn = $(this);
        frappe.call({
            method: 'italian_invoice.utilities.fatture_passive.create_purchase_invoice_from_document',
            args: {
                doc_name: $btn.data('doc-name'),
                doctype: $btn.data('doctype'),
                bill_no: $btn.data('bill-no'),
                fattura_sdi_name: frm.doc.name
            },
            callback: (r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Purchase Invoice creata con successo'),
                        indicator: 'green'
                    });
                    frappe.set_route('Form', 'Purchase Invoice', r.message);
                }
            }
        });
    });
}
