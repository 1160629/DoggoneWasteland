import pygame
import json
import xmltodict
from itertools import product
from control import ActionTimer
from logic import Rect, in_range


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

    def get_door_positions(self):
        pass

    def add_layout_mod(self, lm, lmp):
        self.layout_mod = lm
        self.layout_mod_path = lmp

    def remove_layout_mod(self):
        self.layout_mod = None
        self.layout_mod_path = None

    def setup(self, loader):
        self.layout = loader(self.layout_path, self.tilesets)

        if self.layout_mod != None:
            self.setup_layout_mod(loader)

        self.create_hallways(loader)

        self.walkable_map = self.walkable_map = create_room_walkable_map(self)

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

def check_door_mouseover(self, door, m):
    dung = self.dungeon
    doors = dung.doors

    d = door
    lout = d.get_layout()
    bx, by = d.pos
    ox, oy = d.get_off()
    roomx, roomy = d.room_pos
    tsw, tsh = d.get_ts_size()
    direction = door.direction
    return check_door_mouseover_tbt(self, lout, bx, by, roomx, roomy, ox, oy, tsw, tsh, m, direction)


def check_door_mouseover_tbt(self, lout, bx, by, roomx, roomy, ox, oy, tsw, tsh, m, direction):
    if direction == "east":
        range_mod = 2
    else:
        range_mod = 1

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

    if any(mover) and any(inrange):
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
            if self.direction in ("north", "south") and \
                    (y == 0):
                continue
            rx = -ox + px + x
            ry = -oy + py + y
            real = rx, ry
            reals.append(real)
        return reals

    def check_mouseover(self, g_obj, m):
        return check_door_mouseover(g_obj, self, m)
        # return False

    def update(self, g_obj, mpos, mpress, ui, fighting):
        self.open_timer.update()

        if not mpress[0]:
            return

        # if not fighting:
        # return

        if not self.open_timer.ticked:
            return

        if ui.get_selected() != None:
            return

        am = ui.at_mouse

        m = am["mapped"]
        if self.check_mouseover(g_obj, mpos):
            if self.is_closed == True:
                self.is_closed = False
                self.sound.play_sound_now("door open")
            elif self.is_closed == False:
                self.is_closed = True
                self.sound.play_sound_now("door close")

            self.open_timer.reset()


class Dungeon:
    def __init__(self):
        self.rooms = []
        self.hallways = []

        self.doors = []

        self.in_room = 0

    def update(self, mc_pos, g_obj, mpos, mpress, ui, fighting):
        mcx, mcy = mc_pos
        px, py = mcx // g_obj.rw, mcy // g_obj.rh
        ind = 0
        for r in self.rooms:
            gx, gy = r.grid_pos
            if (gx, gy) == (px, py):
                self.in_room = ind
                break
            ind += 1

        gr = self.get_room()
        if not gr.has_been:
            gr.has_been = True
            g_obj.mc.get_xp(1)

        for d in self.doors:
            d.update(g_obj, mpos, mpress, ui, fighting)

        inside = self.get_room()
        rt = inside.room_type
        if rt == "rest room":  # so if mouse pointer is pressed on bed, and you've not previously rested
            pass  # then "rest" for 3 seconds (becoming immobile), animated sideways on the bed, healing fully
        elif rt == "loot room":
            pass  # if mouse pointer is pressed on chest not during combat, then change the chest animation to
            # one that is open with loot, and create a loot spawner at chest location. once finished spawning
            # make the chest animation empty
        elif rt == "shop room":
            pass  # here just draw a shopkeep character that is always idle, never does anything
            # he is also invincible? (or really strong)
            # to buy an item just pick it up like any other item from a chest, except these
            # subract a certain amount from your bullets currency, if u dont have enough, u
            # cant pick it up

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

    def setup_rooms(self, loader, sound):
        for r in self.rooms:
            r.setup(loader)

        for r in self.rooms:
            for i in r.needs_doors:
                door = Door(r.layout_mods, r.tilesets, sound)
                door.room_pos = r.grid_pos
                door.belongs_to = r
                door.setup(i, loader)
                self.doors.append(door)

    def get_starting_room(self):
        for r in self.rooms:
            if r.room_type == "starting room":
                return r


class Bed:
    def __init__(self):
        self.pos = []

    def update(self):
        pass
