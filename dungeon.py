import pygame
import json
import xmltodict
from itertools import product
from control import ActionTimer, LootSpawner
from logic import Rect, in_range
from random import choice, randint, shuffle, choice, random

# Dungeon class

class Room:
    def __init__(self, layout_path=None, tilesets=None):
        self.room_type = None
        self.room_id = None

        self.grid_pos = 0, 0

        self.east = None
        self.west = None
        self.north = None
        self.south = None

        self.layout = None

        self.layout_name = None

        if layout_path != None:
            self.layout_path = layout_path
        else:
            self.layout = None
        if tilesets != None:
            self.tilesets = tilesets
        else:
            self.tilesets = None

        self.layout_mod = None
        self.layout_mod_path = None

        self.has_enemies = False
        self.has_boss = False

        self.unexplored = True
        self.danger_rating = None

        self.connectors = {}
        self.connected = {}

        self.has_rested = False
        self.has_been = False

        self.needs_doors = []

        self.needs_bed_logic = False
        self.needs_shopkeeper = False
        self.needs_chest = False

    def get_n_connections(self):
        n = 4 - sum(list(map(lambda x: x == None, (self.east, self.west, self.north, self.south))))
        return n

    def add_layout_mod(self, lm, lmp):
        self.layout_mod = lm
        self.layout_mod_path = lmp

    def remove_layout_mod(self):
        self.layout_mod = None
        self.layout_mod_path = None

    def pre_setup(self, loader):
        self.layout = loader(self.layout_path, self.tilesets)

        self.walkable_map = create_room_walkable_map(self)

    def post_setup(self):
        self.walkable_map = create_room_walkable_map(self)

    def setup(self, loader):
        if self.layout_mod != None:
            self.setup_layout_mod(loader)

        self.create_hallways(loader)

    def change_layout(self, sindx, eindx, sindy, eindy, lay, boostx=0, boosty=0, fromx=0, fromy=0, tox=0, toy=0):
        layer_names = list(self.layout.layers)

        if toy == 0:
            endy = eindy
        else:
            endy = toy

        if tox == 0:
            endx = eindx
        else:
            endx = tox

        for x_, y_, l in product(range(sindx, eindx + 1), range(sindy, eindy + 1), layer_names):
            x, y = x_ + fromx, y_ + fromy
            if not lay.has_layer(l):
                continue
            if not ((sindx <= x <= endx) and (sindy <= y <= endy)):
                continue
            mx, my = x - sindx, y - sindy
            tind = lay.get_tile_index(l, mx, my)
            orient = lay.get_tile_orient(l, mx, my)

            self.layout.set_tile_index_and_orient(l, x + boostx, y + boosty, tind, orient)

    def setup_layout_mod(self, loader):
        self.layout_mod = loader(self.layout_mod_path, self.tilesets)

        sindx, eindx = 13, 18
        sindy, eindy = 4, 9

        self.change_layout(sindx, eindx, sindy, eindy, self.layout_mod)

    def create_hallways(self, loader):
        for k, i in self.connectors.items():
            if k == "north":
                self.make_north_hallway(loader, k, i)
                self.north.connected["southern room"] = "connected to you"
            elif k == "south":
                self.make_south_hallway(loader, k, i)
                self.south.connected["southern room"] = "connected to you"
            elif k == "east":
                self.make_east_hallway(loader, k, i)
                self.east.connected["eastern room"] = "connected to you"
            elif k == "west":
                self.make_west_hallway(loader, k, i)
                self.west.connected["western room"] = "connected to you"

    def make_north_hallway(self, loader, key, item):
        name, lout, sindx_rand = item[0], loader(item[1], self.tilesets), item[2]

        sindy, eindy = 0, 4
        sindx, eindx = 0, 3

        door = (sindx_rand, 0), "north"
        self.needs_doors.append(door)

        self.change_layout(sindx, eindx, sindy, eindy, lout, boostx=sindx_rand, boosty=-2, fromy=2)

    def make_south_hallway(self, loader, key, item):
        name, lout, sindx_rand = item[0], loader(item[1], self.tilesets), item[2]

        sindy, eindy = 0, 4
        sindx, eindx = 0, 3

        door = (sindx_rand, 13), "south"
        self.needs_doors.append(door)

        self.change_layout(sindx, eindx, sindy, eindy, lout, boostx=sindx_rand, boosty=11, fromy=0, toy=1)

    def make_east_hallway(self, loader, key, item):
        name, lout, sindy_rand = item[0], loader(item[1], self.tilesets), item[2]

        sindy, eindy = 0, 3
        sindx, eindx = 0, 3

        door = (31, sindy_rand), "east"
        self.needs_doors.append(door)

        self.change_layout(sindx, eindx, sindy, eindy, lout, boosty=sindy_rand, boostx=30, fromx=0, tox=1)

    def make_west_hallway(self, loader, key, item):
        name, lout, sindy_rand = item[0], loader(item[1], self.tilesets), item[2]

        sindy, eindy = 0, 3
        sindx, eindx = 0, 3

        door = (0, sindy_rand), "west"
        self.needs_doors.append(door)

        self.change_layout(sindx, eindx, sindy, eindy, lout, boosty=sindy_rand, boostx=-2, fromx=2)


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


