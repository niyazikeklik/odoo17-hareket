/** @odoo-module **/
// import DocumentViewer from '@mail/component/document_viewer';
// import view_registry from 'web.view_registry';
// import ActionMenus from 'web.ActionMenus';
import { spiffyDocumentViewer } from "@spiffy_theme_backend/js/widgets/spiffyDocumentViewer";
import { ListRenderer } from "@web/views/list/list_renderer";
// import { registerPatch } from '@mail/model/model_core';
// import "@mail/models/file_uploader";
import { useService } from "@web/core/utils/hooks";

import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";

import { registry } from "@web/core/registry";
import { divertColorItem } from "./apps_menu";
import { session } from '@web/session';
import { FileViewer } from "@web/core/file_viewer/file_viewer";
import { AttachmentList } from "@mail/core/common/attachment_list";
import { SplitviewContainer } from './split_view/split_view_container';
import { beforeSplitViewOpen } from "./split_view/split_view_components";

const serviceRegistry = registry.category("services");
const userMenuRegistry = registry.category("user_menuitems");

import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { AttachmentUploadService } from "@mail/core/common/attachment_upload_service";
import { onMounted, useState, useChildSubEnv, whenReady } from "@odoo/owl";

// TODO add list view document here , old way will not work
/**
 * @property {import("models").Attachment[]} attachments
 * @extends {ListRenderer<Props, Env>}
 */
patch(ListRenderer.prototype, {

    setup() {
        super.setup();
        var self = this
        this.fileViewer = useFileViewer();
        self.showattachment = false
        if ($('body').hasClass('show_attachment')) {
            self.showattachment = true
        }
        var rec_ids = []
        this.notificationService = useService("notification");
        var records = this.props.list.records
        var model = this.props.list.resModel
        records.map(record => rec_ids.push(record.resId))
        jsonrpc("/get/attachment/data", {
            model: model,
            rec_ids: rec_ids,
        }).then(function (data) {
            if (data) {
                self.biz_attachment_data = data;
            }
        });

        onMounted(() => {
            if ($('.o_action_manager > .o_view_controller.o_list_view > .o_control_panel .reload_view').length) {
                $('.o_action_manager > .o_view_controller.o_list_view > .o_control_panel .reload_view').click()
            }
        });
        // split view code

        this.SplitViewForm = useState({
            show: false,
            id: 0,
        })

        const formViewId = this.getFormViewId()
        useChildSubEnv({
            config: {
                ...this.env.config,
                isX2Many: this.isX2Many,
                views: [[formViewId, 'form']],
                close: this.closeSplitViewForm.bind(this),
            },
        });
    },

    close: function(){
        registry.category("main_components").remove('spiffy_document');
    },

    _loadattachmentviewer(ev) {
        var attachment_id = parseInt($(ev.currentTarget).data("id"));
        var rec_id = parseInt($(ev.currentTarget).data("rec_id"));
        var attachment_mimetype = $(ev.currentTarget).data("mimetype");
        var mimetype_match = attachment_mimetype.match("(image|application/pdf|text|video)");
        var attachment_data = this.biz_attachment_data[0];

        if (mimetype_match) {
            var biz_attachment_id = attachment_id;
            var biz_attachment_list = [];
            attachment_data[rec_id].forEach((attachment) => {
                if (attachment.attachment_mimetype.match("(image|application/pdf|text|video)")) {
                    biz_attachment_list.push({
                        id: attachment.attachment_id,
                        filename: attachment.attachment_name,
                        name: attachment.attachment_name,
                        url: "/web/content/" + attachment.attachment_id + "?download=true",
                        type: attachment.attachment_mimetype,
                        mimetype: attachment.attachment_mimetype,
                        is_main: false,
                    });
                }
            });
            
            registry.category("main_components").add('spiffy_document', {
                Component: spiffyDocumentViewer,
                props: { attachments: biz_attachment_list, activeAttachmentID: biz_attachment_id},
            });

            // await whenReady();
        } else {
            this.notificationService.add(_t("Preview for this file type can not be shown"), {
                title: _t("File Format Not Supported"),
                type: 'danger',
                sticky: false
            });
        }
    },

    // split view functions

    getFormViewId() {
        return this.env.config.views.find(view => view[1] === 'form')?.[0] || false
    },

    getSplitviewContainerProps() {
        const resIds = this.props.list.records.map((record) => record.resId);
        const props = {
            context: {
                ...this.SplitViewFormRecord.context,
            },
            record: this.SplitViewFormRecord,
            resModel: this.props.list.resModel,
            resId: this.SplitViewForm.id,
            resIds: resIds,
        }
        const viewId = this.getFormViewId()
        if (viewId) {
            props.viewId = viewId
        }
        return props
    },

    async callbeforeSplitViewOpen() {
        return await Promise.all(beforeSplitViewOpen.map(func => func()))
    },
    /**
     * @param {Object} record
     * @param {Object} column
     * @param {PointerEvent} ev
     */
    async onCellClicked(record, column, ev) {
        var split_view_enabled = $('body').hasClass('tree_form_split_view')

        if ((!this.isX2Many && !split_view_enabled) || (this.isX2Many && !this.props.archInfo.splitView) || (this.props.archInfo.editable)) {
            return await super.onCellClicked(record, column, ev);
        }
        if (ev.target.special_click) {
            return;
        }
        if (record.resId && this.SplitViewForm.id !== record.resId && !this.props.archInfo.editable) {
            await this.callbeforeSplitViewOpen();
            this.SplitViewForm.id = record.resId;
            this.SplitViewForm.show = true;
            this.SplitViewFormRecord = record;
            this.recordDatapointID = record.id;
        }
    },

    async closeSplitViewForm() {
        await this.callbeforeSplitViewOpen();
        this.SplitViewForm.show = false;
        this.SplitViewForm.id = false;
        $('.tree_form_split > .o_view_controller > .o_content > .spiffy_list_view > #separator').remove()
        // $('.tree_form_split > .o_view_controller > .o_content > .spiffy_list_view > .close_form_view').remove()
        $('.o_action_manager.tree_form_split').removeClass('tree_form_split')
        $('.spiffy_list_view').attr('style', '')
        $('.o_list_table .o_data_row').removeClass('side-selected')
    },

});

