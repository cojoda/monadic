import re

from .chunk import Chunk




def chunker(text: str | None) -> list[str]:
    if text is None: return []
    text = text.replace('\\#', '\n\n')
    paragraphs = re.split(r'\n\s*\n', text.strip())
    return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]