# may want to manage doors and chests outside the
# "room" class? as individual entities?
# could be managed by dungeon

# because they will be animated, not static
# and that will be weird in terms of prerendering?
# then again, prerendering won't be called often for doors and chests
# BUT we will need to manage the shopkeep dudes regardless
# as well as loot/loot spawners
# figure out

def should_be_open(self, door, m):
    dung = self.dungeon
    doors = dung.doors

    d = door
    lout = d.get_layout()
    bx, by = d.pos
    ox, oy = d.get_off()
    roomx, roomy = d.room_pos
    tsw, tsh = d.get_ts_size()
    direction = door.direction
    return should_be_open_tbt(self, lout, bx, by, roomx, roomy, ox, oy, tsw, tsh, m, direction)


def should_be_open_tbt(self, lout, bx, by, roomx, roomy, ox, oy, tsw, tsh, m, direction):
    if direction == "east":
        range_mod = 2
    else:
        range_mod = 2

    tw, th = self.tw, self.th

    cam = self.cam
    cx, cy = cam.get()
    # print(cx, cy)

    rw, rh = self.rw, self.rh

    rx = tw * roomx * rw
    ry = th * roomy * rh

    rsize = tw, th

    u = self.mc
    x, y = u.anim_pos
    rux, ruy = ox + x * tw, oy + y * th
    aox, aoy = 0, 0
    if (u.state == "attacking" and u.attack_weapon.attack_type == "melee") or u.dashing:
        aox, aoy = u.projectile_pos

    mc_pos = rux + aox + cx + tw / 2, ruy + aoy + cy + th / 2

    mpos = m

    mover = []
    inrange = []

    for dx, dy in product(range(tsw), range(tsh)):

        at = rx + (bx - ox + dx) * tw + cx, ry + (by - oy + dy) * th + cy
        # at = (bx+dx) * tw, (by+dy) * th
        # self.swin.blit(img, at)

        r = Rect(at, rsize)
        if r.collidepoint(mpos):
            mover.append(True)
        else:
            mover.append(False)
        if in_range(mc_pos, r.center, 3 + tw * range_mod):
            inrange.append(True)
        else:
            inrange.append(False)

    if any(inrange):# and any(mover):
        return True
    else:
        return False


