from random import choice
from logic import in_range, create_walkable_matrix, get_distance, one_tile_range
from equipment import get_weapon_range
from itertools import product
from control import ActionTimer

def get_units_list_at(units_, at):
    units = []
    for rad in range(1, 8):
        units.append([])
        for u in units_:
            if in_range(u.pos, at, rad):
                units[-1].append(u)
    
    return units

def get_walkable_pos(epos, unit, g_obj, eval_func):
    upos = unit.pos

    room = g_obj.dungeon.get_room()
    walk_mat = create_walkable_matrix(room, g_obj.units, unit, g_obj)

    rwalkmat = room.walkable_map

    rw, rh = g_obj.rw, g_obj.rh
    sx, sy = rw, rh
    ex, ey = sx+rw, sy+rh

    gx, gy = room.grid_pos

    avail_pos = []
    for x, y in product(range(sx, ex), range(sy, ey)):
        if walk_mat[x][y] == True:
            rpos = x-rw+gx*rw, y-rh+gy*rh
            for u in g_obj.units:
                if u == unit:
                    continue
                if u.pos == rpos:
                    break
            else:
                avail_pos.append(rpos)

    walk_to = avail_pos[0]
    dist = get_distance(avail_pos[0], epos)
    for ap in avail_pos:
        d = get_distance(ap, epos)
        if ap == epos:
            continue
        elif eval_func == min and d < dist:
            dist = d
            walk_to = ap
        elif eval_func == max and d > dist:
            dist = d
            walk_to = ap

    #print(unit.pos, epos, walk_to)

    return walk_to

def get_available_abis(unit, c_ap, abi_types):
    potential = []
    for a in unit.memory.get_abilities():
        if a.cooldown.cooldown == 0 and a.ap_cost <= c_ap:
            potential.append(a)

    actual = []
    for p in potential:
        if p.category in abi_types:
            actual.append(p)

    #print("AVAIL ABIS", actual)

    #return actual
    return []

def get_max_range_of(unit):
    ranges = []

    atkw = unit.attack_weapon
    unit.attack_weapon = None

    u_range = unit.get_range()

    weapons = unit.equipment.hand_one, unit.equipment.hand_two
    for w in weapons:
        if w == None:
            continue

        r = get_weapon_range(w) + u_range
        ranges.append(r)

    for a in unit.memory.get_abilities():
        r = a.ability_range + u_range
        #ranges.append(r)

    unit.attack_weapon = atkw

    if len(ranges) == 0:
        return 0

    mrange = max(ranges)
    if mrange == 1:
        one_tile_range
        
    return mrange

def get_in_range_abis(a_abis, unit, epos):
    abis = []

    atkw = unit.attack_weapon
    unit.attack_weapon = None

    u_range = unit.get_range()

    for a in unit.memory.get_abilities():
        r = a.ability_range + u_range
        if in_range(unit.pos, epos, r):
            abis.append(a)

    unit.attack_weapon = atkw

    #return abis
    return []

def get_in_range_atks(unit, epos):
    ranges = []
    weps = []

    atkw = unit.attack_weapon
    unit.attack_weapon = None

    u_range = unit.get_range()

    weapons = unit.equipment.hand_one, unit.equipment.hand_two
    for w in weapons:
        if w == None:
            continue

        r = get_weapon_range(w) + u_range
        weps.append(w)
        ranges.append(r)

    can_swing_with = []
    for w, r in zip(weps, ranges):
        if w.weapon_class == "Brawler":
            real_range = one_tile_range
        else:
            real_range = r

        if in_range(unit.pos, epos, real_range):
            can_swing_with.append(w)

    unit.attack_weapon = atkw

    return can_swing_with

