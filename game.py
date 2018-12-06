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

# and do chests, beds, ?shops?

# ignore for now
# enemies cant move between rooms

# still can't move to bottom tiles in dungeon
# is this cuz of wall tiles? -- yeah!
# so bottom wall tiles should be walkable? :-)
# but we use same ones for top and bottom
# maybe ignore this? will take long to solve.
# fastest solution might be post-loading, 
# to figure out all bottom-tiles and overwrite
# walkable flag to True
# yes? maybe this.
# ignore, for now.

# ignore for now
# ray-box checks 
# to determine if any objects occlude targets?

# background for ui - do this last, when everything else about ui is set in stone

# ignore for now
# throw together something quick here? if possible
# time rating: 5 hours
# fix:
# correct equipping of weapons according to attacks/abilities
# TryToLeave - ensure it is working, once doors are added
# weapon/shields/gear mods
# add shields & gear?
# ensure everything as working as intended
# dead enemies still get labels? oopsie. could change label to take a unit, and then the update
# function of label could see if the unit is dead, and remove that label.
# make sure weapons apply their stat mods & status effect mods :)
# easiest solution; only do it on basic attacks.
# well... they still have stat mods that should always apply...
# so make a proper solution?
# also deal with making sure the correct weapons are applied
# / equipped when casting certain abilities (also check for basic attacks)

# ignore for now
# time rating: 2 hours
# in game menu
# - when you start the game, just drop the player into the training map
# if the player wants to load, then they can load from a set of 5 saves
# if they want to start a new run, they just keep playing
# so there is only an in game menu, openable by pressing a little UI item;
# Resume (Onwards)
# Save - figure out everything that needs to be stored, store it as json
# Load - then load it from json
# Settings - also a json file, specifying certain in game things
# examples: resolution, render lighting pass or not, music volume, sound volume
# Quit (Some other time)

# time rating: 5 hours
# implement farm house (with tutorial)
# what's done: sandra's levels imported
# what's needed: a custom function to set up the map
# and maybe a small intro
# and logic for "falling through"
# will this take us to a different map?

# ignore for now
# just a combat indicator, really
# make this 0.5 hrs
# time rating: 2 hours
# cool things swishing by screen when fights start etc
# or at least an indicator
# don't spend much time here - just a half our if you can

# time rating: 5 hours
# AI. 
# make a very simple A.I.
# with two archetype controllers for "melee, ranged"

# time rating: 2 hours
# weapons, abilities, etc
# need little widgets representing them;
# for our ui
# maybe just use 1x1 weapons, gear, etc?
# this is probably the best thoice
# then we can use the same image
# everywhere

# time rating: 0.5 hours
# UI tooltips - for weapons, abilities, syringes.
# both on the ground, and when equipped.

# time rating: 2.5 hours
# equipping stuff:
# loot on the ground
# and abilities from skill tree
# reordering abilities and weapons

# ignore for now
# time rating: 2.5 hours
# mutations!

# time rating: 0.5 hours
# show cooldowns

# ignore for now
# time rating: 0.5 hours
# show status effects


# if you get here, youve got real far. :-)


# forget about this for now, just make shit work!
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
