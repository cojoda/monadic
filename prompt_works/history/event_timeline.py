import re

from . import data_chunk
from prompt_works.context import context_manager



class Timeline:
    
    def __init__(self) -> None:
        self.__history = []


    def add_history(self,
                    role,
                    content) -> None:
        chunk_content_list = self.__chunker(content)
        for chunk_content in chunk_content_list:
            index = len(self.__history)
            chunk = data_chunk.Chunk(role, chunk_content, index)
            context = context_manager.Context(chunk, self.__history)
            chunk.set_context(context)
            self.__history.append(chunk)

    
    def get_history(self):
        if len(self.__history) == 0: return repr([])
        last = self.__history[-1]
        context = last.get_context()
        if len(context) == 0:
            return [last.get_form()]
        else: 
            return ([chunk.get_form() for chunk in context] + [last.get_form()])


    def __chunker(self, text):
        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        paragraphs = re.split(r'\n\s*\n', normalized.strip())
        return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]