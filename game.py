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
        # game loop
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

# check if cooldowns are working?
# save remaining refactoring for later, get some abilities working!

# refactoring:
# in general: more comments, and some cleanup
# specifically:
# clean up Unit stuff heavily
# - movement & pathfinding
# - projectiles & attack logic
# - ...
# and think about;
# abilities
# status effects
# proper combat logic system
