from odoo import models, fields, api


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    tr_mut_id = fields.Many2one("tr.mut", "Mutabakat", ondelete="set null")

    @api.model
    def _mark_done(self):
        super(SurveyUserInput, self)._mark_done()
        if self.tr_mut_id:
            answers = self.env["survey.user_input.line"].search([("user_input_id", "=", self.id)])
            for answer in answers:
                if answer.question_id.id == self.env.ref("tr_mutabakat.tr_mut_survey_q1").id:
                    if answer.suggested_answer_id.id == self.env.ref("tr_mutabakat.tr_mut_survey_q1_a1").id:
                        self.tr_mut_id.write({
                            "state":"Kabul Edildi"
                        })
                    elif answer.suggested_answer_id.id == self.env.ref("tr_mutabakat.tr_mut_survey_q1_a2").id:
                        self.tr_mut_id.write({
                            "state": "Reddedildi"
                        })
                elif answer.question_id.id == self.env.ref("tr_mutabakat.tr_mut_survey_q_red").id:
                    self.tr_mut_id.write({
                        "red_aciklama": answer.value_text_box
                    })

                elif answer.question_id.id == self.env.ref("tr_mutabakat.tr_mut_survey_q2").id:
                    answer.value_file.write({
                        "res_id":self.tr_mut_id.id,
                        "res_model": "tr.mut"
                    })
