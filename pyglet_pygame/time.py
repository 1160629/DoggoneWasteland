
class Clock:
    def __init__(self):
        self.fps = 60

    def tick(self, fps):
        self.fps = fps

    def get_fps(self):
        return self.fps