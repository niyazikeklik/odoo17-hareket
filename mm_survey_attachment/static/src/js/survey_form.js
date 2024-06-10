odoo.define('mm.survey.form', function (require) {
'use strict';

var SurveyFormWidget = require('survey.form');
var utils = require('web.utils');

SurveyFormWidget.include({
    // Possible add file validation on client side when it mandatory question
    start: function () {
        console.log("test3");
        this.fileEncoderPromises = [];
        var self = this;
        return this._super.apply(this, arguments)
    },

    // Rewrite _submitForm to catch promise that converts file to base64 format.
    _submitForm: function (options) {
        console.log("test4");
        var self = this;
        var params = {};
        if (options.previousPageId) {
            params.previous_page_id = options.previousPageId;
        }
        var route = "/survey/submit";

        if (this.options.isStartScreen) {
            route = "/survey/begin";
            // Hide survey title in 'page_per_question' layout: it takes too much space
            if (this.options.questionsLayout === 'page_per_question') {
                this.$('.o_survey_main_title').fadeOut(400);
            }
        } else {
            var $form = this.$('form');
            var formData = new FormData($form[0]);

            if (!options.skipValidation) {
                // Validation pre submit
                if (!this._validateForm($form, formData)) {
                    return;
                }
            }
            this.fileEncoderPromises = [];
            this._prepareSubmitValues(formData, params);
        }

        // prevent user from submitting more times using enter key
        this.preventEnterSubmit = true;

        if (this.options.sessionInProgress) {
            // reset the fadeInOutDelay when attendee is submitting form
            this.fadeInOutDelay = 400;
            // prevent user from clicking on matrix options when form is submitted
            this.readonly = true;
        }

        var submitPromise = Promise.all(this.fileEncoderPromises).then(() => {
            return self._rpc({
                route: _.str.sprintf('%s/%s/%s', route, self.options.surveyToken, self.options.answerToken),
                params: params,
            });
        });

        this._nextScreen(submitPromise, options);
    },

    _prepareSubmitValues: function (formData, params) {
        console.log("test2");
        var self = this;

        var result = this._super.apply(this, arguments);
        this.$('[data-question-type]').each(function () {
            if ($(this).data('questionType') == 'file') {
                self._prepareSubmitAnswerFile(params, $(this), this.name);
            }
        });

        return result;
    },

    _prepareSubmitAnswerFile: function (params, $parent, questionId) {
        console.log("test1");
        const file = $parent[0].files[0];
        if (file) {
            var fileEncoderPromise = utils.getDataURLFromFile(file).then(function (data) {
                data = data.split(',')[1];
                params[questionId] = [file.name, data];
            });
            this.fileEncoderPromises.push(fileEncoderPromise);
        }

    },
})

});
