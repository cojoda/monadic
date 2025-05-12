import logging

from . import interactions
from . import config

from monadic.history import event_timeline



logger = logging.getLogger(__name__)



class Interact:

    def __init__(self) -> None:
        self.input_tokens  = 0
        self.output_tokens = 0
        self.timeline      = event_timeline.Timeline()



    def respond(self, content) -> str:
        self.timeline.add_outgoing('user', content)

        response = interactions.responses(self.timeline.get_form())
        if response.usage: self.update_tokens(response.usage.input_tokens, response.usage.output_tokens)

        self.timeline.add_incoming('assistant', response.output_text)
        return response.output_text



    def update_tokens(self, input_tokens, output_tokens) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        token_string =  f'\n{config.MON}input tokens:        {input_tokens}{config.CLR}'
        token_string += f'\n{config.MON}output tokens:       {output_tokens}{config.CLR}'
        token_string += f'\n{config.MON}total input tokens:  {self.input_tokens}{config.CLR}'
        token_string += f'\n{config.MON}total output tokens: {self.output_tokens}{config.CLR}'
        logger.info(token_string)
