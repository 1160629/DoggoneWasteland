
from logic import Rect
import json
import xmltodict
from itertools import product

from ui import UI, Camera

from generation import place_starting_units, generate_dungeon

from combat import CombatController

from control import Animation, AnimationSetInitializer, RenderLogic, LabelMgr, SkillTreeMgr, Tooltips

from tiles import *

from audio import Music, SoundManager

import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

def setup_display_and_drawables(self):
    # set resolution
    self.w, self.h = 1600, 800

    # display surface
    self.scale = 3
    self.tw, self.th = 16 * self.scale, 16 * self.scale
    self.swin = pygame.display.set_mode((self.w, self.h), pygame.HWSURFACE)

    self.black_surf = pygame.Surface((self.w, self.h))
    self.black_surf.fill((0,0,0))

    # drawing surface
    #self.swin = pygame.Surface((self.w, self.h), flags = pygame.HWSURFACE)
    
    # other surfaces
    self.wsurf = pygame.Surface((16*self.scale, 16*self.scale), flags = pygame.HWSURFACE)
    self.wsurf.set_alpha(200)
    self.nwsurf = pygame.Surface((16*self.scale, 16*self.scale), flags = pygame.HWSURFACE)
    self.nwsurf.set_alpha(200)
    self.wsurf.fill((0,255,0))
    self.nwsurf.fill((255,0,0))

    self.darktile = pygame.Surface((16*self.scale, 16*self.scale), flags = pygame.HWSURFACE)
    self.darktile.set_alpha(50)
    self.darktile.fill((0,0,0))

    self.lighttile = pygame.Surface((16*self.scale, 16*self.scale), flags = pygame.HWSURFACE)
    self.lighttile.set_alpha(50)
    self.lighttile.fill((255,200,200))

    tsx, tsy = 150, 50
    self.tsurf = pygame.Surface((tsx, tsy), flags = pygame.HWSURFACE)
    self.tsurf.fill((255, 255, 255))

# generic functions to load and store json

def load_json(path_to_json):
    with open(path_to_json, "r") as f:
        o = json.load(f)

    return o
	

def store_json(path_to_json, o):
    with open(path_to_json, "w+") as f:
        json.dump(o, f)


# functions for loading tilesets and maps

def load_tsx(filename):
    with open(filename, "r") as f:
        xml = "\n".join(f.readlines()[0:])

    d = (xmltodict.parse(xml))
    return d

def get_tiles_metadata(data_path):
    d = load_json(data_path)

    meta = {}
    tiles = d["tiles"]

    for i in tiles:
        tid = i["id"]
        meta[tid] = {
            "collidable": False,
            "triggerable": False
        }
        cmeta = meta[tid]
        
        if "properties" not in i:
            continue
        props = i["properties"]
        for p in props:
            if p["name"] == "Collidable" and p["value"] == True:
                cmeta["collidable"] = True
            elif p["name"] == "Triggerable" and p["value"] == True:
                cmeta["triggerable"] = True

    return meta

def load_tileset(img_path, data_path, width, height, scale):
    # from https://stackoverflow.com/questions/16280608/pygame-how-to-tile-subsurfaces-on-an-image
    # - edited

    image = pygame.image.load(img_path).convert_alpha()
    image_width, image_height = image.get_size()

    nw, nh = image_width//width, image_height//height

    meta = get_tiles_metadata(data_path)

    tileset = Tileset()
    tileset.tw, tileset.th = width * scale, height * scale
    tileset.nw, tileset.nh = nw, nh

    for tile_x in range(0, nw):
        line = []
        tileset.tiles.append(line)
        for tile_y in range(0, nh):
            rect = Rect(tile_x*width, tile_y*height, width, height)
            transformed = pygame.transform.scale(image.subsurface(rect), (width*scale, height*scale))
            new = pygame.Surface((width*scale, height*scale), flags = pygame.HWSURFACE)
            new.fill((0,0,0))
            new.set_colorkey((0,0,0))
            new.blit(transformed, (0,0))
            
            tid = (tile_y * (nw) + tile_x) # flat indexing
            if tid in meta and meta[tid]["collidable"]:
                walkable = False
            else:
                walkable = True

            if tid in meta and meta[tid]["triggerable"]:
                triggerable = True
            else:
                triggerable = False

            tile = Tile()
            tile.image = new
            tile.walkable = walkable
            tile.triggerable = triggerable
            
            tileset.tiles[tile_x].append(tile)

    return tileset

def load_tilesets(json_filename, scale):
    d = load_json(json_filename)    

    tsets = Tilesets()
    for k in d.keys():
        ele = d[k]
        fpath = ele["path"]

        j = load_tsx(fpath)

        tw, th = int(j["tileset"]["@tilewidth"]), int(j["tileset"]["@tileheight"])

        img_path = "tilesets/actual/" + j["tileset"]["image"]["@source"]
        data_path = ".".join(img_path.split(".")[:-1])+".json"

        tset = Tileset()
        tset = load_tileset(img_path, data_path, tw, th, scale)
        tset.source = fpath
        
        tsets.tilesets[k] = tset

    tsets.tw, tsets.th = tw*scale, th*scale

    return tsets


# load a layout; a json export of a tiled map

