import logging



logger = logging.getLogger(__name__)





        


    # # return list of chunks in context
    # def get_context(self):
    #     if self.__ancestry is not None:
    #         ancestry = self.__ancestry.get_ancestry()
    #     else: ancestry = []
    #     if self.__window is not None:
    #         window = self.__window.get_window()
    #     else: window = []
    #     if self.__id is not None and self.__window is not None:
    #         start = max(self.__id - self.__window.get_size(), 0)
    #     else: start = 0
    #     context = []
    #     roles = itertools.cycle(['assistant', 'user'])
    #     window = window[start:self.__id]
    #     for chunk in ancestry:
    #         if chunk not in context and chunk not in window:
    #             context.append(chunk)
    #     for chunk in window:
    #         if chunk not in context:
    #             context.append(chunk)
    #     return context





    # def get_form(self) -> list[str]:
    #     return [f'{chunk}' for chunk in self.get_context()]


    # def __log_init(self):
    #     logger.info(f'{config.CON}\nid: {self.__id}{config.CLR}')