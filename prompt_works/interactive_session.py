import logging

from . import interactions

from prompt_works.history import event_timeline


class Interact:

    def __init__(self) -> None:
        self.input_tokens  = 0
        self.output_tokens = 0
        self.timeline      = event_timeline.Timeline()


    def respond(self, content) -> str:
        self.timeline.add_history('user', content)
        logging.debug('},\n'.join(str(self.timeline.get_history()).split('},')))
        # for line in str(self.timeline.get_history()).split('},'): print(line+'}')
        response = interactions.responses(self.timeline.get_history()).output_text
        self.timeline.add_history('assistant', response)
        return response
