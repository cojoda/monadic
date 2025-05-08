from collections import deque



class Window:

    def __init__(self, size):
        self.max_size = size
        self.window = deque(maxlen=self.max_size)

    def slide(self, pane):
        front = self.window.popleft()
        self.window.append(pane)
        return front
    
    def open(self):
        return [pane['index'] for pane in self.window]
    
    def __len__(self):
        return len(self.window)