# from collections import deque



class DynamicWindow:

    def __init__(self, history,
                 id:   int | None,
                 size: int | None) -> None:
        if history is None:
            self.__window = []
            self.__size   = 0

        self.__window = history
        self.__id     = id
        self.__size   = size



    # Overloads

    def __len__(self) -> int:
         if self.__window == None: return 0
         return len(self.__window)
    


    # Getters

    def get_size(self) -> int:
        if self.__size is None: return 0;
        return self.__size
    


    # return list of chunks in window
    def get_window(self) -> list[dict[str,str]]:
        if self.__window is None: return []
        return self.__window
    