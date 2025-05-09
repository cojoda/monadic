import re

def colorize_text_in_terminal(text_string: str, words_to_colorize: list[str]):
    """
    Prints a string of text to the terminal, colorizing specified words.

    Args:
        text_string: The input string to print and colorize.
        words_to_colorize: A list of words that should be colorized in the text.
                           The matching is case-sensitive and whole-word only.
    """
    RED = '\033[91m'  # ANSI escape code for red text
    RESET = '\033[0m' # ANSI escape code to reset color

    if not words_to_colorize:
        print(text_string)
        return

    # Escape any special regex characters in the words to be colorized
    # and ensure they are treated as literal strings.
    # We sort by length descending to prefer matching longer words first
    # if there's any ambiguity (e.g., "cat" and "catalog"), though \b usually handles this.
    # For example, if "cat" and "catalog" are both in words_to_colorize,
    # and text is "catalog", we want to match "catalog", not "cat".
    # `\b` handles this well, but sorting is a good practice for complex patterns.
    sorted_words = sorted(words_to_colorize, key=len, reverse=True)
    escaped_words = [re.escape(word) for word in sorted_words]

    # Create a regex pattern that matches any of the words as whole words.
    # \b ensures that we match whole words (e.g., "cat" in "the cat sat"
    # but not in "catalog").
    pattern_string = r'\b(' + '|'.join(escaped_words) + r')\b'
    
    # Compile the regex pattern for efficiency if used multiple times,
    # though for a single call it's not strictly necessary.
    # The default regex compilation is case-sensitive.
    try:
        pattern = re.compile(pattern_string)
    except re.error as e:
        print(f'Error compiling regex pattern: {e}')
        print(f'Original text: {text_string}') # Print original if pattern fails
        return

    last_end = 0
    result_parts = []

    for match in pattern.finditer(text_string):
        start, end = match.span()
        # Add the part of the string before the match
        result_parts.append(text_string[last_end:start])
        # Add the colorized matched word
        result_parts.append(f'{RED}{match.group(0)}{RESET}')
        last_end = end
    
    # Add the remaining part of the string after the last match
    result_parts.append(text_string[last_end:])
    
    print(''.join(result_parts))