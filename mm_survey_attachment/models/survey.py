import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    question_type = fields.Selection(
        selection_add=[('file', 'Upload file')])
    mm_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment', string='Survey file')


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    answer_type = fields.Selection(
        selection_add=[('file', 'Upload file')])
    value_file = fields.Many2one(
        comodel_name='ir.attachment', string='Survey file', readonly=True,)
    filename = fields.Char(
        compute='_compute_website_url', )
    website_url = fields.Char(
        compute='_compute_website_url', )

    @api.depends('value_file')
    def _compute_website_url(self):
        burl = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for obj in self:
            if not obj.value_file:
                obj.website_url = obj.filename = ''
                continue
            att = self.env['ir.attachment'].sudo().search([
                ('id', '=', obj.value_file.id)], limit=1)
            if not att:
                obj.website_url = obj.filename = ''
                continue
            token = att.generate_access_token()
            token = token[0] if token else ''
            obj.filename = att.name
            obj.website_url = \
                '{}/web/content/ir.attachment/{}/datas/{}?access_token={}' \
                ''.format(burl, att.id, att.name, token)



class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    def save_lines(self, question, answer, comment=None):
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id),
            ('question_id', '=', question.id), ])
        if question.question_type == 'file':
            res = self._save_line_file(question, old_answers, answer)
        else:
            res = super().save_lines(question, answer, comment)
        return res

    def _save_line_file(self, question, user_input_line, answer):
        vals = (self._get_line_answer_file(
            question, answer, question.question_type))
        if user_input_line:
            user_input_line.write(vals)
        else:
            user_input_line = self.env['survey.user_input.line'].create(vals)
        return user_input_line

    def _get_line_answer_file(self, question, answer, answer_type):
        vals = {'user_input_id': self.id, 'question_id': question.id,
                'skipped': False, 'answer_type': answer_type, }
        if not answer or (isinstance(answer, str) and not answer.strip()):
            vals.update(answer_type=None, skipped=True)
            return vals
        attachment = self.env['ir.attachment'].create({
            'name': answer[0], 'datas': answer[1], 'type': 'binary', })
        vals['value_file'] = int(attachment.id) if attachment else False
        return vals
