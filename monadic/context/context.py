from .ancestry import AncestryTree
from .window import DynamicWindow



class Context:
    def __init__(
            self,
            uid,
            data,
            history
    ):
        self.uid = uid
        self.data = data
        self.history = history

        self.window = DynamicWindow(self.uid, self.history, 3)
        self.ancestry = AncestryTree(self.uid, self.data, self.history, 3)

    
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


    # data

    @property
    def data(self):
        return self.__data
    
    @data.setter
    def data(self, data):
        if not data:
            raise ValueError("'data' cannot be empty or None")
        if not isinstance(data, str):
            raise TypeError(f"Expected a 'str' for 'data', got '{type(data).__name__}'")
        self.__data = data


    # history

    @property
    def history(self):
        return self.__history
    
    @history.setter
    def history(self, history):
        if history is None:
            raise ValueError("'history' cannont be None")
        if not isinstance(history, list):
            raise TypeError(f"Expected a 'list' for 'history', got '{type(history).__name__}'")
        self.__history = history


    # window

    @property
    def window(self):
        return self.__window
    
    @window.setter
    def window(self, window):
        if window is None:
            raise ValueError("'window' cannot be None")
        if not isinstance(window, DynamicWindow):
            raise TypeError(f"Expected a 'DynamicWindow' instance for 'window', got '{type(window).__name__}'")
        self.__window = window


    # ancestry

    @property
    def ancestry(self):
        return self.__ancestry
    
    @ancestry.setter
    def ancestry(self, ancestry):
        if ancestry is None:
            raise ValueError("'ancestry' cannot be None")
        if not isinstance(ancestry, AncestryTree):
            raise TypeError(f"Expected an 'Ancestry' instance for 'ancestry', got '{type(ancestry).__name__}'")
        self.__ancestry = ancestry


    # context

    @property
    def context(self):
        return self.__context
    
    @context.setter
    def context(self, context):
        if context is None:
            raise ValueError("'context' cannot be None")
        if not isinstance(context, list):
            raise TypeError(f"Expected a 'list' for 'context', got '{type(list).__name__}'")
        self.__context = context