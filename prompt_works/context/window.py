from collections import deque



class SlidingWindow:

    def __init__(self, size, history=None) -> None:
        if history != None:
            window = history[-1*(len(history)):]
            self.__window = deque(window, maxlen=size)
        else:
            self.__window = deque(maxlen=size)


    # Add to

    def add(self, chunk) -> None:
        self.__window.append(chunk)


    def extend(self, chunks) -> None:
        self.__window.extend(chunks)


    # Overloads

    def __len__(self) -> int:
         return len(self.__window)
    

    # Getters

    def get_size(self) -> int | None:
        return self.__window.maxlen
    

    # return list of chunks in window
    def get_window(self) -> list[dict[str,str]]:
        return list(self.__window)
    


# class StaticWindow(Context):

#     def __init__(self, size) -> None:
#         self.__size = size
#         self.__panes = []


#     def __len__(self) -> int:
#         return len(self.__panes)


#     def add(self, pane) -> None:
#         if (len(self.__panes)) < self.__size:
#             self.__panes.append(pane)


#     def get_context(self) -> list[Chunk]:
#         return self.__panes.copy()
    

#     def get_size(self) -> int:
#         return self.__size