def from_same_source(s1, s2):
    l1 = s1.split("/")[-1]
    l2 = s2.split("/")[-1]

    return l1 == l2

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
        if from_same_source(which_source["source"], tset.source):
            which_tileset = k
            break
    else:
        raise Exception("Could not map tile")

    FLIPPED_HORIZONTALLY_FLAG = 0x80000000
    FLIPPED_VERTICALLY_FLAG   = 0x40000000
    FLIPPED_DIAGONALLY_FLAG   = 0x20000000

    flags = FLIPPED_HORIZONTALLY_FLAG, FLIPPED_VERTICALLY_FLAG, FLIPPED_DIAGONALLY_FLAG
    lowest_flag = min(flags)

    and_with = lowest_flag-1 # 2**29-1

    source_fgid = which_source["firstgid"]
    flat_corr = (flat - source_fgid) & and_with #+ 1
    flat_nocorr = flat - source_fgid

    tset = tsets.tilesets[which_tileset]
    nw, nh = tset.nw, tset.nh
    x = flat_corr % nw
    y = flat_corr // nw
    h, v, d = (FLIPPED_HORIZONTALLY_FLAG & flat_nocorr) >> 31, (FLIPPED_VERTICALLY_FLAG & flat_nocorr) >> 30, \
    (FLIPPED_DIAGONALLY_FLAG & flat_nocorr) >> 29
    mat_tile = [which_tileset, x, y, h, v, d]

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
    d = load_json(path)

    mapwidth, mapheight = int(d["width"]), int(d["height"])

    layers = convert_layers(d["layers"], d["tilesets"], tilesets)
    
    layout = Layout()
    layout.w, layout.h = mapwidth, mapheight
    layout.layers = layers

    return layout

def load_layouts(path):
    d = load_json(path)
    return d

def load_layout_mods(path):
    d = load_json(path)
    return d

# load animations

def tiledanimformat2ouranimformat(json_file_path):
    save_to = "animations_converted.json"
    d = load_json(json_file_path)

    new_d = {}

    # need UltimateTileset.json's animations to have
    # both set-type (i.e. character), and anim-type
    # (i.e. character-walking, character-standing)
    # this would make conversion easier.

    for k, e in d.items():
        new_ele = {}
        new_d[k] = new_ele

    store_json(new_d, save_to)

#tiledanimformat2ouranimformat("/tilesets/UltimateTileset.json")

def load_animations(json_file_path):
    d = load_json(json_file_path)

    animations = AnimationSetInitializer(d)

    return animations


def load_game_module(use_pygame_replacement):
    global pygame
    if not use_pygame_replacement:
        import pygame
        import_statement = "import pygame"
    else:
        import pyglet_pygame as pygame
        import_statement = "import pyglet_pygame as pygame"

    using_module = "dungeon.py", "prerendering.py", "drawing.py", "game_update.py", "audio.py"

    for m in using_module:
        with open(m, "r") as f:
            l = f.readlines()

        l[0] = import_statement+"\n"
        n = "".join(l)

        with open(m, "w+") as f:
            l = f.write(n)


# load sound and music

def audio_loader(sound_path, music_path):
    ds = load_json(sound_path)
    dm = load_json(music_path)

    snd_rel = "./audio/sounds/"
    msc_rel = "./audio/music/"

    sndmgr = SoundManager()
    sndmgr.setup_sounds(snd_rel, ds)

    music = Music()
    songs = dm
    music.songs = songs
    music.rel = msc_rel

    return sndmgr, music


# game load function

def load(self):
    use_pygame_replacement = False
    load_game_module(use_pygame_replacement)
    from prerendering import prerender
    from dungeon import Dungeon, Room

    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    
    setup_display_and_drawables(self)

    # tileset & game scaling
    self.tilesets = load_tilesets("json/tilesets.json", self.scale)
    self.botlayers = "Floor1", "Floor2 (Decoration)"
    self.toplayers = "Walls (Collidable)", "Items1 (Collidable)"#, "Items2 (Triggerable)"
    self.layouts = load_layouts("json/layouts.json")
    self.layout_mods = load_layout_mods("json/layout_mods.json")

    self.animations = load_animations("json/animations.json")

    self.sound, self.music = audio_loader("json/sound.json", "json/music.json")
    self.music.muted = True

    self.font = pygame.font.Font("fonts/joystix proportional.otf", 36)
    self.smallfont = pygame.font.Font("fonts/joystix proportional.otf", 24)

    weapons = load_json("json/weapons.json")
    gear = load_json("json/gear.json")

    self.tooltips = Tooltips()
    self.tooltips.load_tooltips(load_json, "json/tooltips.json")

    

    self.stage = 0
    rw, rh = self.rw, self.rh = 32, 13
    self.dungeon = generate_dungeon(self.layouts, self.layout_mods, self.tilesets, rw, rh, stage = self.stage)
    self.dungeon.setup_rooms(load_layout, self.sound)

    self.ui = UI(self)

    self.cam = Camera(self.w, self.h)    

    self.labels = LabelMgr(self.w)

    self.mc, self.units = place_starting_units(weapons, self.labels, self.animations, self.dungeon, rw, rh, self.sound)

    self.skilltree_mgr = SkillTreeMgr(self.mc.skilltree, self.tw, self.th, self.h, self)
    self.skilltree_mgr.setup()

    self.cc = CombatController()
    self.cc.units_in_combat = self.units

    # other drawing stuff
    self.renderlogic = RenderLogic()
    prerender(self, self.renderlogic)

    self.clock = pygame.time.Clock()
    self.fps = 144