class Door:
    def __init__(self, lm, ts, sound):
        self.open_tiles = None
        self.closed_tiles = None

        self.is_closed = True

        self.layout_mods = lm
        self.tilesets = ts

        self.trans = {
            "west": {
                "open": "door_open_left_farm",
                "closed": "door_closed_left_farm"
            },
            "east": {
                "open": "door_open_right_farm",
                "closed": "door_closed_right_farm"
            },
            "north": {
                "open": "door_open_up_farm",
                "closed": "door_closed_up_farm"
            },
            "south": {
                "open": "door_open_down_farm",
                "closed": "door_closed_down_farm"
            },
        }

        self.pos = None
        self.off = None
        self.room_pos = None

        self.direction = None

        self.sound = sound
        self.open_timer = ActionTimer("interact", 0.5)

        self.belongs_to = None

    def get_ts_size(self):
        ysize = 2
        if self.direction in ("north", "south"):
            xsize = 2
        else:
            if self.is_closed:
                xsize = 1
            else:
                xsize = 3

        return xsize, ysize

    def get_off(self):
        if self.direction == "east" and self.is_closed == False:
            off = self.off[0] + 2, self.off[1]
        else:
            off = self.off

        return off

    def setup(self, item, loader):
        pos, orient = item

        self.direction = orient

        on = self.trans[orient]["open"]
        cn = self.trans[orient]["closed"]

        op = self.layout_mods[on]
        cp = self.layout_mods[cn]

        self.open_tiles = loader(op, self.tilesets)
        self.closed_tiles = loader(cp, self.tilesets)

        self.pos = pos

        if orient == "north":
            self.off = -1, 0
        elif orient == "east":
            self.off = 0, -1
        elif orient == "south":
            self.off = -1, 2
        elif orient == "west":
            self.off = 0, -1

    def get_layout(self):
        if self.is_closed:
            return self.closed_tiles
        else:
            return self.open_tiles

    def get_collidable(self):
        tsw, tsh = self.get_ts_size()
        ox, oy = self.get_off()
        px, py = self.pos

        reals = []
        for x, y in product(range(tsw), range(tsh)):
            if self.direction in ("south",) and \
                    (y == 0):
                continue
            rx = -ox + px + x
            ry = -oy + py + y
            real = rx, ry
            reals.append(real)
        return reals

    def should_be_open(self, g_obj, m):
        return should_be_open(g_obj, self, m)
        # return False

    def update(self, g_obj, mpos, mpress, ui, fighting):
        self.open_timer.update()

        if fighting:
            if not self.is_closed and ((not self.should_be_open(g_obj, mpos)) or self.room_pos != g_obj.dungeon.get_room().grid_pos):
                self.is_closed = True
                self.sound.play_sound_now("door close")
            return

        #if not self.open_timer.ticked:
        #    return

        #if not ui.get_selected() == None:
        #    return

        am = ui.at_mouse
        
        """
        m = am["mapped"]
        if self.check_mouseover(g_obj, mpos):
            if self.is_closed == True:
                self.is_closed = False
                self.sound.play_sound_now("door open")
            elif self.is_closed == False:
                self.is_closed = True
                self.sound.play_sound_now("door close")

            self.open_timer.reset()
        """
        m = am["mapped"]
        if self.should_be_open(g_obj, mpos):
            if self.is_closed == True:
                self.is_closed = False
                self.sound.play_sound_now("door open")

                #self.open_timer.reset()
        else:
            if self.is_closed == False:
                self.is_closed = True
                self.sound.play_sound_now("door close")

                #self.open_timer.reset()

