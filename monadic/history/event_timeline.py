from . import data_chunk

from monadic.context import context_manager



class Timeline:
    
    def __init__(self) -> None:
        self.__history: list[data_chunk.Chunk] = []
        self.__index = 0


    def add_history(self,
                    role,
                    content) -> None:
        self.__index = len(self.__history)
        chunk_content_list = data_chunk.chunker(content)
        for chunk_content in chunk_content_list:
            index = len(self.__history)
            chunk = data_chunk.Chunk(role, chunk_content, index)
            context = context_manager.Context(chunk, self.__history)
            chunk.set_context(context)
            self.__history.append(chunk)


    # Returns committed chunks
    def get_last(self) -> list[data_chunk.Chunk]:
        return self.__history[self.__index:]
    

    # Returns pending chunks
    def get_rest(self) -> list[data_chunk.Chunk]:
        return self.__history[:self.__history]

    
    def get_history(self):
        if len(self.__history) == 0: return repr([])
        last = self.__history[-1]
        context = last.get_context()
        if len(context) == 0:
            return [last.get_form()]
        else: 
            return ([chunk.get_form() for chunk in context] + [last.get_form()])
    