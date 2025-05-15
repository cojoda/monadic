import logging

from . import timeline_plot

from monadic import config
from monadic import interactions
from monadic.context import context_manager
from monadic.data import data_chunk
from monadic.data import chunk_ops



logger = logging.getLogger(__name__)



class Timeline:
    
    def __init__(self) -> None:
        self.__id:       int                     = 0
        self.__history:  list[data_chunk.Chunk]  = []
        self.__outgoing: data_chunk.Chunk | None = None
        self.__incoming: data_chunk.Chunk | None = None
        self.__plot_counter = 0
        self.__plot_dir = config.EvalEmbed.plot_dir



    def add_outgoing(self,
                     role:    str | None,
                     content: str | None) -> None:
        if role is None: role = ''
        if content is None: content = ''
        # Hack to allow newlines from terminal
        content = content.replace('\\#', '\n\n')
        # Get outgoing context before chunking to prevent it from contexting itself
        self.__outgoing = data_chunk.Chunk(role, content.replace('\\#', ' '), len(self.__history))
        context = context_manager.Context(self.__outgoing, self.__history)
        self.__outgoing.set_context(context)
        self.visualize()
        self.add_history(role, content)



    def add_incoming(self,
                     role:    str | None,
                     content: str | None) -> None:
        if role is None: role = ''
        if content is None: content = ''

        self.add_history(role, content)



    def add_history(self,
                    role:    str | None,
                    content: str | None) -> None:
        if role is None: role = ''
        if content is None: content = ''

        chunked_contents = chunk_ops.chunker(content)

        chunked_embeds_response = interactions.embeddings(chunked_contents)
        chunked_embeds = [chunk.embedding for chunk in chunked_embeds_response.data]

        for chunk_content, chunk_embed in zip(chunked_contents, chunked_embeds):
            self.__id = len(self.__history)
            chunk = data_chunk.Chunk(role, chunk_content, len(self.__history),chunk_embed)
            context = context_manager.Context(chunk, self.get_residing())
            chunk.set_context(context)
            self.__history.append(chunk)
        # self.visualize()



    # Fetches and returns context history of __last
    def get_form(self) -> list:
        if len(self.__history) == 0 or self.__outgoing is None: return []

        context = self.__outgoing.get_context()
        if len(context) == 0:
            return [self.__outgoing.get_form()]
        return ([chunk.get_form() for chunk in context] + [self.__outgoing.get_form()])
    


    # Returns pending chunks
    def get_residing(self) -> list[data_chunk.Chunk]:
        return self.__history[:self.__id]



    def visualize(self) -> None:
        self.__plot_counter = timeline_plot.plot(
            self.__history,
            self.__outgoing,
            self.__plot_counter,
            title_prefix=config.EvalEmbed.plot_file_prefix,
            plot_dir    =self.__plot_dir
        )
