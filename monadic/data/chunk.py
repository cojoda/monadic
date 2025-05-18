import logging



logger = logging.getLogger(__name__)



class Chunk:

    def __init__(
            self,
            role,
            data,
            uid,
            context
    ):
        self.role = role
        self.data = data
        self.uid = uid
        self.context = context


    # role

    @property
    def role(self):
        return self.__role
    
    @role.setter
    def role(self, role):
        if not role:
            raise ValueError('role cannot be empty or None')
        if not isinstance(role, str):
            raise TypeError(f"Expected a string for 'role', got {type(role).__name__}")
        self.__role = role


    # data

    @property
    def data(self):
        return self.__data
    
    @data.setter
    def data(self, data):
        if not data:
            raise ValueError('data cannot be empty or None')
        if not isinstance(data, str):
            raise TypeError(f"Expected a string for 'data', got {type(data).__name__}")
        self.__data = data

    
    # uid

    @property
    def uid(self):
        return self.__uid
    
    @uid.setter
    def uid(self, uid):
        if uid is None:
            raise ValueError("'id' cannot be None")
        if not isinstance(uid, int):
            raise TypeError(f"Expected an int for 'uid', got {type(uid).__name__}")
        self.__uid = uid

    
    # context

    @property
    def context(self):
        return self.__context
    
    @context.setter
    def context(self, context):
        # if not context:
        #     raise ValueError('context cannot be empty or None')
        # if not isinstance(context, Context):
        #     raise TypeError(f"Expected a Context instance for 'context', got {type(context).__name__}")
        self.__context = context


    
    def to_dict(self):
        return {
            'role': self.role,
            'content': self.data
        }
    

    # def __log_init(self):
    #     logger.info(f'{config.HIS}\nid: {self.id}\ncontent: {self.data}{config.CLR}')