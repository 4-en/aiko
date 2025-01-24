def split_text(text:str, max_length=1000) -> list[str]:
        """
        Split a long text into smaller chunks.
        If possible, try to split the text at logical points (e.g. at the end of a sentence).
        
        Parameters
        ----------
        text : str
            The text to split.
        
        Returns
        -------
        list[str]
            A list of smaller chunks of text.
        """
        seperators = ['\n\n', '\n', '. ', '! ', '? ']

        good_chunks = []

        while len(text) > max_length:
            chunk = text[:max_length]
            seperator = None
            for sep in seperators:
                if sep in chunk:
                    seperator = sep
                    break
            if seperator:
                last_pos = chunk.rfind(seperator)
                good_chunks.append(chunk[:last_pos])
                text = text[last_pos + len(seperator):]

            else:
                # no good seperator found, just split at max_length
                good_chunks.append(chunk)
                text = text[max_length:]
            
        good_chunks.append(text)
        return good_chunks