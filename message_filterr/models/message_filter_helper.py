from odoo import models
class MessageFilterHelper(models.Model):

    _name = "message.filter.helper"
    _description = "Message Filter Helper"

    def removedCount(self, text):
        count1 = text.count(" ")
        count2 = text.count("\n")
        count3 = text.count("\t")
        count4 = text.count("\r")
        count5 = text.count("'")
        return count1 + count2 + count3 + count4 + count5
    


    def _normalize_text(self, text):
        if text:
            text = text.lower()
            text = text.replace("ı", "i")
            text = text.replace("ö", "o")
            text = text.replace("ü", "u")
            text = text.replace("ğ", "g")
            text = text.replace("ş", "s")
            text = text.replace("ç", "c")
            text = text.replace("\\", "")
            #text = text.replace(" ", "")
            #text = text.replace("\n", "")
            #text = text.replace("\t", "")
            #text = text.replace("\r", "")
            #text = text.replace("'", "")
            return text
        else:
            return ""

    def get_cleaned_text(self, text, model_id):
        filters = self.env["message.filter"].search([("active", "=", True), ("model_id", "=", model_id)],
                                                    order="sequence")
        for model_filter in filters:
            replace_text = ""
            if model_filter.replace_with:
                replace_text = model_filter.replace_with
            index_start = self._normalize_text(text).find(self._normalize_text(model_filter.baslangic))
            if index_start and model_filter.baslangic:
                index_end_start = index_start + len(model_filter.baslangic)
                index_end = self._normalize_text(text).find(self._normalize_text(model_filter.bitis), index_end_start)
                if index_start == -1 or index_end == -1:
                    continue
                else :
                    index_end += len(model_filter.bitis)
                text2 = text[index_start:index_end]
                text = text.replace(text2, replace_text)
            else:
                return text
        return str(text).replace("><<", "><").replace(">><", "><");
    