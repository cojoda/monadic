from . import interactions

from .history.timeline import Timeline



class Interact:

    def __init__(self) -> None:
        self.timeline = Timeline()


    def respond(self, content):
        self.timeline.add_record('user', content)
        response = interactions.responses(self.timeline.get_record()).output_text
        self.timeline.add_record('assistant', response)
        return self.timeline.get_last_record().get_content()
