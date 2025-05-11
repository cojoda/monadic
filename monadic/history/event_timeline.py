from . import data_chunk
from . import chunk_ops

from monadic.context import context_manager



class Timeline:
    
    def __init__(self) -> None:
        self.__history: list[data_chunk.Chunk] = []
        self.__index = 0
        self.__last = None


    def add_history(self,
                    role,
                    content) -> None:
        
        self.__last = data_chunk.Chunk(role, content, len(self.__history))
        last_context = context_manager.Context(self.__last, self.__history)
        self.__last.set_context(last_context)

        self.__index = len(self.__history)
        chunk_content_list = chunk_ops.chunker(content)
        for chunk_content in chunk_content_list:
            index = len(self.__history)
            chunk = data_chunk.Chunk(role, chunk_content, index)
            context = context_manager.Context(chunk, self.get_rest())
            chunk.set_context(context)
            self.__history.append(chunk)


    # Returns committed chunks
    def get_last(self) -> list[data_chunk.Chunk]:
        return self.__history[self.__index:]
    

    # Returns pending chunks
    def get_rest(self) -> list[data_chunk.Chunk]:
        return self.__history[:self.__index]

    
    def get_history(self):
        if len(self.__history) == 0: return repr([])
        # # last = self.__history[-1]
        # last = self.__history[self.__index:]
        # merged = chunk_ops.merge(last)
        if self.__last is None: return [{}]
        context = self.__last.get_context()
        role = self.__last.get_role()
        if len(context) == 0:
            # no context, return just query JSON
            return [self.__last.get_form()]
        else: 
            # return context + query JSON
            return ([chunk.get_form() for chunk in context] + [self.__last.get_form()])
    