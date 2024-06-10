/*
odoo.define('hr_puantaj.hr_work_entry_dialog', function (require) {
    "use strict";
    import {useService} from "@web/core/utils/hooks";
    import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
    this.rpc = useService("rpc");
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;


    const HrWorkEntryConfirmDialog = ConfirmationDialog.extend({
        template: "hr_puantaj.HrWorkEntryConfirmDialog",

        willStart: function () {
            const resize = Boolean(this._trigger_resize);
            return this._super.apply(this, arguments).then(() => {
                // Render modal once xml dependencies are loaded
                this.$modal = $(
                    QWeb.render("announcement.AnnouncementDialog", {
                        title: this.title,
                        subtitle: this.subtitle,
                        resize: resize,
                    })
                );
                // Soft compatibility with OCAs `web_dialog_size`
                if (resize) {
                    this.$modal
                        .find(".dialog_button_extend")
                        .on("click", this.proxy("_extending"));
                    this.$modal
                        .find(".dialog_button_restore")
                        .on("click", this.proxy("_restore"));
                    rpc.query({
                        model: "ir.config_parameter",
                        method: "announcement_full_size",
                    }).then((config_full_size) => {
                        if (config_full_size) {
                            this._extending();
                            return;
                        }
                        this._restore();
                    });
                }
                this.$footer = this.$modal.find(".modal-footer");
                this.set_buttons(this.buttons);
                this.$modal.on("hidden.bs.modal", _.bind(this.destroy, this));
            });
        },
    });
});
*/