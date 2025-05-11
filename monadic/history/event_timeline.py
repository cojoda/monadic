from . import data_chunk
from . import chunk_ops

from monadic.context import context_manager



class Timeline:
    
    def __init__(self) -> None:
        self.__history: list[data_chunk.Chunk]  = []
        self.__last:    data_chunk.Chunk | None = None
        self.__id:   int                     = 0



    def add_history(self,
                    role,
                    content) -> None:
        
        # Prevents query from contexting itself during the query
        self.__last = data_chunk.Chunk(role, content, len(self.__history))
        last_context = context_manager.Context(self.__last, self.__history)
        self.__last.set_context(last_context)

        # But allow it to context itself after
        self.__id = len(self.__history)
        chunk_content_list = chunk_ops.chunker(content)
        for chunk_content in chunk_content_list:
            chunk = data_chunk.Chunk(role, chunk_content, len(self.__history))
            context = context_manager.Context(chunk, self.get_rest())
            chunk.set_context(context)
            self.__history.append(chunk)



    # Fetches and returns context history of __last
    def get_history(self) -> list:
        if len(self.__history) == 0 or self.__last is None: return []

        context = self.__last.get_context()
        if len(context) == 0:
            # no context, return just query JSON
            return [self.__last.get_form()]
        else: 
            # return context + query JSON
            return ([chunk.get_form() for chunk in context] + [self.__last.get_form()])



    # Returns committed chunks
    def get_last(self) -> list[data_chunk.Chunk]:
        return self.__history[self.__id:]
    


    # Returns pending chunks
    def get_rest(self) -> list[data_chunk.Chunk]:
        return self.__history[:self.__id]
    