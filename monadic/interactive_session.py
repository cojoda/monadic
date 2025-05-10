import logging

from . import interactions

from monadic.history import event_timeline



logger = logging.getLogger(__name__)



class Interact:

    def __init__(self) -> None:
        self.input_tokens  = 0
        self.output_tokens = 0
        self.timeline      = event_timeline.Timeline()


    def respond(self, content) -> str:
        self.timeline.add_history('user', content)
        logger.debug('},\n'.join(str(self.timeline.get_history()).split('},')))
        response = interactions.responses(self.timeline.get_history()).output_text
        self.timeline.add_history('assistant', response)
        return response
