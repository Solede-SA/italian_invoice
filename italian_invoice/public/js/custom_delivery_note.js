frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        console.log("Custom Delivery Note JS loaded - refresh event");
        // Solo per DDT submitted
        if (frm.doc.docstatus !== 1) return;

        // Se non è completamente fatturato
        if (frm.doc.per_billed < 100) {
            // Calcola il gap di fatturazione
            frappe.call({
                method: "italian_invoice.api.delivery_note_billing_adjustment.calculate_billing_gap",
                args: {
                    delivery_note_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        // Mostra il gap nel dashboard
                        if (r.message.billing_gap > 0) {
                            frm.dashboard.add_indicator(
                                __('Billing Gap: {0}', [format_currency(r.message.billing_gap, frm.doc.currency)]),
                                r.message.can_force_complete ? 'orange' : 'red'
                            );
                        }

                        // Se può essere forzato, mostra il bottone
                        if (r.message.can_force_complete) {
                            frm.add_custom_button(__('Force Complete Billing'), function() {
                                frappe.prompt({
                                    label: 'Reason',
                                    fieldname: 'reason',
                                    fieldtype: 'Small Text',
                                    reqd: 1,
                                    description: __('Please provide a reason for forcing the billing completion. Difference: {0}',
                                        [format_currency(r.message.billing_gap, frm.doc.currency)])
                                }, function(values){
                                    frappe.call({
                                        method: "italian_invoice.api.delivery_note_billing_adjustment.force_billing_complete",
                                        args: {
                                            delivery_note_name: frm.doc.name,
                                            reason: values.reason
                                        },
                                        freeze: true,
                                        freeze_message: __("Updating billing status..."),
                                        callback: function(r) {
                                            if (r.message) {
                                                frm.reload_doc();
                                            }
                                        }
                                    });
                                }, __('Force Billing Completion'), __('Confirm'));
                            }, __('Actions'));

                            // Evidenzia il bottone
                            frm.page.set_inner_btn_group_as_primary(__('Actions'));
                        }
                    }
                }
            });
        }

        // Se è stato forzato, mostra bottone per annullare
        if (frm.doc.per_billed === 100) {
            // Controlla se esiste un aggiustamento
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Delivery Note Billing Adjustment Log",
                    filters: {
                        delivery_note: frm.doc.name
                    },
                    limit: 1
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        // Mostra indicatore
                        frm.dashboard.add_indicator(__('Billing Forced to Complete'), 'blue');

                        // Aggiungi bottone per annullare
                        frm.add_custom_button(__('Revert Billing Adjustment'), function() {
                            frappe.confirm(
                                __('Are you sure you want to revert the billing adjustment?'),
                                function() {
                                    frappe.call({
                                        method: "italian_invoice.api.delivery_note_billing_adjustment.revert_billing_adjustment",
                                        args: {
                                            delivery_note_name: frm.doc.name
                                        },
                                        freeze: true,
                                        freeze_message: __("Reverting billing adjustment..."),
                                        callback: function(r) {
                                            if (r.message) {
                                                frm.reload_doc();
                                            }
                                        }
                                    });
                                }
                            );
                        }, __('Actions'));
                    }
                }
            });
        }

        // Aggiungi bottone per vedere i log di aggiustamento
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('View Adjustment Logs'), function() {
                frappe.set_route("List", "Delivery Note Billing Adjustment Log", {
                    "delivery_note": frm.doc.name
                });
            }, __('View'));
        }
    },

    onload: function(frm) {
        console.log("Custom Delivery Note JS loaded - onload event");
        // Calcola il gap quando il documento viene caricato
        if (frm.doc.docstatus === 1) {
            console.log("Calling calculate_billing_gap for:", frm.doc.name);
            // Aggiungi un piccolo delay per assicurarsi che il form sia completamente caricato
            setTimeout(function() {
                frappe.call({
                    method: "italian_invoice.api.delivery_note_billing_adjustment.calculate_billing_gap",
                    args: {
                        delivery_note_name: frm.doc.name
                    },
                    callback: function(r) {
                        console.log("Billing gap response:", r.message);
                        if (r.message && r.message.billing_gap !== undefined) {
                            console.log("Current custom_billing_gap:", frm.doc.custom_billing_gap);
                            console.log("New billing_gap:", r.message.billing_gap);
                            // Aggiorna il campo se il valore è cambiato
                            if (frm.doc.custom_billing_gap != r.message.billing_gap) {
                                console.log("Updating custom_billing_gap from", frm.doc.custom_billing_gap, "to", r.message.billing_gap);
                                frm.set_value('custom_billing_gap', r.message.billing_gap);
                                // Salva automaticamente per evitare che il form rimanga "dirty"
                                frm.save('Update');
                            }
                        }
                    },
                    error: function(err) {
                        console.error("Error calling calculate_billing_gap:", err);
                    }
                });
            }, 500); // Delay di 500ms
        }
    }
});