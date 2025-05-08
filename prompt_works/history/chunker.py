import re

from .chunk import Chunk


class Chunker:
    def split(self, text):
        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        paragraphs = re.split(r'\n\s*\n', normalized.strip())
        return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
    
    def get_chunks(self, start_index, role, content):
        paragraphs = self.split(content)
        chunks = []
        for paragraph in paragraphs:
            chunks.append(Chunk(start_index, role, paragraph))
            start_index+=1
        return chunks