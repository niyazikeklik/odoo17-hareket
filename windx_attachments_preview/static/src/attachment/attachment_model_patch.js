/* @odoo-module */

import { Attachment } from "@mail/core/common/attachment_model";
import { patch } from "@web/core/utils/patch";

patch(Attachment.prototype, {
    get isDoc() {
        return this.extension.toLowerCase() === "doc" && this.mimetype.toLowerCase().includes("officedocument");
    },
    get isDocx() {
        return (this.extension.toLowerCase() === "docx" && this.mimetype.toLowerCase().includes("officedocument"));
    },
    get isPPT() {
        return this.extension.toLowerCase() === "ppt" && this.mimetype.toLowerCase().includes("officedocument");
    },
    get isPPTX() {
        return this.extension.toLowerCase() === "pptx" && this.mimetype.toLowerCase().includes("officedocument");
    },
    get isXLS() {
        return this.extension.toLowerCase() === "xls" && this.mimetype.toLowerCase().includes("ms-excel");
    },
    get isXLSX() {
        return this.extension.toLowerCase() === "xlsx" && this.mimetype.toLowerCase().includes("officedocument");
    },
    get isMsg() {
        return this.extension.toLowerCase() === "msg";
    },

    get isOfficeFile() {
        return ((this.isDocx || this.isPPTX || this.isXLSX) && !this.uploading);
    },

    /*get isOfficeFileOld() {
        return ((this.isDoc || this.isPPT || this.isXLS) && !this.uploading);
    },*/

    get isViewable() {
        return this.isOfficeFile || super.isViewable;
    },

});
