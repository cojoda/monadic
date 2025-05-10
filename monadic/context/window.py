# from collections import deque



class DynamicWindow:

    def __init__(self, history, index, size) -> None:
        self.__window = history
        self.__index = index
        self.__size = size


    # Overloads

    def __len__(self) -> int:
         if self.__window == None: return 0
         return len(self.__window)
    

    # Getters

    def get_size(self) -> int:
        return self.__size
    

    # return list of chunks in window
    def get_window(self) -> list[dict[str,str]]:
        return self.__window
    