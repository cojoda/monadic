from typing import Any

from ..interactions import embeddings



Index = int | float | str
Content = str



class Chunk:
    def __init__(self,
                 index:   Index,
                 role:    str,
                 content: Content,
                 context=None
                 ) -> None:
        self.__index   = index
        self.__role    = role
        self.__content = content
        self.__embed   = embeddings(content).data[0].embedding
        self.__context = context


    def get_index(self) -> Index:
        return self.__index


    def get_role(self) -> str | None:
        return self.__role


    def get_content(self):
        return self.__content


    def get_embed(self):
        return self.__embed


    # TODO Instead of None change to -> list[Chunk]
    def get_context(self) -> list | None:
        # TODO: loop through context list and return chunks as list
        return None


    def get_chunk(self) -> dict[str,Any]:
        return {'role': self.__role,
                'content': self.__content}

    
    def __repr__(self) -> str:
        return (f"{{'role': '{self.__role}',"
                  f"'content': '{self.__content}'}}")