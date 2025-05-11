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
        logger.info('\033[35m'+'},\n'.join(str(self.timeline.get_history()).split('},'))+'\033[0m')
        response = interactions.responses(self.timeline.get_history())
        logger.info(f'\033[35minput tokens: {response.usage.input_tokens}; output tokens: {response.usage.output_tokens}\033[0m')
        self.timeline.add_history('assistant', response.output_text)
        return response.output_text
