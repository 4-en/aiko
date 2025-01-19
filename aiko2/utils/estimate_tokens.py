# estimate amount of tokens in a string
# accuracy will wary depending on the exact tokenizer used

import re

def estimate_tokens(
        text: str, 
        characters_per_token: float = 4.0, 
        words_per_token: float = 2,
        special_characters_per_token: float = 1.0,
        ) -> int:
    """
    Estimate the number of tokens in a string.
    Estimation:
        tokens = characters / 4 + words / 2

    Parameters
    ----------
    text : str
        The text to estimate the number of tokens in.

    Returns
    -------
    int
        The estimated number of tokens in the text.
    """
    # count characters
    characters = len(text)
    # count words
    word_count = len(re.findall(r'\b\w+\b', text))  # Count words
    # count special characters
    special_char_count = len(re.findall(r'[\W_]', text))  # Count non-alphanumeric characters

    # estimate tokens
    tokens = characters / characters_per_token + word_count / words_per_token + special_char_count / special_characters_per_token

    return int(tokens)

if __name__ == "__main__":
    examples = [
        "Hello, how are you?",
        "This is a test!",
        "1 + 1 = 2",
        "Visit https://example.com",
        "Python is 💖"
    ]

    for example in examples:
        print(f"Example: {example}")
        print(f"Estimated tokens: {estimate_tokens(example)}")
        print()

    
