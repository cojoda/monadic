from ..history.chunk import Chunk


class Context:

    def get_context(self) -> list[Chunk]:
        raise NotImplementedError("Subclasses should implement this method")