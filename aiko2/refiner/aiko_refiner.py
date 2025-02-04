from .base_refiner import BaseRefiner
from aiko2.core import Conversation, Message
import re
import random

class AikoRefiner(BaseRefiner):
    """
    A test refiner to test pipeline functionality.
    """
    
    # Define the replacements dictionary, including new anime-fox/Senko-san inspired mappings.
    replacements = {
        "now":        "nyow",
        "hello":      "hewwo",
        "nice":       "nyice",
        "good":       "gwood",
        "great":      "gweat",
        "hi":         "hai",
        "hey":        "hai",
        "bye":        "byebye",
        "sorry":      "sowwy",
        "love":       "wuv",
        "really":     "weally",
        "what":       "nani",
        "yes":        "yus",
        "no":         "nu",
        "friend":     "fwend",
        "cute":       "kawaii",
        "cool":       "coow",
        "sleep":      "sweep",
        "eat":        "nom nom",
        "food":       "nyum-nyum",
        
        # Additional fox-like and Senko-san inspired replacements:
        "fox":        "kitsune",
        "fluffy":     "fuwafuwa",
        "sleepy":     "sweepy",
        "maybe":      "may-kon",
        "thanks":     "thankyuwu",
        "thank":      "thankyuwu",
        "play":       "pway",
        "adorable":   "adawable",
        "snuggle":    "snuggly-wuggly",
        "hug":        "huggies",
        "amazing":    "sugoi",
        "lucky":      "wucky",
        "hungry":     "nummy",
        "tired":      "tiwed",
        "scared":     "scawy",
        "excited":    "excito",
        "dinner":     "din-din",
        "lunch":      "wunch",
        "breakfast":  "brekky",
        "snack":      "snax",
    }
    
    def replacement_func(self, match, selected_positions):
        # Replace only if this match's start index was selected.
        if match.start() in selected_positions:
            word = match.group(0)
            # Get the replacement by looking up the lowercase version of the word.
            repl = AikoRefiner.replacements[word.lower()]
            # Preserve the original capitalization:
            if word.isupper():
                return repl.upper()
            elif word[0].isupper():
                return repl.capitalize()
            else:
                return repl
        else:
            # Otherwise, leave the original word unchanged.
            return match.group(0)
        
    _keyboard_rows = [
        "qwertyuiop",
        "asdfghjkll",
        "zxcvbnm,.-"
    ]
        
    def apply_spelling_error(self, word:str) -> str:
        """
        Apply a spelling error to a word.

        Parameters
        ----------
        word : str
            The word to apply the spelling error to.

        Returns
        -------
        str
            The word with a spelling error applied.
        """
        
        if len(word) < 3:
            return word
        
        # Randomly choose between two types of spelling errors.
        if random.random() < 0.5:
            # Swap two random characters in the word.
            idx1 = random.randint(1, len(word) - 2)
            idx2 = ( idx1 + 1 ) % len(word)
            return word[:idx1] + word[idx2] + word[idx1] + word[idx2+1:]
        else:
            # replace a character with one close to it on the keyboard
            idx = random.randint(0, len(word) - 1)
            row_idx, position = -1, -1
            for i, row in enumerate(AikoRefiner._keyboard_rows):
                if word[idx] in row:
                    row_idx = i
                    position = row.index(word[idx])
                    break
            if row == -1:
                return word
            new_row = max(0, min(2, row_idx + random.randint(-1, 1)))
            new_position = max(0, min(len(AikoRefiner._keyboard_rows[new_row]) - 1, position + random.randint(-1, 1)))
            new_char = AikoRefiner._keyboard_rows[new_row][new_position]
            return word[:idx] + new_char + word[idx+1:]
                
    def apply_case_error(self, word:str) -> str:
        """
        Apply a case error to a word.

        Parameters
        ----------
        word : str
            The word to apply the case error to.

        Returns
        -------
        str
            The word with a case error applied.
        """
        
        # If the first character is uppercase, make it lowercase.
        if word[0].isupper():
            return word[0].lower() + word[1:]
        return word
    
    def apply_punctuation_error(self, word:str) -> str:
        """
        Apply a punctuation error to a word.

        Parameters
        ----------
        word : str
            The word to apply the punctuation error to.

        Returns
        -------
        str
            The word with a punctuation error applied.
        """
        
        # remove any punctuation from the word
        punctuation = [".", ",", "!", "?", ":", ";", "'", '"', "-", "_"]
        for p in punctuation:
            word = word.replace(p, "")
        return word
    
    def vary_punctuation(self, word:str) -> str:
        if word.endswith("."):
            word = word[:-1] + random.choice(["...", "...", "...", "..." "!"])
        return word
    
    def apply_grammar_error(self, word:str) -> str:
        """
        Apply a grammar error to a word.

        Parameters
        ----------
        word : str
            The word to apply the grammar error to.

        Returns
        -------
        str
            The word with a grammar error applied.
        """
        
        
        articles = ["a", "an", "the"]
        repositions = ["in", "on", "at", "by", "with", "from", "to"]
        verbs = [("is", "are"), 
                 ("was", "were"), 
                 ("has", "have"), 
                 ("do", "does")]
        
        if word in articles:
            return random.choice(articles)
        elif word in repositions:
            return random.choice(repositions)
        else:
            for v1, v2 in verbs:
                if word == v1:
                    return v2
                elif word == v2:
                    return v1
        
        return word
        
            
        
    def un_refine(self, content:str) -> str:
        """
        Introduces spelling and grammar errors into the content, making it feel less AI-generated.

        Parameters
        ----------
        content : str
            The content to un-refine.
            
        Returns
        -------
        str
            The un-refined content.
        """
        
        SPELLING_ERROR_CHANCE = 0.01
        CASE_ERROR_CHANCE = 0.1
        PUNCTUATION_ERROR_CHANCE = 0.02
        VARIED_PUNCTUATION_CHANCE = 0.05
        GRAMMAR_ERROR_CHANCE = 0.01
        

        # Split the content into words
        paragraphs = content.split("\n")
        new_paragraphs = []
        for paragraph in paragraphs:
            words = paragraph.split(" ")
            new_words = []
            for word in words:
                if len(word) == 0:
                    new_words.append(word)
                    continue
                # Apply spelling errors
                if random.random() < SPELLING_ERROR_CHANCE:
                    word = self.apply_spelling_error(word)
                # Apply case errors
                if random.random() < CASE_ERROR_CHANCE:
                    word = self.apply_case_error(word)
                # Apply punctuation errors
                if random.random() < PUNCTUATION_ERROR_CHANCE:
                    word = self.apply_punctuation_error(word)
                elif random.random() < VARIED_PUNCTUATION_CHANCE:
                    word = self.vary_punctuation(word)
                # Apply grammar errors
                if random.random() < GRAMMAR_ERROR_CHANCE:
                    word = self.apply_grammar_error(word)
                new_words.append(word)
            new_paragraphs.append(" ".join(new_words))
        return "\n".join(new_paragraphs)
        
    
    def refine(self, conversation: Conversation, response: Message) -> Message:
        """
        Refine the response generated by the generator.

        Parameters
        ----------
        conversation : Conversation
            The conversation object containing the context of the conversation.
        response : Message
            The response generated by the generator.

        Returns
        -------
        Message
            The refined response.
        """
        
        content:str = response.content
        
    

        # Build a regex pattern to match any of the keys as whole words (case-insensitive).
        pattern = re.compile(r'\b(' + '|'.join(map(re.escape, AikoRefiner.replacements.keys())) + r')\b', re.IGNORECASE)

        # --- Compute the Replacement Budget & Spacing ---

        # Calculate the total number of words in the content.
        total_words = len(content.split())

        # Set a replacement limit based on a fraction of the word count.
        # Here we use 5% of the total words, with a minimum of one replacement.
        allowed_replacements = max(1, int(total_words * 0.1))

        # Determine a minimum spacing (in characters) between replacements.
        # This ensures that the selected replacements are spread roughly evenly.
        min_spacing = int(len(content) / allowed_replacements * 0.9)

        # --- Select Which Matches to Replace ---

        # Use re.finditer to collect all matches (they are returned in order).
        selected_positions = set()
        last_replaced_pos = -min_spacing  # Initialize so the first match qualifies.
        replacements_used = 0

        for match in pattern.finditer(content):
            if replacements_used < allowed_replacements:
                # Only select this match if it’s at least min_spacing characters from the previous replacement.
                if match.start() - last_replaced_pos >= min_spacing:
                    selected_positions.add(match.start())
                    last_replaced_pos = match.start()
                    replacements_used += 1

        # Apply the substitutions to create a new, fox-like version of the text.
        new_content = pattern.sub(lambda x: self.replacement_func(x, selected_positions), content)
        
        # Apply un-refinement to the content
        new_content = self.un_refine(new_content)
        
        # Return the refined response
        return Message(new_content, response.user, response.timestamp)
            