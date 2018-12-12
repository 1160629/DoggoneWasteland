from game_loader import load
from game_update import update
from game_drawing import draw


class Game:
    def __init__(self):
        pass

    def update(self):
        update(self)

    def draw(self):
        draw(self)

    def loop(self):
        while True:
            self.update()
            self.draw()


def start():
    g = Game()
    load(g)
    g.loop()


if __name__ == "__main__":
    # execution entry point for Python
    start()

