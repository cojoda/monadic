
from window import Window

class Context:
    def __init__(self):
        self.window = None

    def create_window(self, size):
        self.window = Window(size)

    def get_context(self):
        context = []

        # context window
        context.extend(self.window.open() if self.window else []) 

        # TODO: handle other context here too 

        # ancestors (aRAG)

        # beacons (sRAG)

        return context