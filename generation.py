from numpy.random import choice as weighed_choice
from random import choice, shuffle, randint, random

from equipment import *
from effects import *

from units import MC, Sneak, Zombie, Mage, RedDevil, Tiny

import abilities

from dungeon import Dungeon, Room

from logic import get_distance


# weapon generation

class Mod:
    def __init__(self):
        self.name = None
        self.tier = None

        self.mclass = None
        self.value = None


def make_mod(weapon, tier3_guarantee=False):
    # this first dict just maps out the values of our GDD mod matrix
    mod_dict = {
        "crit": {
            "tier 1": 0.05,
            "tier 2": 0.1,
            "tier 3": 0.2
        },
        "range": {
            "tier 1": 1,
            "tier 2": 2,
            "tier 3": 3
        },
        "burn": {
            "tier 1": 0.05,
            "tier 2": 0.1,
            "tier 3": 0.2
        },
        "blind": {
            "tier 1": 0.02,
            "tier 2": 0.05,
            "tier 3": 0.1
        },
        "cripple": {
            "tier 1": 0.02,
            "tier 2": 0.05,
            "tier 3": 0.1
        },
        "knock": {
            "tier 1": 0.02,
            "tier 2": 0.04,
            "tier 3": 0.08
        }
    }

    # this just specifies the likelyhood of a certain mod. i.e. the AP mod once implemented, should be less 
    # likely to occur, since it is very powerful
    mod_type_likelyhood = {
        "crit": "regular",
        "range": "regular",
        "burn": "regular",
        "blind": "regular",
        "cripple": "half",
        "knock": "regular"
    }

    # all mods are defined by a class
    # any combat effects can then be instantiated when assigned
    # this is just how i did it; maybe not ideal
    burning_mod_class = gen_effect_mod(Burning, 3)
    blind_mod_class = gen_effect_mod(Blinded, 2)
    slowed_mod_class = gen_effect_mod(Slowed, 2)
    knocked_mod_class = gen_effect_mod(Knocked, 2)

    # just mapping classes to effect names
    mod_bonus_dict = {
        "burn": burning_mod_class,
        "blind": blind_mod_class,
        "cripple": slowed_mod_class,
        "knock": knocked_mod_class,
        "crit": None,  # these have no class, since they are just a value to be added
        "range": None  # again; no class, just a value you add to a stat
    }

    # here is where i select the mod
    # by first creating a probability distribution based on the "mod_type_likelyhood" dictionary
    mdkeys = mod_dict.keys()
    pdist1_ = [[1, 0.5][mod_type_likelyhood[k] != "regular"] for k in mdkeys]
    s = sum(pdist1_)
    pdist1 = [i / s for i in pdist1_]

    # here i select the tier of the mod, with a weighed distribution
    # it can be overriden to guarantee a tier 3 mod (useful in the case of creating a legendary weapon)
    mod_name = list(mdkeys)[weighed_choice(list(i for i in range(len(mdkeys))), p=pdist1)]
    if not tier3_guarantee:
        pdist2 = [0.6, 0.3, 0.1]
        mod_tier = ["tier 1", "tier 2", "tier 3"][weighed_choice(list((0, 1, 2)), p=pdist2)]
    else:
        mod_tier = "tier 3"
    mod_value = mod_dict[mod_name][mod_tier]

    # instantiate the mod, assign values
    mc = Mod()
    mc.name = mod_name
    mc.tier = mod_tier
    mc.value = mod_value
    mc.mclass = mod_bonus_dict[mod_name]

    # add to weapon
    weapon.mods.append(mc)


def create_weapon(rarity, quality, weapon):
    # from the GDD; a legendary has 4-5 mods, rare has 1-3, and common has none
    n_mods_dict = {
        "legendary": choice((4, 5)),
        "rare": choice((1, 2, 3)),
        "common": 0
    }
    n_mods = n_mods_dict[rarity]

    quality_multipliers = {
        "good": 1.5,
        "crappy": 0.5,
        "regular": 1
    }

    # make mods
    for m in range(n_mods):
        make_mod(weapon)

    # when its legendary, ensure that it gets at least two tier 3 mods.
    if rarity == "legendary":
        tier3_count = 0
        for m in weapon.mods:
            if m.tier == "tier 3":
                tier3_count += 1

        while tier3_count < 2:
            make_mod(weapon, tier3_guarantee=True)
            i = 0
            for m in weapon.mods:
                if m.tier != "tier 3":
                    kill_me = i
                    break
                i += 1
            weapon.mods.pop(kill_me)
            tier3_count += 1

    # assign weapon quality
    multiplier = quality_multipliers[quality]
    weapon.quality = quality
    weapon.quality_multiplier = multiplier

    # finito!
    return weapon


# unit generation

# this one is for 
def place_starting_units(weapons, labels, animations, dung, rw, rh, sound):
    units = []

    sroom = dung.get_starting_room()
    gx, gy = sroom.grid_pos
    # tw, th = 32, 32
    # raw, rah = tw * rw, th * rh
    ox, oy = gx * rw, gy * rh

    # main character - you
    mc = MC(sound, labels)
    mc.set_pos((2, 2))
    mc.equipment.hand_one = create_weapon("rare", "good", get_new_weapon_instance("Colt", weapons))
    mc.equipment.hand_two = create_weapon("legendary", "good", get_new_weapon_instance("Bat", weapons))

    abi = abilities.FirstAidKit()
    abi.connected_ui_slot = "ability 1"
    mc.memory.learn(abi)
    abi2 = abilities.HolyHandGrenade()
    abi2.connected_ui_slot = "ability 2"
    mc.memory.learn(abi2)

    units.append(mc)

    # other units - also controlled by you, currently
    units.append(Zombie(sound, labels, pos=(15, 6)))
    units.append(Sneak(sound, labels, pos=(15, 7)))
    units.append(Sneak(sound, labels, pos=(15, 8)))
    units.append(Mage(sound, labels, pos=(24, 4)))

    # place units
    assigned_positions = []
    for u in units:
        while True:
            randw, randh = randint(1, rw - 1), randint(2, rh - 2)
            new_pos = ox + randw, oy + randh
            walkable = sroom.walkable_map[randw][randh]
            if walkable and new_pos not in assigned_positions:
                break
        assigned_positions.append(new_pos)
        u.set_pos(new_pos)

    # assign animations
    for u in units:
        name = u.anim_name
        u.animations = animations.new_animation_set_instance(name)

    return mc, units


# gear generation


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


def generate_dungeon(layouts_, layout_mods, tilesets, rw, rh, stage=None):
    if stage == None:
        stage = 0

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

    l2 = [

    ]

    l3 = [

    ]

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
    lm_mid = {
        "shop room": ["shop1_farm", "shop2_farm", "shop3_farm", "shop4_farm", "shop5_farm", "shop6_farm"],
        "loot room": ["loot1_farm", "loot2_farm", "loot3_farm", "loot4_farm", "loot5_farm", "loot6_farm", "loot7_farm"],
        "rest room": ["rest2_farm", "rest3_farm", "rest4_farm", "rest5_farm", "rest6_farm"]
    }

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

    gen_rooms = 8

    dung_list = [[None for y in range(cony)] for x in range(conx)]

    x, y = sx, sy

    start_room = make_a_room(layouts, tilesets)
    start_room.grid_pos = x, y
    # start_room.room_id = 0

    pp = [start_room]
    dung_list[x][y] = start_room
    ar = []

    rn = 0
    while rn <= gen_rooms:
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

    return dung
