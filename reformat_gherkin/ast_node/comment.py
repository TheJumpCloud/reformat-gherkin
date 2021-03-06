from attr import attrib

from ._base import prepare
from .location import Location


def normalize_comment_text(text: str) -> str:
    """
    Return a consistently formatted comment from the given Comment instance.
    All comments should have a single space between the hash sign and the content.
    """
    # A comment always start with a hash sign
    normalized_text = text[1:].strip()

    return "# " + normalized_text


@prepare
class Comment:
    location: Location = attrib(cmp=False, repr=False)
    text: str = attrib(converter=normalize_comment_text)
