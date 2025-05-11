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
        logger.info('\n'+'\033[35m'+'},\n'.join(str(self.timeline.get_history()).split('},'))+'\033[0m')

        response = interactions.responses(self.timeline.get_history())
        if response.usage: self.update_tokens(response.usage.input_tokens, response.usage.output_tokens)

        self.timeline.add_history('assistant', response.output_text)
        return response.output_text



    def update_tokens(self, input_tokens, output_tokens) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        token_string =  f'\n\033[35minput tokens:        {input_tokens}\033[0m'
        token_string += f'\n\033[35moutput tokens:       {output_tokens}\033[0m'
        token_string += f'\n\033[35mtotal input tokens:  {self.input_tokens}\033[0m'
        token_string += f'\n\033[35mtotal output tokens: {self.output_tokens}\033[0m'
        logger.info(token_string)