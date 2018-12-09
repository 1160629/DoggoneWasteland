from numpy.random import choice as weighed_choice
from random import choice, shuffle, randint, random

from dungeon import Dungeon, Room

from logic import get_distance


def place_specials(dungeon):
    pass

# dungeon generation

def load_training_room(dungeon):
    return  # dungeon.rooms.append(room)


def make_a_room(layouts, tilesets):
    layout = choice(list(layouts.items()))
    r = Room(layout_path=layout[1], tilesets=tilesets)
    r.layout_name = layout[0]
    return r


def get_directions(cr, dl, con):
    nbs = (
        (0, 1),
        (1, 0),
        (0, -1),
        (-1, 0)
    )

    orients = {
        (0, 1): "south",
        (1, 0): "east",
        (0, -1): "north",
        (-1, 0): "west"
    }

    conx, cony = con

    gx, gy = cr.grid_pos

    ds = []

    for nb in nbs:
        px, py = gx + nb[0], gy + nb[1]
        if not (0 <= px < conx and 0 <= py < cony):
            continue

        if dl[px][py] != None:
            continue

        orient = orients[(nb[0], nb[1])]

        d = (px, py), orient

        ds.append(d)

    return ds


def generate_dungeon(layouts_, layout_mods, tilesets, rw, rh, stage = None, constraints = None):
    if stage == None:
        stage = 0

    if constraints == None:
        constraints = {"total_rooms": 8, "max_walk_connections": 4, "start_max_walk": 3, "end_max_walk": 1}

    stages = {
        "Farmhouse": 0,
        "Bubbas Basement": 1,
        "The Cave": 2,
        "Trailer Park": 3
    }

    rstages = {j: k for k, j in stages.items()}

    stage_name = rstages[stage]

    shortcuts = {
        "Farmhouse": "farm",
        "Bubbas Basement": "bubbas",
        "The Cave": "cave",
        "Trailer Park": "park"
    }

    short = shortcuts[stage_name]

    l0 = [
        "Sandra's Farmhouse Room 1",
        "Sandra's Farmhouse Room 2",
        "Sandra's Farmhouse Room 3",
        "Sandra's Farmhouse Room 4",
        "Sandra's Farmhouse Room 5",
        "Sandra's Farmhouse Room 6",
        "Sandra's Farmhouse Room 7",
        "Sandra's Farmhouse Room 8",
        "Sandra's Farmhouse Room 9",
        "Sandra's Farmhouse Room 10",
        "Sandra's Farmhouse Room 11",
        "Test Farmhouse Room 1",
        "Test Farmhouse Room 2",
        "Test Farmhouse Room 3"
    ]

    l1 = [

    ]
    l1 = l0

    l2 = [

    ]
    l2 = l0

    l3 = [

    ]
    l3 = l0

    layouts_belonging = l0, l1, l2, l3

    layouts_old = layouts_
    layouts = {k: layouts_[k] for k in layouts_belonging[stage]}

    lm_halls_ = {
        "west": "hallway_left",
        "east": "hallway_right",
        "north": "hallway_up",
        "south": "hallway_down"
    }

    lm_halls = {}
    for k, i in lm_halls_.items():
        new_entry = None
        for kj, ij in layout_mods.items():
            if (i in kj) and (short in kj):
                new_entry = kj
                break
        lm_halls[k] = new_entry

    # this right here is just a token placeholder
    # intended for 
    # actual visual changes can be made in tiled
    # there still needs to be logic applied to all 
    # of these wherever the rooms are actually "setup"
    # i.e. loot rooms w/ chest should place a chest
    # that actually keeps track of a chest() object
    # and shop rooms should load a shopkeeper unit
    # and place him in the middle
    # and rest rooms should load the bed

    # this is just for additional visual variation
    lm_mid_farm = {
        "shop room": ["shop1_farm", "shop2_farm", "shop3_farm", "shop4_farm", "shop5_farm", "shop6_farm"],
        "loot room": ["loot1_farm", "loot2_farm", "loot3_farm", "loot4_farm", "loot5_farm", "loot6_farm", "loot7_farm"],
        "rest room": ["rest2_farm", "rest3_farm", "rest4_farm", "rest5_farm", "rest6_farm"]
    }

    lm_mid_trans = {
        0: lm_mid_farm,
        1: lm_mid_farm,
        2: lm_mid_farm,
        3: lm_mid_farm
    }

    lm_mid = lm_mid_trans[stage]

    # note: all enemy rooms should have a chest
    # i.e. be loot rooms
    # at least, probably?
    # make it like this; if it IS a loot room, then 
    # theres a 90% chance it also has enemies

    # the following are potential room types:

    room_types = [
        "starting room",
        "loot room",
        "rest room",
        "shop room",
        "boss room"
    ]

    starting_room = None

    # create rooms & path

    con = conx, cony = 7, 7
    sx, sy = 3, 6

    gen_rooms = constraints["total_rooms"]

    dung_list = [[None for y in range(cony)] for x in range(conx)]

    x, y = sx, sy

    start_room = make_a_room(layouts, tilesets)
    start_room.grid_pos = x, y
    # start_room.room_id = 0

    pp = [start_room]
    dung_list[x][y] = start_room
    ar = []

    rn = 0
    while rn <= gen_rooms - 1:
        # shuffle list of potential rooms
        shuffle(pp)
        # and grab one
        cr = pp.pop(0)

        cr.layout_mods = layout_mods

        # set room id
        cr.room_id = rn
        # increment room number variable
        rn = rn + 1

        # decide room type (shop, loot, rest)
        rt_sub = room_types[1:4]
        # 80% loot/enemy, 10 % shops, 10% rest
        pdist = [0.8, 0.1, 0.1]
        rt_choice = weighed_choice([i for i in range(len(rt_sub))], p=pdist)
        rt = rt_sub[rt_choice]
        cr.room_type = rt

        # if it's a loot room, then it has a 90% chance of have enemies
        if rt == "loot room" and random() >= 0.1:
            cr.has_enemies = True
        else:
            cr.has_enemies = False

        # danger rating
        if cr.has_enemies == True:
            cr.danger_rating = choice((1, 2, 3))
        else:
            cr.danger_rating = 0

        # decide layout mod
        lm = choice(lm_mid[rt])
        cr.layout_mod = lm
        cr.layout_mod_path = layout_mods[lm]

        # add room to actual rooms in dungeon
        ar.append(cr)

        # now branch out and find new potential rooms
        ds = get_directions(cr, dung_list, con)
        shuffle(ds)
        nds = len(ds)
        if nds == 0:
            go_n = 0
        elif nds == 1:
            go_n = 1
        else:
            go_n = randint(1, nds)
        already_connected = cr.get_n_connections()
        if len(ar) == 1:
            go_n = min(go_n, constraints["start_max_walk"]-already_connected)
        elif len(ar) == gen_rooms:
            go_n = min(go_n, constraints["end_max_walk"]-already_connected)
        else:
            go_n = min(go_n, constraints["max_walk_connections"]-already_connected)
        for i in range(go_n):

            ads = ds.pop(0)
            nr = make_a_room(layouts, tilesets)
            nr.grid_pos = ads[0]
            orient = ads[1]
            sindx = sindy = None
            if orient in ("north", "south"):
                room_placement_range = 2, 26
                sindx = randint(*room_placement_range)
            elif orient in ("east", "west"):
                room_placement_range = 3, 7
                sindy = randint(*room_placement_range)
            if orient == "north":
                cr.north = nr
                tc = lm_halls["north"]
                cr.connectors["north"] = (tc, layout_mods[tc], sindx)
                nr.south = cr
                nr.connectors["south"] = (tc, layout_mods[tc], sindx)
            elif orient == "south":
                cr.south = nr
                tc = lm_halls["south"]
                cr.connectors["south"] = (tc, layout_mods[tc], sindx)
                nr.north = cr
                nr.connectors["north"] = (tc, layout_mods[tc], sindx)
            elif orient == "east":
                cr.east = nr
                tc = lm_halls["east"]
                cr.connectors["east"] = (tc, layout_mods[tc], sindy)
                nr.west = cr
                nr.connectors["west"] = (tc, layout_mods[tc], sindy)
            elif orient == "west":
                cr.west = nr
                tc = lm_halls["west"]
                cr.connectors["west"] = (tc, layout_mods[tc], sindy)
                nr.east = cr
                nr.connectors["east"] = (tc, layout_mods[tc], sindy)
            dung_list[ads[0][0]][ads[0][1]] = nr

            pp.append(nr)

        if len(pp) == 0:
            for r in ar:
                ds = get_directions(r, dung_list, con)
                shuffle(ds)
                if len(ds) == 0:
                    continue

                while len(ds) > 0:
                    ads = ds.pop(0)
                    nr = make_a_room(layouts, tilesets)
                    nr.grid_pos = ads[0]
                    orient = ads[1]
                    sindx = sindy = None
                    if orient in ("north", "south"):
                        room_placement_range = 2, 26
                        sindx = randint(*room_placement_range)
                    elif orient in ("east", "west"):
                        room_placement_range = 3, 7
                        sindy = randint(*room_placement_range)
                    if orient == "north":
                        r.north = nr
                        tc = lm_halls["north"]
                        r.connectors["north"] = (tc, layout_mods[tc], sindx)
                        nr.south = r
                        nr.connectors["south"] = (tc, layout_mods[tc], sindx)
                    elif orient == "south":
                        r.south = nr
                        tc = lm_halls["south"]
                        r.connectors["south"] = (tc, layout_mods[tc], sindx)
                        nr.north = r
                        nr.connectors["north"] = (tc, layout_mods[tc], sindx)
                    elif orient == "east":
                        r.east = nr
                        tc = lm_halls["east"]
                        r.connectors["east"] = (tc, layout_mods[tc], sindy)
                        nr.west = r
                        nr.connectors["west"] = (tc, layout_mods[tc], sindy)
                    elif orient == "west":
                        r.west = nr
                        tc = lm_halls["west"]
                        r.connectors["west"] = (tc, layout_mods[tc], sindy)
                        nr.east = r
                        r.connectors["east"] = (tc, layout_mods[tc], sindy)
                    dung_list[ads[0][0]][ads[0][1]] = nr

                    pp.append(nr)

                break

    # remove "connections" to unused rooms
    for r in ar:
        if r.north not in ar:
            r.north = None
            if "north" in r.connectors.keys():
                del r.connectors["north"]
        if r.south not in ar:
            r.south = None
            if "south" in r.connectors.keys():
                del r.connectors["south"]
        if r.east not in ar:
            r.east = None
            if "east" in r.connectors.keys():
                del r.connectors["east"]
        if r.west not in ar:
            r.west = None
            if "west" in r.connectors.keys():
                del r.connectors["west"]

    dung = Dungeon()

    # set the dungeons rooms to the actual rooms
    dung.rooms = ar

    # set starting room
    dung.in_room = 0
    dung.rooms[0].room_type = "starting room"
    dung.rooms[0].has_enemies = False
    dung.rooms[0].unexplored = False
    dung.rooms[0].remove_layout_mod()
    dung.rooms[0].add_layout_mod("empty room", layout_mods["empty_room1_farm"])

    # set boss room
    # i.e. the room furthest away from starting room
    # using euclidian distance
    # and checking only the ones that have just one
    # connection
    # i.e. boss room = furthest room away in raw distance, which is also an end room
    end_rooms = []
    for r in ar:
        l = r.north, r.south, r.west, r.east
        n_conns = 4 - sum(1 for i in l if i == None)
        if n_conns == 1:
            end_rooms.append(r)

    gdist = 0
    froom = dung.rooms[0]

    rhw, rhh = 32 / 2, 14 / 2
    gfr = dung.rooms[0]
    p1x, p1y = gfr.grid_pos
    p1 = p1x + rhw, p1y + rhh

    if len(end_rooms) == 0:
        p_boss_rooms = ar
    else:
        p_boss_rooms = end_rooms

    for er in p_boss_rooms:
        p2x, p2y = er.grid_pos
        p2 = p2x + rhw, p2y + rhh
        d = get_distance(p1, p2)
        if d > gdist:
            gdist = d
            froom = er

    froom.room_type = "boss room"
    froom.layout_name = "Farmhouse Boss Room"
    froom.layout_path = layouts_old["Farmhouse Boss Room"]
    froom.has_boss = True
    froom.has_enemies = False
    froom.danger_rating = 3
    froom.remove_layout_mod()

    dung.stage = stage
    dung.stage_name = stage_name

    dung.rw, dung.rh = rw, rh

    return dung
