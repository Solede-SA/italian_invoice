// Copyright (c) 2024, Solede SA and contributors
// For license information, please see license.txt

frappe.ui.form.on("Transazione SDI", {
    refresh: function (frm) {
        frm.disable_save();

        frm.set_df_property('notifiche_sdi', 'cannot_add_rows', true); // Hide add row button
        frm.set_df_property('notifiche_sdi', 'cannot_delete_rows', true); // Hide delete button
        frm.set_df_property('notifiche_sdi', 'cannot_delete_all_rows', true); // Hide delete all button

        if (frm.doc.notifiche_sdi && frm.doc.notifiche_sdi.length) {
            frm.doc.notifiche_sdi.sort((a, b) => {
                return new Date(b.data_notifica) - new Date(a.data_notifica);
            });
        }

        frm.add_custom_button(
            __("Scarica PDF"),
            () => {
                let url = "/api/method/openapi.api.sdi.fatture.download?doctype=" + frm.doc.tipo_fattura + "&docname=" + frm.doc.fattura + "&type=pdf";
                // window.open(url);
                window.location.href = url
            }
        );

        if (frm.doc.ultima_notifica) {
            let utlima_notifica = JSON.parse(frm.doc.ultima_notifica);

            // Crea un div vuoto per visualizzare le notifiche
            let notificationContainer = $('<div>').appendTo(frm.fields_dict['uuid'].wrapper);

            // Funzione ricorsiva per iterare attraverso l'oggetto JSON e costruire una lista puntata
            function displayNotification(data, parentElement, depth = 0) {
                let ul = $('<ul>').css('margin-left', depth > 0 ? '20px' : '0').appendTo(parentElement);
                for (let key in data) {
                    let li = $('<li>').appendTo(ul);
                    if (typeof data[key] === 'object' && data[key] !== null) {
                        $('<strong>').text(key + ': ').appendTo(li);
                        displayNotification(data[key], li, depth + 1);
                    } else {
                        $('<span>').html(`<strong>${key}:</strong> ${data[key]}`).appendTo(li);
                    }
                }
            }

            // Determina quale parte del JSON visualizzare in base alla struttura
            let dataToDisplay = null;
            if (utlima_notifica.notification) {
                dataToDisplay = utlima_notifica.notification;
            } else if (utlima_notifica.data && utlima_notifica.data.notification) {
                dataToDisplay = utlima_notifica.data.notification;
            } else if (utlima_notifica.data && utlima_notifica.data.data) {
                dataToDisplay = utlima_notifica.data.data;
            } else {
                dataToDisplay = utlima_notifica;
            }

            displayNotification(dataToDisplay, notificationContainer);
        }


    }
});

