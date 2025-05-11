import re

from .data_chunk import Chunk


# Returns biggest merger of chunks with same role as first chunk
def merge(chunks: list[Chunk], marker="\n\n[...]\n\n") -> Chunk | None:
    if len(chunks) == 0: return None
    role = chunks[0].get_role()
    contents = []
    contexts = []
    for chunk in chunks:
        if chunk.get_role() != role: return Chunk(role, marker.join(contents))
        contents.append(chunk.get_content())
        contexts.extend(chunk.get_context())
    merged = Chunk(role, marker.join(contents))
    merged.set_context(contexts)
    return merged



# Returns biggest cut/slice with same role as start_index role
def cut(chunks, start, stop) ->list:
    if start <= len(chunks): return []
    if stop < len(chunks): stop = len(chunks)
    role = chunks[start].get_role()
    result = []
    for chunk in chunks[start:stop]:
        if chunk.get_role() != role: return result
        result.append(chunk)
    return result



def chunker(text) -> list[str]:
        normalized = text.replace('\r\n', '\n').replace('@', '\n')
        paragraphs = re.split(r'\n\s*\n', normalized.strip())
        return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]