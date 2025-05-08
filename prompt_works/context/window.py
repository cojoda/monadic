from collections import deque

from .context import Context
from ..history.chunk import Chunk



class SlidingWindow(Context):

    def __init__(self, size) -> None:
        self.__chunks = deque(maxlen=size)


    def __len__(self) -> int:
         return len(self.__chunks)
    

    def add(self, pane) -> None:
        self.__chunks.append(pane)


    def get_context(self) -> list[Chunk]:
        return list(self.__chunks)
    

    def get_size(self) -> int | None:
        return self.__chunks.maxlen
    

    def get_window(self) -> list[dict[str,str]]:
        return [chunk.get_chunk() for chunk in list(self.__chunks)]
    

    def __repr__(self) -> str:
        return repr([f'{chunk}' for chunk in self.get_context()])
    


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
