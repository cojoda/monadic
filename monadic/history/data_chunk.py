from __future__ import annotations

import logging

from monadic import config
from monadic import interactions



logger = logging.getLogger(__name__)



class Chunk:
    
    def __init__(self,
                 role:    str,
                 content: str,
                 id:      int=-1,
                 embed:   list[float]|None=None) -> None:
        self.__id:      int         = id
        self.__role:    str         = role
        self.__content: str         = content
        
        self.__embed: list[float] | None = embed
        self.__context: list[Chunk] = []
        if embed is None:
            self.__embed = interactions.embeddings([content]).data[0].embedding
        self.__log_init()
    

    # Getters

    def get_form(self) -> dict[str,str]:
        return {'role': self.__role, 'content': self.__content}


    def get_id(self) -> int:
        return self.__id


    def get_role(self) -> str:
        return self.__role


    def get_content(self) -> str:
        return self.__content


    def get_embed(self) -> list[float]:
        if self.__embed is None: return []
        return self.__embed


    def get_context(self) -> list[Chunk]:
        return self.__context


   # Setters

    def set_id(self, index) -> None:
        self.__id = index


    def set_context(self, context) -> None:
        self.__context = context


    def __log_init(self):
        logger.info(f'{config.HIS}\nid: {self.__id}\ncontent: {self.__content}{config.CLR}')