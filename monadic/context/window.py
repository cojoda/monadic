


class DynamicWindow:
    def __init__(
            self,
            uid,
            history,
            size
    ):
        self.uid = uid
        self.history = history
        self.size = size
        self.window = []


    # uid

    @property
    def uid(self):
        return self.__uid
    
    @uid.setter
    def uid(self, uid):
        if uid is None:
            raise ValueError("'uid' cannot be None")
        if not isinstance(uid, int):
            raise TypeError(f"Expected an 'int' for 'uid', got '{type(uid).__name__}'")
        self.__uid = uid


    # history

    @property
    def history(self):
        return self.__history
    
    @history.setter
    def history(self, history):
        if history is None:
            raise ValueError("'history' cannot be None")
        if not isinstance(history, list):
            raise ValueError(f"Expected a 'list' for 'history', got '{type(history).__name__}'")
        self.__history = history


    # size

    @property
    def size(self):
        return self.__size
    
    @size.setter
    def size(self, size):
        if size is None:
            raise ValueError("'size' cannot be None")
        if not isinstance(size, int):
            raise TypeError(f"Expected an 'int' for 'size', got '{type(size).__name__}'")
        self.__size = size


    # window

    @property
    def window(self):
        return self.__window
    
    @window.setter
    def window(self, window):
        if window is None:
            raise ValueError("'window' cannot be None")
        if not isinstance(window, list):
            raise TypeError(f"Expected a 'list' for 'window', got '{type(window).__name__}'")
        self.__window = window
