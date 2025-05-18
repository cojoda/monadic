# import logging
# from typing import Sequence, List, Optional
# from evaluation.visualization import embedding

# from monadic.data import chunk



# logger = logging.getLogger(__name__)



# def plot(
#     history:  Sequence['chunk.Chunk'],
#     outgoing: Optional['chunk.Chunk'],
#     counter:  int,
#     *,
#     title_prefix: str = 'tsne',
#     plot_dir: str = 'embedding_plots'
# ) -> int:
    
#     '''
#     Convert Timeline state into (embeddings, labels) and call `embedding.visualize`.

#     Returns the **incremented** counter so Timeline can keep its own copy.
#     '''
#     if not history and outgoing is None:
#         logger.info('Timeline: nothing to plot.')
#         return counter

#     working = list(history) + ([outgoing] if outgoing else [])
#     ctx_ids = (
#         {c.id for c in outgoing.context} | {outgoing.id}
#         if outgoing else set()
#     )

#     embeddings: List[list[float]] = []
#     labels:     List[str]         = []

#     for idx, chunk in enumerate(working):
#         vec = chunk.context
#         if not vec:
#             logger.debug('Skipping chunk %s - no embedding.', chunk.id)
#             continue
#         label = f'id:{idx},{chunk.data}' if idx in ctx_ids else ''
#         embeddings.append(vec)
#         labels.append(label)

#     if not embeddings:
#         logger.info('Timeline: no embeddings available after filtering.')
#         return counter

#     counter += 1
#     embedding.visualize(
#         embeddings,
#         labels=labels,
#         title=f'{title_prefix}-{counter}',
#         plot_dir=plot_dir,
#         tsne_perplexity=max(5.0, min(30.0, len(embeddings) - 1)),
#         tsne_max_iter=1_000,
#     )
#     return counter