const getAttachmentNextTemporaryId = (function () {
    let tmpId = 0;
    return () => {
        tmpId -= 1;
        return tmpId;
    };
})();

patch(AttachmentUploadService.prototype, {
    get uploadURL() {
        if (session.bg_color){
            return "/app/attachment/upload";
        }
        else{
            return "/mail/attachment/upload";
        }
    },
});

patch(AttachmentList.prototype, {
    /**
     * @param {import("models").Attachment} attachment
     */
    onClickDownload(attachment) {
        if (session.bg_color) {
            var attach_id = attachment.id
            jsonrpc("/attach/get_data", {
                id: attach_id
            }).then(function (data) {
                if (data) {
                    window.flutter_inappwebview.callHandler('blobToBase64Handler', btoa(data['pdf_data']), data['attach_type'], data['attach_name']);
                }
            });
        } else {
            super.onClickDownload(attachment);
        }
    }
});

patch(FileViewer.prototype, {
    setup() {
        super.setup();
        this.bg_color = session.bg_color;
    },

    _spiffyattachmentdownload(){
        // var attach_id = this.id
        var localId = this.props.files[this.props.startIndex].localId;
        var match = localId.match(/\d+/);
        var numericPart = match ? match[0] : null;
        jsonrpc("/attach/get_data", {
            id: numericPart
        }).then(function (data) {
            if (data) {
                window.flutter_inappwebview.callHandler('blobToBase64Handler', btoa(data['pdf_data']), data['attach_type'], data['attach_name']);
            }
        });
    }
});

// registerPatch({
//     name: 'Attachment',
//     recordMethods: {
//         /**
//          * Handles click on download icon.
//          *
//          * @param {MouseEvent} ev
//          */
//         onClickDownload(ev) {
//             if (session.bg_color) {
//                 var attach_id = this.id
//                 ajax.jsonrpc("/attach/get_data", "call", {
//                     id: attach_id
//                 }).then(function (data) {
//                     if (data) {
//                         window.flutter_inappwebview.callHandler('blobToBase64Handler', btoa(data['pdf_data']), data['attach_type'], data['attach_name']);
//                     }
//                 });
//             } else {
//                 this._super.apply(this, arguments);
//             }
//         },
//     }
// })

// registerPatch({
//     name: 'AttachmentViewerViewable',
//     recordMethods: {
//         download() {
//             if (session.bg_color) {
//                 var attach_id = this.attachmentOwner.id
//                 ajax.jsonrpc("/attach/get_data", "call", {
//                     id: attach_id
//                 }).then(function (data) {
//                     if (data) {
//                         window.flutter_inappwebview.callHandler('blobToBase64Handler', btoa(data['pdf_data']), data['attach_type'], data['attach_name']);
//                     }
//                 });
//             } else {
//                 this._super.apply(this, arguments);
//             }
//         },
//     }
// })

// registerPatch({
//     name: 'AttachmentImage',
//     recordMethods: {
//         /**
//          * Called when clicking on download icon.
//          *
//          * @param {MouseEvent} ev
//          */
//         onClickDownload(ev) {
//             if (session.bg_color) {
//                 var attach_id = this.attachment.id
//                 ajax.jsonrpc("/attach/get_data", "call", {
//                     id: attach_id
//                 }).then(function (data) {
//                     if (data) {
//                         window.flutter_inappwebview.callHandler('blobToBase64Handler', btoa(data['pdf_data']), data['attach_type'], data['attach_name']);
//                     }
//                 });
//             } else {
//                 this._super.apply(this, arguments);
//             }
//         }
//     }
// })

const bg_colorService = {
    start() {
        var is_body_color = session.bg_color
        if (is_body_color) {
            userMenuRegistry.remove('log_out');
            userMenuRegistry.remove('odoo_account');
            userMenuRegistry.remove('documentation');
            userMenuRegistry.remove('support');

            userMenuRegistry.add("divert.account", divertColorItem);
        }
    },
};
serviceRegistry.add("bg_color", bg_colorService);

ListRenderer.components = {
    ...ListRenderer.components,
    SplitviewContainer,
};
