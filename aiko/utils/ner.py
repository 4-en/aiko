# static class to share NER model

import spacy

class NER:
    nlp = spacy.load("en_core_web_sm")

    @staticmethod
    def get_entities(text: str):
        """
        Get named entities from a text.
        
        Parameters
        ----------
        text : str
            The text
        
        Returns
        -------
        list
            A list of tuples with the entity text and the entity label
        """
        doc = NER.nlp(text)
        allowed_entities = {"PERSON", "ORG", "GPE", "NORP", "FAC", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART", "LAW", "LANGUAGE"}
        return [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in allowed_entities]