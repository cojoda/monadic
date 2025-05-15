import itertools
import logging

from monadic import config
from monadic.history import data_chunk 

from . import ancestry_tree, window



logger = logging.getLogger(__name__)



class Context:

    def __init__(self,
                 chunk:   data_chunk.Chunk       | None,
                 history: list[data_chunk.Chunk] | None) -> None:
        
        self.__id:       int                    | None = None
        self.__window:   window.DynamicWindow   | None = None
        self.__ancestry: ancestry_tree.Ancestry | None = None
        if chunk is None: return
        if history is None: history = []

        self.__id       = chunk.get_id()
        self.__window   = window.DynamicWindow(history, self.__id, config.TOP_N)
        self.__ancestry = ancestry_tree.Ancestry(chunk, history)
        self.__log_init()
        


    # return list of chunks in context
    def get_context(self) -> list:
        if self.__ancestry is not None:
            ancestry = self.__ancestry.get_ancestry()
        else: ancestry = []
        if self.__window is not None:
            window = self.__window.get_window()
        else: window = []
        if self.__id is not None and self.__window is not None:
            start = max(self.__id - self.__window.get_size(), 0)
        else: start = 0
        context = []
        roles = itertools.cycle(['assistant', 'user'])
        window = window[start:self.__id]
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



    def get_form(self) -> list[str]:
        return [f'{chunk}' for chunk in self.get_context()]


    def __log_init(self):
        logger.info(f'{config.CON}\nid: {self.__id}{config.CLR}')