class Dungeon:
    def __init__(self):
        self.rooms = []
        self.hallways = []

        self.doors = []
        self.chests = []
        self.beds = []
        self.shopkeepers = []
        self.specials = []

        self.in_room = 0

        self.stage = None
        self.stage_name = None

    def update(self, mc_pos, g_obj, mpos, mpress, ui, fighting):
        for d in self.doors:
            d.update(g_obj, mpos, mpress, ui, fighting)

        for c in self.chests:
            c.update(g_obj.mc, mpos, mpress, ui, fighting)

        for s in self.shopkeepers:
            s.update(g_obj.mc, mpos, mpress, ui, fighting)

        for b in self.beds:
            b.update(g_obj, mpos, mpress, ui, fighting)

        if fighting:
            return

        gr = self.get_room()
        if not gr.has_been:
            gr.has_been = True
            g_obj.mc.get_xp(1)

        mcx, mcy = mc_pos
        px, py = mcx // g_obj.rw, mcy // g_obj.rh
        ind = 0
        for r in self.rooms:
            gx, gy = r.grid_pos
            if (gx, gy) == (px, py):
                self.in_room = ind
                break
            ind += 1

    def get_room(self):
        return self.rooms[self.in_room]

    def which_room(self, u, g_obj):
        mcx, mcy = u.pos
        px, py = mcx // g_obj.rw, mcy // g_obj.rh
        ind = 0
        for r in self.rooms:
            gx, gy = r.grid_pos
            if (gx, gy) == (px, py):
                in_room = ind
                break
            ind += 1
        # print(px, py)
        return self.rooms[in_room]

    def get_rooms(self):
        return self.rooms

    def adjacent_rooms(self):
        adj = []
        cr = self.get_room()
        gx, gy = cr.grid_pos
        for r in self.rooms:
            ogx, ogy = r.grid_pos
            dx = ogx - gx
            dy = ogy - gy
            if sum((abs(dx), abs(dy))) == 1:
                adj.append(((dx, dy), r))

        return adj

    def setup(self, loader):
        for r in self.rooms:
            r.setup(loader)

            #print(r.room_type, r.grid_pos, r.needs_chest, r.needs_shopkeeper)

    def get_starting_room(self):
        for r in self.rooms:
            if r.room_type == "starting room":
                return r

    def modify(self, sheet, layout_mods, units):
        lm_mid_farm = {
            "shop room": ["shop1_farm", "shop2_farm", "shop3_farm", "shop4_farm", "shop5_farm", "shop6_farm"],
            "loot room": ["loot1_farm", "loot2_farm", "loot3_farm", "loot4_farm", "loot5_farm", "loot6_farm", "loot7_farm"],
            "rest room": ["rest2_farm", "rest3_farm", "rest4_farm", "rest5_farm", "rest6_farm"]
        }

        lm_mid_farm["empty room"] = ["empty_room1_farm"]

        lm_mid_trans = {
            0: lm_mid_farm,
            1: lm_mid_farm,
            2: lm_mid_farm,
            3: lm_mid_farm
        }

        lm_mid = lm_mid_trans[self.stage]

        empty = ["empty_room1_farm"]

        mid_trans = {
            "empty": "empty room",
            "shop": "shop room",
            "loot": "loot room",
            "rest": "rest room"
        }

        reordered_rooms = self.sequential_ordering()

        last_room = list(sorted(list(sheet.keys()), reverse = True))[0]

        ind = 0
        for r in sheet.keys():
            ref = sheet[r]["room_center"]
            spawn = list(map(lambda x: x.spawn_in_room, units))
            has_enemies = r in spawn
            room = reordered_rooms[ind]
            if has_enemies and r != "room 1":
                room.has_enemies = True
                n = spawn.count(r)
                boss_room = r == last_room
                if boss_room:
                    danger_rating = 3
                else:
                    if n >= 5:
                        danger_rating = 3
                    elif 2 < n <= 4:
                        danger_rating = 2
                    else:
                        danger_rating = 1
                room.danger_rating = danger_rating
            else:
                room.has_enemies = False
                room.danger_rating = 0
            if ref == "":
                continue
            trans = mid_trans[ref]
            room.remove_layout_mod()
            room.room_type = trans
            room.layout_mod = lm_mid[trans]
            rand_correct_lmod_name = choice(lm_mid[trans])
            lmod_path = layout_mods[rand_correct_lmod_name]
            room.layout_mod_path = lmod_path
            ind += 1

    def sequential_ordering(self):
        return self.rooms

    def get_sheet(self):
        return {}

    def pre_setup(self, loader):
        for r in self.rooms:
            r.pre_setup(loader)

    def post_setup(self, loader, sound, rw, rh, tw, th, lootmgr, weapons):
        for r in self.rooms:
            r.post_setup()

        self.rooms[0].has_been = True

        rating_trans = {
            0: {"common": 0.5, "rare": 0.3, "legendary": 0.2},
            1: {"common": 0.7, "rare": 0.2, "legendary": 0.1},
            2: {"common": 0.5, "rare": 0.3, "legendary": 0.2},
            3: {"common": 0.2, "rare": 0.3, "legendary": 0.5}
        }

        for r in self.rooms:
            if r.room_type == "loot room":
                r.needs_chest = True
            elif r.room_type == "shop room":
                r.needs_shopkeeper = True
            elif r.room_type == "rest room":
                r.needs_bed_logic = True

            for i in r.needs_doors:
                door = Door(r.layout_mods, r.tilesets, sound)
                door.room_pos = r.grid_pos
                door.belongs_to = r
                door.setup(i, loader)
                self.doors.append(door)
            
            if r.needs_chest:
                rating_chances = rating_trans[r.danger_rating]
                rating_rand = random()
                if rating_rand <= rating_chances["common"]:
                    rating = "common"
                elif rating_rand <= rating_chances["rare"]+rating_chances["common"]:
                    rating = "rare"
                else:
                    rating = "legendary"
                c = Chest(r, rw, rh, tw, th, sound, rating, lootmgr, weapons)
                self.chests.append(c)

            if r.needs_shopkeeper:
                rating = "common"
                discount = 0.9
                s = Shop(r, rw, rh, tw, th, sound, rating, lootmgr, weapons, discount)
                self.shopkeepers.append(s)

            if r.needs_bed_logic:
                b = Bed(r, rw, rh, sound)
                self.beds.append(b)


