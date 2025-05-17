from __future__ import annotations

import logging

from monadic import config
from monadic import interactions



logger = logging.getLogger(__name__)



class Chunk:
    
    def __init__(self,
                 role,
                 data,
                 id   =-1,
                 embed=None):
        self.role = role
        self.data = data
        self.id   = id
        
        self.embed   = embed
        self.context = []
        if embed is None:
            self.embed = interactions.embeddings([data]).data[0].embedding
        self.__log_init()



    # role

    @property
    def role(self):
        return self.__role

    @role.setter
    def role(self, role: str):
        if not role:
            raise ValueError('role expects str')
        self.__role = role
    


    # id

    @property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self, id):
        if not id:
            raise ValueError('id expects int')
        self.__id = id



    # data

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, data):
        if not data:
            raise ValueError('data expects data')
        self.__data = data



    # embedding

    @property
    def embedding(self):
        return self.__embed
    
    @embedding.setter
    def embedding(self, embedding):
        if not embedding:
            raise ValueError('embedding expects embedding')
        self.__embed = embedding



    # context

    @property
    def context(self):
        return self.__context
    
    @context.setter
    def context(self, context):
        if not context:
            raise ValueError('context expects context')
        self.__context = context


    # logger

    def __log_init(self):
        logger.info(f'{config.HIS}\nid: {self.id}\ncontent: {self.data}{config.CLR}')


    def get_form(self):
        return {'role': self.role, 'content': self.data}