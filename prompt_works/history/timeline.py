from .chunk import Chunk
from .chunker import Chunker
from ..context import window


class Timeline:
    
    def __init__(self) -> None:
        self.__chunks: list[Chunk] = []
        self.__window = window.SlidingWindow(5)
        self.__chunker = Chunker()


    def add_record(self, role, content) -> None:
        chunks = self.__chunker.get_chunks(len(self.__chunks), role, content)
        self.__window.extend(chunks)
        self.__chunks.extend(chunks)


    def get_records(self) -> list[dict[str,str]]:
        print(f'sent records: {self.__window.get_window()}')
        return self.__window.get_window()
