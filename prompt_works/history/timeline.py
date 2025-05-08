from .chunk import Chunk
from ..context import window


class Timeline:
    
    def __init__(self) -> None:
        self.__chunks: list[Chunk] = []
        self.window = window.SlidingWindow(5)


    def add_record(self, role, content) -> None:
        chunk = Chunk(len(self.__chunks), role, content)
        self.window.add(chunk)
        self.__chunks.append(chunk)


    def get_record(self) -> list[dict[str,str]]:
        return self.window.get_window()

    
    def get_last_record(self) -> Chunk:
        return self.__chunks[-1]