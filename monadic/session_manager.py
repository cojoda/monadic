import logging


from monadic.context.context import Context
from monadic.data.chunk import Chunk
from monadic.history import timeline_manager
from monadic.interaction.batch import embedding_batcher



logger = logging.getLogger(__name__)



class Session:

    def __init__(self, connections):
        self.connections   = connections
        self.timeline      = timeline_manager.Timeline()
        self.input_tokens  = 0
        self.output_tokens = 0


    def exchange(self, data):
        uid = len(self.timeline)

        context = Context(
            uid    =uid,
            data   =data,
            history=self.timeline.history
        )

        chunk = Chunk(
            role   ='user',
            data   =data,
            uid    =uid,
            context=context
        )

        self.timeline.append(chunk)
        embedding_batcher.send()
        return 'output'
