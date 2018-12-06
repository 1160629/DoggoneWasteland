import json
import xmltodict
import pygame
from itertools import product


# Dungeon class

class Room:
    def __init__(self):
        self.east = None
        self.west = None
        self.north = None
        self.south = None

        self.layout = None
        self.tilesets = None

    def setup(self):
        self.walkable_map = self.walkable_map = create_room_walkable_map(self)


def create_room_walkable_map(room):
    layout = room.layout

    mw, mh = room.layout.w, room.layout.h

    walkable_map = [[0 for i in range(mh)] for j in range(mw)]

    for x, y in product(range(mw), range(mh)):
        walkable = []
        for k in layout.layers.keys():
            tile_index = layout.get_tile_index(k, x, y)
            if tile_index == None:
                continue

            tile = room.tilesets.get_tile(*tile_index)
            walkable.append(tile.walkable)
        # print(walkable)
        walkable_map[x][y] = all(walkable)

    return walkable_map


class Dungeon:
    def __init__(self):
        self.rooms = []

        self.in_room = 0

    def get_room(self):
        return self.rooms[self.in_room]
