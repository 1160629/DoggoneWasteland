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
# dropping needs to consider whether tiles are walkable or not - ignore for now.
# death animations / death timer not quite working? - not super important.
# no door close sound when going into combat.

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
# spawn a melee weapon in 1st room (done)
# start with 3 stat points (done)
# collar + bubbles
# grandpa in 1st room too (goes away when you leave first room) + bubbles
# bed in 1st room? constant 1st room layout? yeah, probably
# start in a state of resting
# wake up - bubbles?
# no more - enough!

# time rating: 5 hours
# AI. 
# make a very simple A.I.
# with two archetype controllers for "melee, ranged"

# ignore for now
# time rating: 2.5 hours
# mutations!
