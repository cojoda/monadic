import logging

from monadic.data.chunk import Chunk



logger = logging.getLogger(__name__)



class Timeline:
    def __init__(self):
        self.history = []


    # history

    @property
    def history(self):
        return self.__history
    
    @history.setter
    def history(self, history):
        if history is None:
            raise ValueError("'history' cannot be None")
        if not isinstance(history, list):
            raise TypeError(f"Expected a 'list' for 'history', got '{type(history).__name__}'")
        self.__history = history



    def append(self, chunk):
        if chunk is None: return
        if not isinstance(chunk, Chunk):
            raise TypeError(f"Expected a 'Chunk' instance for 'chunk', got '{type(chunk).__name__}'")
        self.history.append(chunk)



    def extend(self, chunks):
        if chunks is None: return
        if not isinstance(chunks, list):
            raise TypeError(f"Expected a 'list' for 'chunks', got '{type(chunks).__name__}'")
        self.history.extend(chunks)


    def __iter__(self):
        return iter(self.history)
    

    def __len__(self):
        return len(self.history)
    