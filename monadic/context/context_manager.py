import itertools

from . import ancestry_tree, window
from monadic.history import data_chunk 



class Context:

    def __init__(self,
                 chunk: data_chunk.Chunk,
                 history) -> None:
        self.__index = chunk.get_index()
        self.__window = window.DynamicWindow(history, self.__index, 3)
        self.__ancestry = ancestry_tree.Ancestry(chunk, history)
        


    # return list of chunks in context
    def get_context(self) -> list:
        context = []
        roles = itertools.cycle(['assistant', 'user'])
        ancestry = self.__ancestry.get_ancestry()
        window = self.__window.get_window()
        start = max(self.__index - self.__window.get_size(), 0)
        window = window[start:self.__index]
        for chunk in ancestry:
            if chunk not in context and chunk not in window:
                context.append(chunk)
        for chunk in window:
            if chunk not in context:
                context.append(chunk)
        return context


    def __len__(self) -> int:
        return len(self.get_context())


    def __iter__(self):
        return iter(self.get_context())


    def get_form(self):
        return [f'{chunk}' for chunk in self.get_context()]
