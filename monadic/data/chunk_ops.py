import re

from .data_chunk import Chunk


# Returns biggest merger of chunks with same role as first chunk
def merge(chunks: list[Chunk] | None,
          marker: str         | None='\n\n[...]\n\n') -> Chunk | None:
    
    if chunks is None or len(chunks) == 0: return None
    if marker is None: marker = ''

    role = chunks[0].role
    contents = []
    contexts = []
    for chunk in chunks:
        if chunk.role != role: return Chunk(role, marker.join(contents))
        contents.append(chunk.context)
        contexts.extend(chunk.context)
    merged = Chunk(role, marker.join(contents))
    merged.context = contexts
    return merged



# Returns biggest cut/slice with same role as start_index role
def cut(chunks: list[Chunk] | None,
        start:  int         | None,
        stop:   int         | None) ->list:
    
    if chunks is None or start is None or stop is None: return [] 
    
    if start <= len(chunks): return []
    if stop < len(chunks): stop = len(chunks)
    role = chunks[start].role
    result = []
    for chunk in chunks[start:stop]:
        if chunk.role != role: return result
        result.append(chunk)
    return result



def chunker(text: str | None) -> list[str]:
    if text is None: return []
    # normalized = '\n'.join(text.splitlines())
    text = text.replace('\\#', '\n\n')
    paragraphs = re.split(r'\n\s*\n', text.strip())
    return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]