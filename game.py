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



# so;

# FIX!!
# East-doors of starting room sometimes broken? wtf
# Dungeon generation edge-cases w/ constraint of 2 connections (i.e. it spawns itself stuck in a corner)

# background for ui - do this last, when everything else about ui is set in stone

# ignore for now
# time rating: 5 hours
# combat system:
# fix:
# correct equipping of weapons according to attacks/abilities
# TryToLeave - ensure it is working, once doors are added
# add shields & gear?
# weapon/shields/gear mods
# ensure everything as working as intended (i.e. mods applying)

# time rating: 1.5 hours
# farmhouse:
# specials stuff

# time rating: 2 hours
# enemy spawning:
# make archetype stuff

# time rating: 5 hours
# AI. 
# make a very simple A.I.
# with two archetype controllers for "melee, ranged"

# time rating: 2.5 hours
# equipping stuff:
# loot on the ground
# and abilities from skill tree
# reordering abilities and weapons

# ignore for now
# time rating: 2.5 hours
# mutations!
