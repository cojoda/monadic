from .ancestry_tree import Ancestry
from .window import DynamicWindow



class Context:
    def __init__(self):
        self.uid = None
        self.data = None
        self.history = None

        self.window = None
        self.window_size = None
        
        self.ancestry = None
        self.ancestry_depth = None

    
    # uid

    @property
    def uid(self):
        return self.__uid
    
    @uid.setter
    def uid(self, uid):
        if uid is None:
            raise ValueError('uid cannot be None')
        self.__uid = uid


    # data

    @property
    def data(self):
        return self.__data
    
    @data.setter
    def data(self, data):
        if data is None:
            raise ValueError('data cannont be None')
        self.__data = data


    # history

    @property
    def history(self):
        return self.__history
    
    @history.setter
    def history(self, history):
        if history is None:
            raise ValueError('history cannont be None')
        self.__history = history


    # window

    @property
    def window(self):
        return self.__window
    
    @window.setter
    def window(self):
        if self.data is None:
            raise ValueError('data cannot be None in window')
        self.__window = DynamicWindow(self.history, self.uid, 3)


    # ancestry

    @property
    def ancestry(self):
        return self.__ancestry
    
    @ancestry.setter
    def ancestry(self):
        if self.data is None:
            raise ValueError('data cannot be None in ancestry')
        self.__ancestry = Ancestry(self.data, self.history)