class Controller:
    def __init__(self):
        self.state = "idling"
        self.last_action = "wait"

        self.last_dest_pos = None

        self.action_delay = ActionTimer("", 0.05)

        self.controller_type = None

        self.unit = None

        self.spot_range = 15

        self.con_act = {"do": "nothing"}
        self.l_con_act = None
        self.l_move_con_act = None

    def action(self, c_ap, c_hp_self, m_hp_self, c_pos_enemy, c_hp_enemy, u_state, c_state, l_action, c_type):
        if u_state in ("dying", "dead") or u_state != "idle":
            return "wait", c_state, {}

        flee_per = 0.3
        if c_hp_self / m_hp_self < flee_per:
            c_state = "fleeing"
        else:
            pass

        if c_ap < 1 and c_state != "fleeing":
            return "pass", c_state, {}

        if c_state == "fleeing":
            available_abis = get_available_abis(self.unit, c_ap, ["heal", "buff"]) # returns a list of cast-able abilities
            if len(available_abis) == 0:
                return "walk", c_state, {"walk_command": "away_from_enemy"}
            else:
                abi_choice = choice(available_abis)
                return "cast", c_state, {"cast_ability": abi_choice}
            pass # check if we have heal/buff available, then go into that state
            # otherwise stay in this state and keep running away.
        
        elif c_state == "idling":
            if in_range(self.unit.pos, c_pos_enemy, self.spot_range):
                c_state = "approaching"
                return "wait", c_state, {}
            else:
                return "pass", c_state, {}
            pass # check if enemy is within range, if so- go out of idle state.

        elif c_state == "approaching":
            cur_max_range_self = get_max_range_of(self.unit)
            if in_range(self.unit.pos, c_pos_enemy, cur_max_range_self):
                c_state = "attacking"
                return "wait", c_state, {}
            else:
                return "walk", c_state, {"walk_command": "toward_enemy"}
            pass # if you're too far away from enemy to attack - approach; walk toward
            # otherwise; go into attack state.

        elif c_state == "kiting":
            pass # if you're ranged and your range is greater than the enemies, then
            # move a little back, otherwise go into a state of attacking.

        elif c_state == "attacking":
            available_abis = get_available_abis(self.unit, c_ap, ["ranged", "melee"])
            in_range_abis = get_in_range_abis(available_abis, self.unit, c_pos_enemy)
            in_range_attacks = get_in_range_atks(self.unit, c_pos_enemy)

            if len(in_range_abis) != 0 and False: # ignore abilites for now
                use_abi = choice(in_range_abis)
                return "cast", c_state, {"use_ability": use_abi}
            elif len(in_range_attacks) != 0:
                use_weapon = choice(in_range_attacks)
                return "smack", c_state, {"use_weapon": use_weapon}
            else:
                c_state = "approaching"
                return "wait", c_state, {}
            pass # here we can use a ranged or melee ability, or ranged or melee basic attack.

        return "wait", c_state, {}

    def update(self, g_obj, mc, mpos, mpress, ui, fighting):
        self.action_delay.update()
        
        con_act = {"do": "nothing"}

        if self.unit.end_turn == True:
            return 
        elif self.action_delay.ticked:
            c_ap = self.unit.ap.get_ap()
            m_hp_self = self.unit.get_health()
            dmg = self.unit.damage_taken
            c_hp_self = m_hp_self - dmg
            c_hp_enemy = mc.get_health()
            u_state = self.unit.state
            c_state = self.state
            l_action = self.last_action
            c_type = self.controller_type
            c_pos_enemy = mc.pos
            action, c_state, commands = self.action(c_ap, c_hp_self, m_hp_self, c_pos_enemy, \
                c_hp_enemy, u_state, c_state, l_action, c_type)

            self.state = c_state
            self.l_action = action

            if action == "pass":
                self.unit.end_turn = True
            elif action == "wait":
                pass
            elif action == "walk":
                con_act["do"] = "walk"
                w_comm = commands["walk_command"]
                if w_comm == "away_from_enemy":
                    dest_pos = get_walkable_pos(mc.pos, self.unit, g_obj, eval_func = max)
                elif w_comm == "toward_enemy":
                    dest_pos = get_walkable_pos(mc.pos, self.unit, g_obj, eval_func = min)
                con_act["dest"] = dest_pos
                #self.state = "attacking"
                if dest_pos == self.last_dest_pos and w_comm == "away_from_enemy":
                    self.unit.end_turn = True
                    #self.con_act = {"do": "nothing"}
                self.last_dest_pos = dest_pos
                self.action_delay.reset()
                self.l_move_con_act = con_act
            elif action == "cast":
                pass
            elif action == "smack":
                con_act["do"] = "smack"
                weapon = commands["use_weapon"]
                dest_pos = c_pos_enemy
                con_act["dest"] = dest_pos
                con_act["weapon"] = weapon
                con_act["at_mouse"] = {}
                con_act["at_mouse"]["unit"] = mc
                con_act["at_mouse"]["units"] = get_units_list_at(g_obj.units, dest_pos)
                con_act["at_mouse"]["mapped"] = dest_pos
                self.action_delay.reset()

            self.con_act = con_act

        else:
            self.con_act = {"do": "nothing"}
            



            

# 5 action types
# smack; use attack - ranged / melee; depending on its weapon, range to enemy, and cds, it will try to attack
# cast; use ability (4 ability categories)
# - heal
# - buff
# - ranged
# - melee
# walk; move somewhere, either toward player (melee attack / ranged attack but too far) or away from player (kiting / fleeing)
# wait; wait until unit finishes its' current action, or enemy is in sight
# pass; end turn

# state types
# idle
# approaching
# kiting
# attacking
# heal/buff
# fleeing