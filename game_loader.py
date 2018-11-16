import pygame
import json
import xmltodict
from itertools import product

from dungeon import Dungeon, Room
from ui import UI, Camera

from generation import place_training_room_units

from combat import CombatController

from control import Animation, AnimationSetInitializer

from tiles import *


def setup_display_and_drawables(self):
    # set resolution
    self.w, self.h = 1600, 800
    # tileset & game scaling
    self.scaling = 2

    # display surface
    self.win = pygame.display.set_mode((self.w, self.h))

    # drawing surface
    self.swin = pygame.Surface((self.w, self.h))
    
    # other surfaces
    self.wsurf = pygame.Surface((16*self.scaling, 16*self.scaling))
    self.wsurf.set_alpha(200)
    self.nwsurf = pygame.Surface((16*self.scaling, 16*self.scaling))
    self.nwsurf.set_alpha(200)
    self.wsurf.fill((0,255,0))
    self.nwsurf.fill((255,0,0))


# load equipment stuff

def load_json(path_to_json):
    with open(path_to_json, "r") as f:
        object = json.load(f)

    return object
	


# functions for loading tilesets and maps

def load_tsx(filename):
    with open(filename, "r") as f:
        xml = "\n".join(f.readlines()[0:])

    d = (xmltodict.parse(xml))
    return d

def load_tileset(img_path, data_path, width, height, scale):
    # from https://stackoverflow.com/questions/16280608/pygame-how-to-tile-subsurfaces-on-an-image
    # - edited

    image = pygame.image.load(img_path).convert_alpha()
    image_width, image_height = image.get_size()

    nw, nh = image_width//width, image_height//height

    with open(data_path, "r") as f:
        d = json.load(f)

    d_ = {k["id"]: True for k in d["tiles"]}

    tileset = Tileset()
    tileset.tw, tileset.th = width * scale, height * scale
    tileset.nw, tileset.nh = nw, nh

    for tile_x in range(0, nw):
        line = []
        tileset.tiles.append(line)
        for tile_y in range(0, nh):
            rect = (tile_x*width, tile_y*height, width, height)
            new = pygame.transform.scale(image.subsurface(rect), (width*scale, height*scale))
            new.set_colorkey(image.get_colorkey())
            
            tid = tile_y * (nw) + tile_x # flat indexing
            if str(tid) not in d_:
                walkable = True
            else:
                walkable = False

            tile = Tile()
            tile.image = new
            tile.walkable = walkable
            
            tileset.tiles[tile_x].append(tile)

    return tileset

def load_tilesets(json_filename, scale):
    with open(json_filename, "r") as f:
        d = json.load(f)    

    tsets = Tilesets()
    for k in d.keys():
        ele = d[k]
        fpath = ele["path"]
        j = load_tsx(fpath)

        tw, th = int(j["tileset"]["@tilewidth"]), int(j["tileset"]["@tileheight"])

        img_path = j["tileset"]["image"]["@source"]
        data_path = ".".join(img_path.split(".")[:-1])+".json"

        tset = Tileset()
        tset = load_tileset(img_path, data_path, tw, th, scale)
        tset.source = fpath
        
        tsets.tilesets[k] = tset

    tsets.tw, tsets.th = tw*scale, th*scale

    return tsets


# load a layout; a json export of a tiled map

def convert_tile_index(flat, sources, tsets):
    which_tileset = None
    which_source = None
    source_fgid = None

    i = 0
    while i+1 < len(sources):
        ele = sources[i]
        ele_next = sources[i+1]
        if ele["firstgid"] <= flat < ele_next["firstgid"]:
            which_source = ele
            break
        i += 1
    else:
        which_source = sources[-1]

    for k in tsets.tilesets.keys():
        tset = tsets.tilesets[k]
        if which_source["source"] == tset.source:
            which_tileset = k
            break
    else:
        raise Exception("Could not map tile")

    source_fgid = which_source["firstgid"]
    flat_corr = flat - source_fgid #+ 1
    tset = tsets.tilesets[which_tileset]
    nw, nh = tset.nw, tset.nh
    x = flat_corr % nw
    y = flat_corr // nw
    mat_tile = [which_tileset, x, y]

    return mat_tile

def convert_layer_indexes_and_tile_indexes(layer, lw, lh, sources, tilesets):
    data = layer["data"]
    mat_data = [[None for y in range(lh)] for x in range(lw)]
    for x, y in product(range(lw), range(lh)):
        flat_data_index = y * lw + x
        flat_tile_index = data[flat_data_index]
        if flat_tile_index == 0:
            continue
        mat_tile_index = convert_tile_index(flat_tile_index, sources, tilesets)
        mat_data[x][y] = mat_tile_index

    return mat_data

def convert_layers(layers, sources, tilesets):
    new_layers = {}
    for l in layers:
        lw, lh = l["width"], l["height"]
        l["data"] = convert_layer_indexes_and_tile_indexes(l, lw, lh, sources, tilesets)
        
        layer_name = l["name"]
        new_layers[layer_name] = l 

    return new_layers

def load_layout(path, tilesets):
    with open(path, "r") as f:
        d = json.load(f)

    mapwidth, mapheight = int(d["width"]), int(d["height"])

    layers = convert_layers(d["layers"], d["tilesets"], tilesets)
    
    layout = Layout()
    layout.w, layout.h = mapwidth, mapheight
    layout.layers = layers

    return layout


# load animations


def load_animations(json_file_path):
    with open(json_file_path, "r") as f:
        d = json.load(f)

    animations = AnimationSetInitializer(d)

    return animations


# game load function

def load(self):
    pygame.init()
    
    setup_display_and_drawables(self)

    self.scale = 2
    self.tilesets = load_tilesets("tilesets.json", self.scale)

    self.animations = load_animations("animations.json")

    self.dungeon = Dungeon()
    room = Room()
    room.layout = load_layout("Training_Room.json", self.tilesets)
    room.tilesets = self.tilesets
    room.setup()
    self.dungeon.rooms.append(room)
    self.dungeon.in_room = 0

    self.ui = UI(self)

    self.cam = Camera(self.w, self.h)        


    weapons = load_json("weapons.json")
    gear = load_json("gear.json")

    self.units = place_training_room_units(weapons, self.animations)


    self.cc = CombatController()
    self.cc.units_in_combat = self.units


    self.clock = pygame.time.Clock()
    self.fps = 144