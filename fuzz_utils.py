def uniform_random_word() -> str:
    """
    Returns (truly) a random English word.
    """
    from persistent import load
    from random import choice
    word_file = __file__[:-len(__name__) - 3] + "Text Data\Words.pyt"
    words = load(word_file)
    return choice(words)


def random_word() -> str:
    """
    Returns a random word with natural appearance frequencies.
    """
    from persistent import load
    from random import choice
    sentence_file = __file__[:-len(__name__) - 3] + "Text Data\Sentences.pyt"
    sentences = load(sentence_file)
    import re
    word_re = re.compile(r"[A-Za-z0-9-']+")
    return choice(word_re.findall(choice(sentences)))


def random_sentence() -> str:
    """
    Returns a random english sentence.
    """
    from persistent import load
    from random import choice
    sentence_file = __file__[:-len(__name__) - 3] + "Text Data\Sentences.pyt"
    sentences = load(sentence_file)
    return choice(sentences)