class Bed:
    def __init__(self, room, rw, rh, sound):
        self.room = room
        self.rw, self.rh = rw, rh

        self.pos = None, None
        self.set_pos()

        self.has_used = False
        self.done_resting = False
        self.sound = sound

        self.rest_timer = ActionTimer("", 2)

    def set_pos(self):
        cox, coy = 13, 4
        cw, ch = 6, 6

        room = self.room
        gx, gy = room.grid_pos
        ox, oy = gx * self.rw, gy * self.rh
        self.pos = ox + cox + cw//2 - 0.5, oy + coy + ch//2 - 0.5

    def close_to_bed(self, g_obj, mpos):
        return in_range(self.pos, g_obj.mc.pos, 2)

    def update(self, g_obj, mpos, mpress, ui, fighting):
        if fighting:
            return

        self.rest_timer.update()

        # if not fighting:
        #    return

        #if not self.open_timer.ticked:
        #    return

        #if not ui.get_selected() == None:
        #    return

        if self.has_used and self.rest_timer.ticked and not self.done_resting:
            self.done_resting = True
            g_obj.mc.labels.add_label("Rested", g_obj.mc.pos[0], g_obj.mc.pos[1], delay = 0)
            g_obj.mc.heal("percentage", 1, delay = 0.5)

        am = ui.at_mouse
        
        """
        m = am["mapped"]
        if self.check_mouseover(g_obj, mpos):
            if self.is_closed == True:
                self.is_closed = False
                self.sound.play_sound_now("door open")
            elif self.is_closed == False:
                self.is_closed = True
                self.sound.play_sound_now("door close")

            self.open_timer.reset()
        """
        m = am["mapped"]
        if self.close_to_bed(g_obj, mpos) and not self.has_used:
            g_obj.mc.current_bed = self
            g_obj.mc.state = "resting"
            self.sound.play_sound_now("rest")
            self.has_used = True
            self.rest_timer.reset()



