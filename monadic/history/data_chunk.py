from __future__ import annotations

from monadic import interactions



class Chunk:
    
    def __init__(self,
                 role:    str,
                 content: str,
                 index:   int=-1) -> None:
        self.__id:      int         = index
        self.__role:    str         = role
        self.__content: str         = content
        self.__embed:   list[float] = interactions.embeddings(content).data[0].embedding
        self.__context: list[Chunk] = []
    

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
        return self.__embed


    def get_context(self) -> list[Chunk]:
        return self.__context


   # Setters

    def set_id(self, index) -> None:
        self.__id = index


    def set_context(self, context) -> None:
        self.__context = context

