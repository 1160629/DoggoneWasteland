from numpy.random import choice as weighed_choice
from random import choice, shuffle, randint, random

from units import *

# unit generation

def make_enemy(enemy, enemy_archetype, enemy_controller, specifics, weapons):
    e = enemy()

    for k, s in specifics.items():
        if k == "health":
            e.base_health = s

    if enemy_controller == None:
        e.has_controller = False
        e.controller_name = None
    else:
        e.has_controller = True
        e.controller_name = enemy_controller

    # use skill tree to assign skills, stats, mutations
    # and give them weapons, shields, gear 
    # according to archetype
    if enemy_archetype == "rocketeer":
        pass
    elif enemy_archetype == "gunslinger":
        pass
    elif enemy_archetype == "fighter":
        pass
    elif enemy_archetype == "tank":
        pass
    elif enemy_archetype == "basic melee":
        pass
    elif enemy_archetype == "basic range":
        pass

    return e

def assign_unit_stuff(units, labels, sound, animations):
    # assign pertinent objects
    for u in units:
        u.labels = labels
        u.sound = sound

    # assign animations
    for u in units:
        name = u.anim_name
        u.animations = animations.new_animation_set_instance(name)

def setup_mc():
    mc = MC()
    mc.spawn_in_room = "room 1"

    return mc

def setup_enemies(weapons, setup_sheet):
    enemies = []

    name2class = {
        "Zombie": Zombie,
        "Sneak": Sneak,
        "Mage": Mage,
        "RedDevil": RedDevil,
        "Tiny": Tiny,
        "Gramps": Gramps
    }

    for r in setup_sheet.keys():
        for entry in setup_sheet[r]["enemies"]:
            if entry == []:
                continue
            #print(entry)
            class_name, arch, con, specifics = entry
            c = name2class[class_name]
            e = make_enemy(c, arch, con, specifics, weapons)
            enemies.append(e)
            e.spawn_in_room = r

    return enemies

def place_units(dungeon, rw, rh, units):

    cox, coy = 13, 4
    cw, ch = 6, 6
    center_positions = []
    for x, y in product(range(cw), range(ch)):
        centerp = cox + x, coy + y
        center_positions.append(centerp)

    # other units - also controlled by you, currently

    # place units
    assigned_positions = []
    for u in units:
        ind = int(u.spawn_in_room.split(" ")[1]) - 1
        room = dungeon.get_rooms()[ind]
        #print(sroom.grid_pos)
        gx, gy = room.grid_pos
        ox, oy = gx * rw, gy * rh
        while True:
            randw, randh = randint(1, rw - 1), randint(2, rh - 2)
            new_pos = ox + randw, oy + randh
            walkable = room.walkable_map[randw][randh]
            if walkable and new_pos not in assigned_positions and (randw, randh) not in center_positions:
                break
        assigned_positions.append(new_pos)
        u.set_pos(new_pos)


def setup_units(dungeon, rw, rh, setup_sheet, weapons, labels, sound, animations):
    if setup_sheet == None:
        setup_sheet = dungeon.get_setup_sheet()

    mc = setup_mc()

    from abilities import TeleportAnywhere
    abi = TeleportAnywhere()
    abi.connected_ui_slot = "ability 5"
    mc.memory.learn(abi)

    enemies = setup_enemies(weapons, setup_sheet)

    units = [mc] + enemies
    assign_unit_stuff(units, labels, sound, animations)

    place_units(dungeon, rw, rh, units)

    return mc, units