class Chest:
    def __init__(self, room, rw, rh, tw, th, sound, rating, lootmgr, weapons):
        self.room = room
        self.sound = sound
        self.weapons = weapons

        self.rw, self.rh = rw, rh
        self.tw, self.th = tw, th

        self.rating = rating
        #print(self.rating)
        self.lootmgr = lootmgr
        
        self.loot_spawner = None

        self.pos = None, None
        self.place()

        self.frames = {
            "legendary": {"closed": 256, "spawning": 258, "spawned": 242},
            "rare": {"closed": 245, "spawning": 277, "spawned": 261},
            "common": {"closed": 244, "spawning": 276, "spawned": 260}
        }
        
        self.frame = None

        self.state = "closed"

    def place(self):
        cox, coy = 13, 4
        cw, ch = 6, 6
        center_positions = []
        for x, y in product(range(cw), range(ch)):
            centerp = cox + x, coy + y
            center_positions.append(centerp)

        shuffle(center_positions)

        # place units
        assigned_positions = []

        room = self.room
        #print(sroom.grid_pos)
        gx, gy = room.grid_pos
        ox, oy = gx * self.rw, gy * self.rh
        for i in range(len(center_positions)):
            randw, randh = center_positions.pop(0)
            new_pos = ox + randw, oy + randh
            walkable = room.walkable_map[randw][randh]
            if walkable and (self.pos == (None, None) or in_range(new_pos, self.pos, 3)):
                assigned_positions.append(new_pos)
                self.pos = assigned_positions[0]

        self.pos = assigned_positions.pop(0)
        self.available_spots = assigned_positions

    def update(self, mc, mpos, mpress, ui, fighting):
        if fighting:
            return
        if self.state == "closed":
            self.frame = self.frames[self.rating]["closed"]
            rad = 2
            if in_range(mc.pos, self.pos, rad):
                self.loot_spawner = self.lootmgr.new_spawner(self.pos, self.available_spots, \
                self.rating, self.sound, self.weapons)
                self.state = "opening"
                self.sound.play_sound_now("chest open")
        elif self.state == "opening":
            self.frame = self.frames[self.rating]["spawning"]
            if self.loot_spawner.done_spawning:
                self.state = "opened"
        elif self.state == "opened":
            self.frame = self.frames[self.rating]["spawned"]


class Shop:
    def __init__(self, room, rw, rh, tw, th, sound, rating, lootmgr, weapons, discount):
        self.room = room
        self.sound = sound
        self.weapons = weapons
        self.discount = discount

        self.rw, self.rh = rw, rh
        self.tw, self.th = tw, th

        self.rating = rating
        #print(self.rating)
        self.lootmgr = lootmgr
        
        self.loot_spawner = None

        self.pos = None, None
        self.place()
        
        self.frame = 400

        self.state = "closed"

    def place(self):
        cox, coy = 13, 4
        cw, ch = 6, 6
        center_positions = []
        for x, y in product(range(cw), range(ch)):
            centerp = cox + x, coy + y
            center_positions.append(centerp)

        shuffle(center_positions)

        # place units
        assigned_positions = []

        room = self.room
        #print(sroom.grid_pos)
        gx, gy = room.grid_pos
        ox, oy = gx * self.rw, gy * self.rh
        for i in range(len(center_positions)):
            randw, randh = center_positions.pop(0)
            new_pos = ox + randw, oy + randh
            walkable = room.walkable_map[randw][randh]
            if walkable and (self.pos == (None, None) or in_range(new_pos, self.pos, 3)):
                assigned_positions.append(new_pos)
                self.pos = assigned_positions[0]

        self.pos = assigned_positions.pop(0)
        self.available_spots = assigned_positions

    def update(self, mc, mpos, mpress, ui, fighting):
        if fighting:
            return
        rad = 2
        if self.state == "closed":

            if in_range(mc.pos, self.pos, rad):
                self.loot_spawner = self.lootmgr.new_spawner(self.pos, self.available_spots, \
                self.rating, self.sound, self.weapons, use_cost = True, discount = self.discount)
                self.state = "opening"
                self.sound.play_sound_now("blahblah")
        elif self.state == "opening":

            if self.loot_spawner.done_spawning:
                self.state = "opened"
        elif self.state == "opened":
            if not in_range(mc.pos, self.pos, rad):
                if self.sound.is_sound_playing("blahblah"):
                    self.sound.stop_sound_now("blahblah")
            else:
                if not self.sound.is_sound_playing("blahblah"):
                    self.sound.play_sound_now("blahblah")