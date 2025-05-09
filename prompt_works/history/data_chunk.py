from prompt_works import interactions



class Chunk:
    
    def __init__(self,
                 role,
                 content,
                 index  =-1):
        self.__index   = index
        self.__role    = role
        self.__content = content
        self.__embed   = interactions.embeddings(content).data[0].embedding
        self.__context = None
    

    # Getters

    def get_index(self):
        return self.__index


    def get_role(self):
        return self.__role


    def get_content(self):
        return self.__content


    def get_embed(self):
        return self.__embed


    def get_context(self):
        return self.__context


   # Setters

    def set_index(self, index):
        self.__index = index


    def set_context(self, context):
        self.__context = context


    def get_form(self):
        return {'role': self.__role, 'content': self.__content}


    def __lt__(self, other):
        # other is the object on the right side of the < operator
        if isinstance(other, Chunk):
            # Implement your custom comparison logic here
            return self.get_index() < other.get_index()
        # If 'other' is not of the same type or a type you can compare with,
        # it's good practice to return NotImplemented.
        # This allows Python to try other comparison mechanisms,
        # like calling __gt__ on the 'other' object if defined.
        return NotImplemented
