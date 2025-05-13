import logging

from . import data_chunk
from . import chunk_ops

from monadic.context import context_manager
from monadic import interactions
from evaluation.visualization import embedding

from monadic import config



logger = logging.getLogger(__name__)



class Timeline:
    
    def __init__(self) -> None:
        self.__id:       int                     = 0
        self.__history:  list[data_chunk.Chunk]  = []
        self.__outgoing: data_chunk.Chunk | None = None
        self.__incoming: data_chunk.Chunk | None = None
        self.__plot_counter = 0



    def add_outgoing(self,
                     role:    str | None,
                     content: str | None) -> None:
        if role is None: role = ''
        if content is None: content = ''
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

        # self.__id = len(self.__history)
        for chunk_content, chunk_embed in zip(chunked_contents, chunked_embeds):
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



    def visualize(self):
        if not self.__history:
            logger.info(f'{config.HIS}Timeline: No history to visualize.{config.CLR}')
            return
        history = self.__history
        outgoing = self.__outgoing
        if outgoing:
            context_ids = [chunk.get_id() for chunk in outgoing.get_context()] + [outgoing.get_id()]
            history += [outgoing]
        else:
            context_ids = []
    
        embeddings_to_plot = []
        labels_to_plot = []

        for i, chunk in enumerate(history):
            embed = chunk.get_embed() # Assuming get_embed() returns the embedding vector
            if embed is not None and len(embed) > 0:
                spec = ''
                if i in context_ids:
                    spec = f'id:{i},{chunk.get_content()}'
                embeddings_to_plot.append(embed)
                # labels_to_plot.append(f"{spec}id:{chunk.get_id()}:{chunk.get_content()[0:30]}...") # Example label
                labels_to_plot.append(f"{spec}") # Example label
            else:
                logger.info(f'{config.HIS}Skipping chunk {chunk.get_id()} due to missing/empty embedding.{config.CLR}')
        
        if embeddings_to_plot:
            self.__plot_counter += 1
            plot_title = f"{self.__plot_counter}"
            
            # Adjust perplexity based on number of actual points being plotted
            num_points = len(embeddings_to_plot)
            perplexity_val = 30.0
            if num_points <=1:
                # Visualizer handles single point, but TSNE specific params are moot
                pass
            elif num_points <= perplexity_val:
                 perplexity_val = max(1.0, num_points -1.0)


            embedding.visualize.visualize_embeddings(
                embeddings_to_plot,
                labels=labels_to_plot,
                title=plot_title,
                tsne_perplexity=perplexity_val, # Dynamic perplexity
                tsne_max_iter=1000# tsne_max_iter can be kept at default or adjusted
            )
        else:
            logger.info(f'{config.HIS}Timeline: No valid embeddings found in current history to visualize.{config.CLR}')
