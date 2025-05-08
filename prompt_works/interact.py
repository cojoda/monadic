from . import interactions

from .history.timeline import Timeline



class Interact:

    def __init__(self) -> None:
        self.timeline = Timeline()


    def respond(self, content):
        self.timeline.add_record('user', content)
        response = interactions.responses(self.timeline.get_records()).output_text
        self.timeline.add_record('assistant', response)
        return response
