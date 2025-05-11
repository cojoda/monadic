from __future__ import annotations

from monadic import interactions



class Chunk:
    
    def __init__(self,
                 role,
                 content,
                 index  =-1):
        self.__index   = index
        self.__role    = role
        self.__content = content
        self.__embed   = interactions.embeddings(content).data[0].embedding
        self.__context: list[Chunk] = []
    

    # Getters

    def get_index(self):
        return self.__index


    def get_role(self):
        return self.__role


    def get_content(self):
        return self.__content


    def get_embed(self):
        return self.__embed


    def get_context(self) -> list[Chunk]:
        return self.__context


   # Setters

    def set_index(self, index):
        self.__index = index


    def set_context(self, context):
        self.__context = context


    def get_form(self):
        return {'role': self.__role, 'content': self.__content}
