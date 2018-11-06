import pygame
import threading
import json
import xmltodict
import random
from numpy.random import choice as weighed_choice
import itertools
import time
import math


# from https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread
class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, target = None):
        super(StoppableThread, self).__init__(target=target)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


# pathfinding

def reconstruct_path(cameFrom, current):
    total_path = [current]
    while current in cameFrom.keys():
        current = cameFrom[current]
        total_path.append(current)
    return total_path

def lowest_fscore_value(fScore, openSet):
    lowest = openSet[0]
    for n in openSet:
        if fScore[n] < fScore[lowest]:
            lowest = n
    #print(lowest.pos)
    return lowest

def heuristic_cost_estimate(n1, n2):
    cost = dist_between(n1, n2)
    return cost

def dist_between(n1, n2):
    x1, y1 = n1.pos 
    x2, y2 = n2.pos

    dsq = (x1-x2)**2 + (y1-y2)**2
    return dsq

def A_Star(start, goal):
    #// The set of nodes already evaluated
    closedSet = {}

    discovered = {}

    #// The set of currently discovered nodes that are not evaluated yet.
    #// Initially, only the start node is known.
    openSet = [start]

    #// For each node, which node it can most efficiently be reached from.
    #// If a node can be reached from many nodes, cameFrom will eventually contain the
    #// most efficient previous step.
    cameFrom = {}

    #// For each node, the cost of getting from the start node to that node.
    gScore = {}

    #// The cost of going from start to start is zero.
    gScore[start] = 0

    #// For each node, the total cost of getting from the start node to the goal
    #// by passing by that node. That value is partly known, partly heuristic.
    fScore = {}

    #// For the first node, that value is completely heuristic.
    fScore[start] = heuristic_cost_estimate(start, goal)
    while len(openSet) != 0:
        current = lowest_fscore_value(fScore, openSet)
        if current == goal:
            return reconstruct_path(cameFrom, current)

        n = 0
        for i in openSet:
            if i == current:
                ind = n
                break
            n += 1

        openSet.pop(ind)
        closedSet[current] = True

        for neighbor in current.neighbours:
            in_closed = True
            try:
                closedSet[neighbor]
            except KeyError:
                in_closed = False
            if in_closed:
                continue
            #// The distance from start to a neighbor
            tentative_gScore = gScore[current] + dist_between(current, neighbor)

            in_discovered = True
            try:
                discovered[neighbor]
            except KeyError:
                in_discovered = False
            if not in_discovered:	#// Discover a new node
                discovered[neighbor] = True
                openSet.append(neighbor)
            elif tentative_gScore >= gScore[neighbor]:
                continue		#// This is not a better path.

            #// This path is the best until now. Record it!
            cameFrom[neighbor] = current
            gScore[neighbor] = tentative_gScore
            fScore[neighbor] = gScore[neighbor] + heuristic_cost_estimate(neighbor, goal)


# status effects

class StatusEffect:
    def __init__(self):
        self.name = None
        self.stacks = None
        self.finished = False

    def tick(self):
        if self.finished:
            return
        if self.stacks == 0:
            self.finished = True
        self.stacks -= 1

def has_status_effect(target, effect_name):
    for i in target.statuses:
        if i.name == effect_name:
            return True
    
    return False

def get_relevant_status_effect(target, effect_name):
    for i in target.statuses:
        if i.name == effect_name:
            return i
    
    return None

def remove_status_effect(target, effect_name):
    n = 0
    for i in target.statuses:
        if i.name == effect_name:
            break
        n += 1
    else:
        return False

    target.statuses.pop(n)

    return True

def add_status_effect(target, effect):
    target.statuses.append(effect)

class NonStackingEffect(StatusEffect):
    def __init__(self):
        StatusEffect.__init__(self)

    def apply(self, target):
        # so in here i first to a check to see if the status effect is currently applied
        # in the case of a "non stacking effect" you only want to apply it if the new
        # effect has more stacks than the currently applied one
        # hence i return if that is not the case
        if has_status_effect(target, self.name) and \
        get_relevant_status_effect(target, self.name).stacks >= self.stacks:
            return

        # otherwise i apply it
        remove_status_effect(target, self.name)
        add_status_effect(target, self)

class Burning(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "burning"

class Knocked(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "knocked"

class Slowed(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "slowed"

class Blinded(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "blinded"

def gen_effect_mod(effect, stacks):
    class Effect:
        def __init__(self):
            effect.__init__(self)
            self.stacks = stacks
            self.name = effect.name
    
    return Effect

# weapons

# Most of these classes are just dedicated storage objects currently;
# they don't have much in the way of methods

class Weapon:
    # Is given base_damage, range, and crit by inheriting classes!
    def __init__(self):
        self.quality = None
        self.quality_multiplier = None
        self.mods = []

        self.projectile_speed = 10

    def get_damage(self):
        dmg = random.randint(*self.base_damage)
        dmg *= self.quality_multiplier
        return dmg

class Mod:
    def __init__(self):
        self.name = None
        self.tier = None

        self.mclass = None
        self.value = None

def make_mod(weapon, tier3_guarantee = False):
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
        "crit": None, # these have no class, since they are just a value to be added
        "range": None # again; no class, just a value you add to a stat
    }

    # here is where i select the mod
    # by first creating a probability distribution based on the "mod_type_likelyhood" dictionary
    mdkeys = mod_dict.keys()
    pdist1_ = [[1, 0.5][mod_type_likelyhood[k] != "regular"] for k in mdkeys]
    s = sum(pdist1_)
    pdist1 = [i/s for i in pdist1_]

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


def create_weapon(rarity, quality, weapon_type):
    # from the GDD; a legendary has 4-5 mods, rare has 1-3, and common has none
    n_mods_dict = {
        "legendary": random.choice((4, 5)),
        "rare": random.choice((1, 2, 3)),
        "common": 0
    }
    n_mods = n_mods_dict[rarity]


    quality_multipliers = {
        "good": 1.5,
        "crappy": 0.5,
        "regular": 1
    }

    # instantiate weapon
    weapon = weapon_type()

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

# Sharpshooter

class Colt(Weapon):
    def __init__(self):
        Weapon.__init__(self)
        self.base_damage = 10, 15
        self.range = 8
        self.crit = 0.05

        self.attack_type = "shot"
        self.projectile_type = "bullet"
        
        self.projectile_speed = 30

class CompoundBow(Weapon):
    def __init__(self):
        Weapon.__init__(self)
        self.base_damage = 20, 25
        self.range = 11
        self.crit = 0.1

        self.attack_type = "shot"
        self.projectile_type = "arrow"

        self.projectile_speed = 20

class DetonatorOnAStick(Weapon):
    def __init__(self):
        Weapon.__init__(self)
        self.base_damage = 15, 20
        self.crit_chance = 0.05
        self.range = 8
        self.blast_radius = 5

        self.attack_type = "bomb"
        self.projectile_type = "bomb"

class WBat(Weapon):
    def __init__(self):
        Weapon.__init__(self)
        self.base_damage = 25, 35
        self.crit_chance = 0.18
        self.range = 1

        self.attack_type = "melee"


# abilities

class Ability:
    def __init__(self):
        pass

class BasicAttack(Ability):
    def __init__(self):
        Ability.__init__(self)

    def calculate_damage(self, weapon):
        pass

    def apply_effects(self, weapon):
        pass

# Sharpshooter
class Kneecapper(Ability):
    def __init__(self):
        Ability.__init__(self)

class TryToLeave(Ability):
    def __init__(self):
        Ability.__init__(self)

class LeadAmmo(Ability):
    def __init__(self):
        Ability.__init__(self)

class Steady(Ability):
    def __init__(self):
        Ability.__init__(self)

class Tornado(Ability):
    def __init__(self):
        Ability.__init__(self)

class FirstAidKit(Ability):
    def __init__(self):
        Ability.__init__(self)

class RipEmANewOne(Ability):
    def __init__(self):
        Ability.__init__(self)

class DanceOff(Ability):
    def __init__(self):
        Ability.__init__(self)

class Mutation:
    def __init__(self):
        self.mutation_to = None

class Stats:
    def __init__(self):
        self.intelligence = 0
        self.dexterity = 0
        self.strength = 0

        self.base_move_speed = 2

class AP:
    def __init__(self):
        self.turn_ap = None

        self.current_ap = None

        self.base_ap = 5
        self.max_ap = 10

        self.fractional_point = 0

        self.end_turn = False

    def use_point(self):
        self.turn_ap -= 1
        if self.turn_ap == 0:
            self.end_turn = True

    def use_fractional_point(self, f):
        self.fractional_point += f
        if self.fractional_point >= 1:
            self.fractional_point -= 1
            self.use_point()

    def new_turn(self):
        self.end_turn = False
        self.turn_ap = self.current_ap
        self.fractional_point = 0

    def calculate_ap(self, intelligence, weapons, mutations):
        ap_int = int(intelligence / 3)

        ap_weapons = 0
        for w in weapons:
            for m in w.mods:
                if not m.name == "ap":
                    continue
                ap_weapons += m.value

        ap_mutations = 0
        for m in mutations:
            if not m.mutation_to == "ap":
                continue
            ap_mutations += m.mutation_value

        ap = self.base_ap + ap_int + ap_weapons + ap_mutations

        capped_ap = min((ap, self.max_ap))

        self.current_ap = capped_ap

        return capped_ap

class Equipment:
    def __init__(self):
        self.hand_one = None
        self.hand_two = None
        self.hand_three = None

        self.head = None
        self.torso = None
        self.legs = None

        self.syringes = [None for i in range(5)]

    def get_weapons(self):
        return [i for i in [self.hand_one, self.hand_two, self.hand_three] if i != None]

    def get_range(self, w):
        weapon = w
        base_range = weapon.range

        mod_range = 0
        for m in weapon.mods:
            if m.name == "range":
                mod_range += m.value

        return base_range + mod_range

class Memory:
    def __init__(self):
        self.abilities = [None for i in range(6)]
        self.abilities[0] = BasicAttack()


class ActionTimer:
    def __init__(self, name = None, dt = None):
        self.name = ""
        if name != None:
            self.name = name
        self.dt = 0
        if dt != None:
            self.dt = dt
        self.clock = time.clock()

        self.ticked = False

    def update(self):
        if self.ticked:
            return

        if time.clock() - self.clock > self.dt:
            self.ticked = True 

    def reset(self):
        self.clock = time.clock()
        self.ticked = False

    def set_tick(self):
        self.ticked = True

class Animation:
    def __init__(self, frames):
        self.frames = frames
        self.nframe = 0

        self.frame_timer = ActionTimer()
        self.frame_timer.dt = 0.1

    def update(self):
        if self.frame_timer.ticked:
            self.nframe += 1
            if self.nframe == len(self.frames):
                self.nframe = 0
            self.frame_timer.reset()

        self.frame_timer.update()

    def get_frame(self):
        return self.frames[self.nframe]

def get_move_speed(base_move_speed, strength, statuses, mutations):
    return base_move_speed + strength//2

def in_range(u1, u2, r):
    x1, y1 = u1
    x2, y2 = u2

    if (x1-x2)**2 + (y1-y2)**2 <= r**2:
        return True
    return False

def corrigated_path(self):
    cpath = []
    ppos = self.pos
    avail_points = self.ap.turn_ap
    use_points = []
    for p in self.path:
        VX, VY = p[0] - ppos[0], p[1] - ppos[1]
        if VX**2 + VY ** 2 == 2:
            move_distance = 1.41
        else:
            move_distance = 1
        ms = get_move_speed(self.stats.base_move_speed, self.stats.strength, self.statuses, self.mutations)
        use_points.append(move_distance/ms)

        cpath.append(p)

        if avail_points - sum(use_points) <= 0:
            break

    return cpath, use_points

def get_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dsq = (x1-x2)**2 + (y1-y2)**2 

    return dsq ** 0.5


class UIInteractiveElement:
    def __init__(self):
        self.assigned_item = None

        self.box = None
        self.select_timer = ActionTimer("Click", 0.2)
        
        self.animations = {}
        self.anim = 0

        self.selected = False

        self.draw_x, self.draw_y = 0, 0

    def update(self, mpos, mpress, at_mouse):
        self.select_timer.update()

        for a in self.animations.values():
            a.update()
        
        x, y = mpos
        
        x, y = x-self.draw_x, y-self.draw_y

        mouseover = False
        curr_select = False
        if self.box.collidepoint((x, y)):
            mouseover = True
            if self.select_timer.ticked and mpress[0] == 1:
                curr_select = True
                self.selected = True - self.selected
                self.select_timer.reset()

        if self.selected:
            self.anim = self.animations["selected"]
        else:
            self.anim = self.animations["not selected"]

        select = False
        if curr_select and self.selected == True:
            select = True
        return mouseover, select

    def get_frame(self):
        return self.anim.get_frame()

class UIInteractive:
    def __init__(self, g_obj):
        self.selected_element = None

        self.ui_elements = {}
        
        self.gen_ui(g_obj)

    def gen_ui(self, g_obj):

        ui_start_x, ui_start_y = 0, g_obj.h - 0 
        ui_x = ui_start_x
        ui_y = ui_start_y
        ui_w, ui_h = 16*g_obj.scaling, 16*g_obj.scaling
        ui_b = 0
        ui_s = 8

        end_desel_anim = (245,)
        end_sel_anim = (245, 229, 213)
        ele = UIInteractiveElement()
        ele.box = pygame.Rect(ui_x, ui_y, ui_w, ui_h)
        self.ui_elements["end turn"] = ele
        ele.animations["selected"] = Animation(end_sel_anim)
        ele.animations["not selected"] = Animation(end_desel_anim)
        ui_x += ui_w + ui_b

        ui_x += ui_s

        mv_desel_anim = (244,)
        mv_sel_anim = (244, 228, 212)
        ele = UIInteractiveElement()
        ele.box = pygame.Rect(ui_x, ui_y, ui_w, ui_h)
        self.ui_elements["move"] = ele
        ele.animations["selected"] = Animation(mv_sel_anim)
        ele.animations["not selected"] = Animation(mv_desel_anim)
        ui_x += ui_w + ui_b

        ui_x += ui_s

        rh_desel_anim = (241,)
        rh_sel_anim = (241, 225, 209)
        ele = UIInteractiveElement()
        ele.box = pygame.Rect(ui_x, ui_y, ui_w, ui_h)
        ele.animations["selected"] = Animation(rh_sel_anim)
        ele.animations["not selected"] = Animation(rh_desel_anim)
        self.ui_elements["right hand"] = ele
        ui_x += ui_w + ui_b

        ui_x += ui_s

        lh_desel_anim = (242,)
        lh_sel_anim = (242, 226, 210)
        ele = UIInteractiveElement()
        ele.box = pygame.Rect(ui_x, ui_y, ui_w, ui_h)
        ele.animations["selected"] = Animation(lh_sel_anim)
        ele.animations["not selected"] = Animation(lh_desel_anim)
        self.ui_elements["left hand"] = ele
        ui_x += ui_w + ui_b

        ui_x += ui_s

        abi_desel_anim = (243,)
        abi_sel_anim = (243, 227, 211)
        for i in range(5):
            ele = UIInteractiveElement()
            ele.box = pygame.Rect(ui_x, ui_y, ui_w, ui_h)
            ele.animations["selected"] = Animation(abi_sel_anim)
            ele.animations["not selected"] = Animation(abi_desel_anim)
            self.ui_elements["ability {0}".format(str(i+1))] = ele
            ui_x += ui_w + ui_b

        ui_x += ui_s

        syr_desel_anim = (240,)
        syr_sel_anim = 240, 224, 208
        for i in range(5):
            ele = UIInteractiveElement()
            ele.box = pygame.Rect(ui_x, ui_y, ui_w, ui_h)
            ele.animations["selected"] = Animation(syr_sel_anim)
            ele.animations["not selected"] = Animation(syr_desel_anim)
            self.ui_elements["syringe {0}".format(str(i+1))] = ele
            ui_x += ui_w + ui_b
    
    def update(self, mpos, mpress, at_mouse):
        mouseover = []
        for k in self.ui_elements.keys():
            e = self.ui_elements[k]
            mover, select = e.update(mpos, mpress, at_mouse)
            mouseover.append(mover)
            if select:
                self.selected_element = k
                for i in [n for n in list(self.ui_elements.values()) if n != e]:
                    i.selected = False
                break

        if any(mouseover):
            return True
        return False

class UIInformational:
    def __init__(self):
        pass

    def update(self, mpos, mpress, at_mouse):
        pass

class UI:
    def __init__(self, g_obj):
        self.ui1 = UIInteractive(g_obj)
        self.ui2 = UIInformational()

    def update(self, mpos, mpress, at_mouse):
        self.ui2.update(mpos, mpress, at_mouse)
        mouseover = self.ui1.update(mpos, mpress, at_mouse)
        return mouseover

    def get_selected(self):
        return self.ui1.selected_element

    def set_selected(self, v):
        self.ui1.selected_element = v
        sel = None
        for k in self.ui1.ui_elements.keys():
            e = self.ui1.ui_elements[k]
            if v == k:
                sel = e
                e.selected = True
                break

        for i in [n for n in list(self.ui1.ui_elements.values()) if n != sel]:
            i.selected = False



class Unit:
    def __init__(self):
        self.pos = 0, 0
        self.next_pos = 0, 0
        self.path = None
        self.has_moved = 0
        self.use_points = []

        self.direction = 1

        self.destination = None
        self.get_path = False
        self.first_move = False


        self.projectile_pos = 0, 0
        self.attacking = None
        self.attack_weapon = None
        self.projectile_angle = 0


        self.area = 1


        self.equipment = Equipment()
        self.memory = Memory()
        self.mutations = [Mutation()]
        self.stats = Stats()
        self.ap = AP()


        self.health = 35
        self.max_health = 35


        self.statuses = []


        self.state = "idle"
        self.timers = {}
        move_timer = ActionTimer()
        move_timer.dt = 0.15
        self.timers["move_timer"] = move_timer

        attack_timer = ActionTimer()
        attack_timer.dt = 0.75
        self.timers["attack_timer"] = attack_timer


        self.end_turn = False


        self.init_health_and_base_ap()
        self.init_abilities()
        self.init_stats()
        self.init_equipment()
        self.init_animations()


        self.ap.calculate_ap(self.stats.intelligence, self.equipment.get_weapons(), self.mutations)
        self.ap.new_turn()

    def init_health_and_base_ap(self):
        pass

    def init_abilities(self):
        pass

    def init_stats(self):
        self.stats.strength = 0

    def init_equipment(self):
        pass

    def init_animations(self):
        pass

    def set_pos(self, pos):
        self.pos = pos
        self.anim_pos = pos
        self.next_pos = pos

    def finish_turn(self):
        if self.state == "dead" or self.state == "dying":
            return
        self.path = None
        self.state = "idle"

    def get_damage(self):
        return self.attack_weapon.get_damage()

    def damage(self, damagee):
        damagee.health -= self.get_damage()
        if damagee.health <= 0:
            damagee.state = "dying"

    def update_general(self, mpos, mpress, at_mouse, ui):
        if self.state == "dying":
            self.state = "dead"

        if self.state == "dead":
            self.end_turn = True
            return

        for t in self.timers.values():
            t.update()

        for a in self.animations.values():
            a.update()

    def launch_bomb(self, at_mouse):
        self.state = "attacking"
        self.attacking = at_mouse["units"][self.attack_weapon.blast_radius-2]
        projectile_speed_per_unit = self.attack_weapon.projectile_speed
        self.attack_to = at_mouse["mapped"]
        
        projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
        self.timers["attack_timer"].dt = projectile_distance
        self.timers["attack_timer"].reset()
        self.ap.use_point()
        self.ap.use_point()

    def fire_shot(self, at_mouse):
        self.state = "attacking"
        self.attacking = [at_mouse["unit"]]

        projectile_speed_per_unit = self.attack_weapon.projectile_speed
        self.attack_to = at_mouse["mapped"]
        
        projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
        self.timers["attack_timer"].dt = projectile_distance
        self.timers["attack_timer"].reset()
        self.ap.use_point()
        self.ap.use_point()

    def swing(self, at_mouse):
        self.state = "attacking"
        self.attacking = [at_mouse["unit"]]

        self.attack_to = at_mouse["mapped"]
        self.timers["attack_timer"].dt = 0.35
        self.timers["attack_timer"].reset()
        self.ap.use_point()
        self.ap.use_point()

    def update_turn(self, mpos, mpress, at_mouse, ui):
        if ui.get_selected() == "right hand":
            self.attack_weapon = self.equipment.hand_one
        elif ui.get_selected() == "left hand":
            self.attack_weapon = self.equipment.hand_two
        else:
            self.attack_weapon = None

        if self.state and self.state == "idle" and not at_mouse["ui mouseover"]:
            # walking
            if at_mouse["walkable"] and self.path == None and ui.get_selected() == "move":
                if mpress[0] == 1:
                    self.get_path = True
                    self.destination = at_mouse["mapped"]
        
            # basic attack
            if self.attack_weapon != None and self.ap.turn_ap >= 2:
                if mpress[0] == 1:
                    if self.attack_weapon.attack_type == "bomb":
                        if in_range(at_mouse["mapped"], self.pos, self.equipment.get_range(self.attack_weapon)):
                            self.launch_bomb(at_mouse)
                    elif self.attack_weapon.attack_type == "shot" and at_mouse["unit"] != None and \
                    at_mouse["unit"].state not in ("dead", "dying"):
                        if in_range(at_mouse["mapped"], self.pos, self.equipment.get_range(self.attack_weapon)):
                            self.fire_shot(at_mouse)
                    elif self.attack_weapon.attack_type == "melee" and at_mouse["unit"] != None and \
                    at_mouse["unit"].state not in ("dead", "dying"):
                        if in_range(at_mouse["mapped"], self.pos, 1.42):
                            self.swing(at_mouse)

        if self.state == "dead":
            self.end_turn = True
            return
        elif self.state == "idle":
            if self.ap.end_turn:
                self.end_turn = True
            if self.path != None:
                self.state = "moving"
            if ui.get_selected() == "end turn":
                self.end_turn = True
                ui.set_selected(None)
            self.anim_state = "standing"
        elif self.state == "moving":
            skip = False
            self.anim_state = "walking"
            if self.timers["move_timer"].ticked:
                if len(self.path) == 0:
                    self.pos = self.next_pos
                    self.anim_pos = self.pos
                    self.state = "idle"
                    self.path = None
                else:
                    
                    if not self.first_move:
                        X, Y = self.pos
                        NX, NY = self.next_pos
                        VX, VY = (NX-X), (NY-Y)

                        if VX < 0:
                            self.direction = -1
                        elif VX > 0:
                            self.direction = 1

                    else:
                        self.path, self.use_points = corrigated_path(self)

                    self.first_move = False
                    
                    if not skip:
                        self.pos = self.next_pos
                        self.next_pos = self.path.pop(0)
                        use_point = self.use_points.pop(0)
                        if use_point != 0:
                            self.ap.use_fractional_point(use_point)
                        self.timers["move_timer"].reset()
            
            if not skip:
                i = (time.clock() - self.timers["move_timer"].clock) / self.timers["move_timer"].dt
                X, Y = self.pos
                NX, NY = self.next_pos
                VX, VY = (NX-X), (NY-Y)
                AX, AY = i * VX + X, i * VY + Y
                self.anim_pos = AX, AY
        
        elif self.state == "casting":
            pass
            
        elif self.state == "attacking":
            if not self.timers["attack_timer"].ticked:
                if self.attack_weapon.attack_type == "bomb":
                    i = (time.clock() - self.timers["attack_timer"].clock) / self.timers["attack_timer"].dt
                    df_pheight = 3
                    pheight = math.sin(i*math.pi) * df_pheight
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX-X), (NY-Y)
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_pos = AX, AY - pheight
                elif self.attack_weapon.attack_type == "shot":
                    i = (time.clock() - self.timers["attack_timer"].clock) / self.timers["attack_timer"].dt
                    df_pheight = 3
                    pheight = math.sin(i*math.pi) * df_pheight
                    pheight = 0
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX-X), (NY-Y)
                    self.projectile_angle = math.degrees(math.atan2(VY, VX))
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_pos = AX, AY - pheight
                elif self.attack_weapon.attack_type == "melee":
                    i = (time.clock() - self.timers["attack_timer"].clock) / self.timers["attack_timer"].dt
                    df_pheight = 5
                    pheight = math.sin(i*math.pi) * df_pheight
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX-X), (NY-Y)
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_angle = (math.atan2(VY, VX))
                    T = 32
                    qx, qy = math.cos(self.projectile_angle) * T, math.sin(self.projectile_angle) * T# - pheight
                    self.projectile_pos = qx, qy
            else:
                self.state = "idle"
                for u in self.attacking:
                    self.damage(u)

        elif self.state == "knocked":
            pass

        elif self.state == "dying":
            self.state = "dead"

    def update(self, mpos, mpress, at_mouse, yourturn, ui):
        if yourturn:
            self.update_turn(mpos, mpress, at_mouse, ui)
        self.update_general(mpos, mpress, at_mouse, ui)

    def current_animation(self):
        return self.animations[self.anim_state]

class MC(Unit):
    def init_animations(self):
        self.animations = {}
        walking = Animation((250,245))
        standing = Animation((250,))
        self.animations["walking"] = walking
        self.animations["standing"] = standing
        self.anim_state = "standing"
        self.anim_pos = self.pos

        self.mc_type = "sharpshooter"

        self.anim_facing = 1

    def init_equipment(self):
        self.equipment.hand_one = create_weapon("rare", "good", WBat)
        self.equipment.hand_two = create_weapon("legendary", "good", Colt)
        self.attack_weapon = None

    def init_stats(self):
        self.health = 100
        self.max_health = 100



class Bat(Unit):
    def init_animations(self):
        self.animations = {}
        walking = Animation((244,148))
        standing = Animation((148,))
        self.animations["walking"] = walking
        self.animations["standing"] = standing
        self.anim_state = "standing"
        self.anim_pos = self.pos

        self.anim_facing = 1

class Zombie(Unit):
    def init_animations(self):
        self.animations = {}
        walking = Animation((243,165))
        standing = Animation((165,))
        self.animations["walking"] = walking
        self.animations["standing"] = standing
        self.anim_state = "standing"
        self.anim_pos = self.pos

        self.anim_facing = -1

class Brute(Unit):
    def init_animations(self):
        self.animations = {}
        walking = Animation((242,164))
        standing = Animation((164,))
        self.animations["walking"] = walking
        self.animations["standing"] = standing
        self.anim_state = "standing"
        self.anim_pos = self.pos

        self.anim_facing = -1

class Mage(Unit):
    def init_animations(self):
        self.animations = {}
        walking = Animation((241,161))
        standing = Animation((161,))
        self.animations["walking"] = walking
        self.animations["standing"] = standing
        self.anim_state = "standing"
        self.anim_pos = self.pos
        
        self.anim_facing = -1

class Tiny(Unit):
    def init_animations(self):
        self.animations = {}
        walking = Animation((240,160))
        standing = Animation((160,))
        self.animations["walking"] = walking
        self.animations["standing"] = standing
        self.anim_state = "standing"
        self.anim_pos = self.pos

        self.anim_facing = -1

def load_tsx(filename):
    with open(filename, "r") as f:
        xml = "\n".join(f.readlines()[0:])

    d = (xmltodict.parse(xml))
    return d


def load_tileset(filename, width, height, scale):
    #from https://stackoverflow.com/questions/16280608/pygame-how-to-tile-subsurfaces-on-an-image
    image = pygame.image.load(filename).convert_alpha()
    image_width, image_height = image.get_size()
    tileset = []
    for tile_y in range(0, image_height//height):
        #line = []
        #tileset.append(line)
        for tile_x in range(0, image_width//width):
            rect = (tile_x*width, tile_y*height, width, height)
            new = pygame.transform.scale(image.subsurface(rect), (width*scale, height*scale))
            new.set_colorkey(image.get_colorkey())
            tileset.append(new)
    return (image_width//width, image_height//height), tileset

def get_walkable(walkable_path, tsw, tsh):
    with open(walkable_path, "r") as f:
        d = json.load(f)

    walkable = {}
    for t in d["tiles"]:
        walkable[t["id"]] = False

    for x, y in itertools.product(range(tsw), range(tsh)):
        tid = y * tsw + x
        if tid not in walkable:
            walkable[tid] = True

    return walkable


def load_json_tilemap(path, scale):
    with open(path, "r") as f:
        d = json.load(f)

    tilesets = []
    tilewidth, tileheight = d["tilewidth"], d["tileheight"]
    mapwidth, mapheight = d["width"], d["height"]
    metadata = {
        "tilewidth": tilewidth*scale,
        "tileheight": tileheight*scale,
        "mapwidth": mapwidth,
        "mapheight": mapheight
    }
    for t in d["tilesets"]:
        path = load_tsx(t["source"])["tileset"]["image"]["@source"]
        (tsw, tsh), tdata = load_tileset(path, tilewidth, tileheight, scale)
        #print(path)
        walkable_path = ".".join(path.split(".")[:-1])+".json"
        #print(walkable_path)
        walkable = get_walkable(walkable_path, tsw*scale, tsh*scale)
        tilesets.append((t["firstgid"], (tsw*scale, tsh*scale), tdata, walkable))

    layers = d["layers"]
    
    return metadata, tilesets, layers

class Dungeon:
    def __init__(self, scaling = None):
        self.scale_tileset = 4
        if scaling != None:
            self.scale_tileset = scaling

    def load_test_room(self, path):
        self.metadata, self.tilesets, self.layers = load_json_tilemap(path, self.scale_tileset)
        self.walkable_map = create_dung_walkable_matrix(self)

    def change_layer_status(self, names, to):
        
        for n in names:
            i = 0
            for l in self.layers:
                if self.layers[i]["name"] == n:
                    self.layers[i]["visible"] = to
                i += 1

    def disable_layers(self, names):
        self.change_layer_status(names, False)

    def enable_layers(self, names):
        self.change_layer_status(names, True)

    def get_layer(self, name):
        for l in self.layers:
            if l["name"] == name:
                return l
        return None


def get_sprite(g_obj, sid):
    return g_obj.dungeon.tilesets[1][2][sid]

def draw_units(g_obj):
    dung = g_obj.dungeon
    tw, th = dung.metadata["tilewidth"], dung.metadata["tileheight"]
    for u in g_obj.units:
        img = get_sprite(g_obj, u.current_animation().get_frame())
        ox, oy = g_obj.cam.get()
        x, y = u.anim_pos
        rx, ry = ox+x*tw, oy+y*th
        #print(rx, ry)
        if u.anim_facing != u.direction:
            xbool = 1
        else:
            xbool = 0
        uimg = pygame.transform.flip(img, xbool, 0)
        if u.state == "dead":
            uimg = pygame.transform.rotate(uimg, 90)
        aox, aoy = 0, 0
        if u.state == "attacking" and u.attack_weapon.attack_type == "melee":
            aox, aoy = u.projectile_pos
        g_obj.swin.blit(uimg, (rx+aox, ry+aoy))

def draw_dungeon_layer(g_obj, name, wmap = None):
    dung = g_obj.dungeon
    layer = dung.get_layer(name)
    ox, oy = g_obj.cam.get()

    sw, sh = g_obj.qw, g_obj.qh

    x, y = ox, oy
    tw, th = dung.metadata["tilewidth"], dung.metadata["tileheight"]
    nx, ny = 0, 0

    mw, mh = dung.metadata["mapwidth"], dung.metadata["mapheight"]

    buffer = max((2*tw, 2*th))
    screen_rect = pygame.Rect(-buffer, -buffer, sw+buffer*2, sh+buffer*2)

    y_len = dung.metadata["mapheight"]
    x_len = dung.metadata["mapwidth"]
    for i in range(mw * mh):
        if mw > nx >= 0 and mh > ny >= 0 and screen_rect.collidepoint((x, y)):
            l = layer
            tv = l["data"][ny * x_len + nx]

            if tv == 0:
                pass 
            else:
                for t in dung.tilesets:
                    if tv <= len(t[2]):
                        break
                    tv -= len(t[2])

                tile = t[2][tv-1]

                g_obj.swin.blit(tile, (x, y))

                if wmap != None:
                    if wmap[nx][ny]:
                        g_obj.swin.blit(g_obj.wsurf, (x, y))
                    else:
                        g_obj.swin.blit(g_obj.nwsurf, (x, y))

        x += tw
        nx += 1
        if nx == mw:
            x = ox
            nx = 0
            ny += 1
            y += th

def draw_projectiles(g_obj):
    cu = g_obj.cc.get_current_unit()
    if not (cu.state == "attacking"):
        return

    bomb_frame = 47+16 # + 16*4-1, + 16*4-2
    arrow_frame = 166
    bullet_frame = 166+16*3

    ox, oy = g_obj.cam.get()
    x, y = cu.projectile_pos
    if cu.attack_weapon.attack_type == "bomb":
        img = get_tile_img(g_obj, 1, bomb_frame)
        g_obj.swin.blit(img, (x*g_obj.scaling*16+ox, y*g_obj.scaling*16+oy))
        
    elif cu.attack_weapon.attack_type == "shot":
        if cu.attack_weapon.projectile_type == "arrow":
            img = get_tile_img(g_obj, 1, arrow_frame)
        elif cu.attack_weapon.projectile_type == "bullet":
            img = get_tile_img(g_obj, 1, bullet_frame)
        
        img = pygame.transform.rotate(img, 90-cu.projectile_angle)

        g_obj.swin.blit(img, (x*g_obj.scaling*16+ox, y*g_obj.scaling*16+oy))


def view_tileset(g_obj, which):
    tfid, (tsw, tsh), tdata, walk = g_obj.dungeon.tilesets[which]
    tw, th = g_obj.dungeon.metadata["tilewidth"], g_obj.dungeon.metadata["tileheight"]
    y_len = tsh
    for x in range(tsw):
        for y in range(tsh):
            tile = tdata[y_len * x + y]
            px, py = x * tw, y * th
            g_obj.swin.blit(tile, (px, py))

    g_obj.win.blit((g_obj.swin), (0,0))


class Camera:
    def __init__(self, w, h):
        self.x, self.y = 0, 0
        self.w, self.h = w, h

        self.update_step = 1

        cw, ch = 180, 180

        self.cw, self.ch = cw, ch

        self.border_left = pygame.Rect((0, 0), (cw, h))
        self.border_bot = pygame.Rect((0, h-ch), (w, ch))
        self.border_right = pygame.Rect((w-cw, 0), (cw, h))
        self.border_top = pygame.Rect((0, 0), (w, ch))

    def update(self, mpos):
        mx, my = mpos

        b = (self.border_left, self.border_bot, self.border_right, self.border_top)
        d = ((-1, 0), (0, 1), (1, 0), (0, -1))

        for r, v in zip(b, d):
            if not r.collidepoint((mx, my)):
                continue
            if v == (-1, 0):
                D = (((self.cw - mx) / self.cw) * 3) ** 2.5
            elif v == (1, 0):
                D = ((1-((self.w - mx)) / self.cw) * 3) ** 2.5
            elif v == (0, -1):
                D = ((((self.ch - my)) / self.ch) * 3) ** 2.5
            elif v == (0, 1):
                D = ((1-(self.h - my) / self.ch) * 3) ** 2.5
            else:
                D = 1
            self.x, self.y = self.x + -1 * v[0] * self.update_step * D, self.y + -1 * v[1] * self.update_step * D

    def get(self):
        return int(self.x), int(self.y)

def get_tile_img(g_obj, tileset, tilenr):
    tile = g_obj.dungeon.tilesets[tileset][2][tilenr]
    return tile

def draw_ui(g_obj):
    # draw informational ui

    turns_w = int(g_obj.w/2) - int(16*g_obj.scaling * 4.5)
    turns_h = 16*g_obj.scaling

    px, py = turns_w, turns_h

    draw_turns = 8
    units = g_obj.cc.units_in_combat
    n = g_obj.cc.turn
    i = 0
    while True:
        unit = units[n]
        n += 1
        if n >= len(units):
            n = 0
        if unit.state == "dead":
            continue

        i += 1

        f = unit.animations["standing"].get_frame()
        img = get_tile_img(g_obj, 1, f)

        px += 16*g_obj.scaling
        g_obj.swin.blit(img, (px, py))

        if i == draw_turns:
            break
        

    cu = g_obj.cc.get_current_unit()
    if g_obj.at_mouse["unit"] != None:
        cu = g_obj.at_mouse["unit"] 
    ca = cu.ap.current_ap
    ta = cu.ap.turn_ap
    
    ap_green = get_tile_img(g_obj, 1, 216)
    ap_yellow = get_tile_img(g_obj, 1, 218)

    x_spot = 128 * 5 + 16*g_obj.scaling

    uiinfo_w = 16

    apx = x_spot
    apy = 16*g_obj.scaling + 64

    for i in range(0, uiinfo_w*ca, uiinfo_w):
        g_obj.swin.blit(ap_yellow, (apx+i, apy))
    for i in range(0, uiinfo_w*ta, uiinfo_w):
        g_obj.swin.blit(ap_green, (apx+i, apy))

    hp = cu.health
    mhp = cu.max_health

    h_repr = 5

    hpx = g_obj.qw - x_spot - 16
    hpy = 16*g_obj.scaling + 64

    hp_red = get_tile_img(g_obj, 1, 215)
    hp_yellow = ap_yellow

    for i in range(0, uiinfo_w*h_repr, uiinfo_w):
        g_obj.swin.blit(hp_yellow, (hpx-i, hpy))
    for i in range(0, uiinfo_w*int((h_repr*hp)/mhp), uiinfo_w):
        g_obj.swin.blit(hp_red, (hpx-i, hpy))

    midx = (apx + hpx) // 2
    img = get_tile_img(g_obj, 1, cu.animations["standing"].frames[0])
    g_obj.swin.blit(img, (midx, hpy))

    # draw interactive ui
    ui_ = g_obj.ui.ui1
    for k in ui_.ui_elements.keys():
        ele = ui_.ui_elements[k]

        pos = ele.box.topleft
        f = ele.get_frame()
        img = get_tile_img(g_obj, 0, f)
        draw_x = int(g_obj.cam.cw/2) + 64
        draw_y = - int(g_obj.cam.ch/2) - 128 - 32 + 8*g_obj.scaling
        ele.draw_x = draw_x
        ele.draw_y = draw_y
        
        g_obj.swin.blit(img, (pos[0] + draw_x, pos[1] + draw_y))

def create_dung_walkable_matrix(dungeon):
    dung = dungeon
    layers = dung.layers

    tw, th = dung.metadata["tilewidth"], dung.metadata["tileheight"]
    nx, ny = 0, 0
    x, y = 0, 0

    mw, mh = dung.metadata["mapwidth"], dung.metadata["mapheight"]

    walkable_map = [[0 for i in range(mh)] for j in range(mw)]

    buffer = max((2*tw, 2*th))

    y_len = dung.metadata["mapheight"]
    x_len = dung.metadata["mapwidth"]
    for i in range(mw * mh):
        if mw > nx >= 0 and mh > ny >= 0:
            for l in layers:
                tv = l["data"][ny * x_len + nx]

                if tv == 0:
                    pass 
                else:
                    for t in dung.tilesets:
                        if tv <= len(t[2]):
                            break
                        tv -= len(t[2])

                    tid = tv-1

                    is_walkable = t[3][tid]

                    walkable_map[nx][ny] = is_walkable



        x += tw
        nx += 1
        if nx == mw:
            x = 0
            nx = 0
            ny += 1
            y += th

    return walkable_map

def copy(l):
    nl = []
    for i in l:
        if isinstance(i, list):
            nl.append(copy(i))
        else:
            nl.append(i)
    return nl

def create_walkable_matrix(dung_walk, units, cu):
    walk_mat = copy(dung_walk)
    for u in units:
        if u == cu:
            continue
        x, y = u.pos
        walk_mat[x][y] = False
    
    return walk_mat

class Node:
    def __init__(self, x, y):
        self.pos = x, y
        self.neighbours = []

def get_node_map(walk_mat):
    node_map = [[Node(x, y) for y in range(len(walk_mat[x]))] for x in range(len(walk_mat))]
    nbors = [
        [0, 1],
        [1, 0],
        [0, -1],
        [-1, 0],
        [1, 1],
        [-1, -1],
        [1, -1],
        [-1, 1]
    ]
    for x, y in itertools.product(range(len(node_map[0])), range(len(node_map[1]))):
        if not walk_mat[x][y]:
            continue
        for nbor in nbors:
            nx, ny = x + nbor[0], y + nbor[1]
            if not (0 <= nx < len(node_map) and 0 <= ny < len(node_map[0])):
                continue
            if not walk_mat[nx][ny]:
                continue
            node_map[x][y].neighbours.append(node_map[nx][ny])
                
    return node_map


def map_mpos(g_obj, mpos):
    dung = g_obj.dungeon
    ox, oy = g_obj.cam.get()

    #sw, sh = g_obj.qw, g_obj.qh

    #x, y = ox, oy
    tw, th = dung.metadata["tilewidth"], dung.metadata["tileheight"]
    #nx, ny = 0, 0

    mw, mh = dung.metadata["mapwidth"], dung.metadata["mapheight"]

    bs, g_obj.scaling = g_obj.scaling, 1

    mx = ((mpos[0]//g_obj.scaling-ox)//(tw))
    my = ((mpos[1]//g_obj.scaling-oy)//(th))

    #print(mx, my)

    g_obj.scaling = bs

    inside = False
    if ((0 <= mx < mw) and (0 <= my < mh)):
        inside = True

    return (mx, my), inside


def get_tiles_at_and_walkable(g_obj, mpos_mapped):
    nx, ny = mpos_mapped

    dung = g_obj.dungeon
    layers = dung.layers

    y_len = dung.metadata["mapheight"]
    x_len = dung.metadata["mapwidth"]

    tiles = []
    tile_walkable = True

    all_tv = True

    for l in layers:
        tv = l["data"][ny * x_len + nx]

        if tv == 0:
            pass
        else:
            all_tv = False
            for t in dung.tilesets:
                if tv <= len(t[2]):
                    break
                tv -= len(t[2])

            tid = tv-1

            is_walkable = t[3][tid]
            if not is_walkable:
                tile_walkable = False

            tile = t[2][tid]
            tiles.append(tile)

    if all_tv:
        tile_walkable = False

    return tiles, tile_walkable

def get_mouse_hover(g_obj, mpos):
    at_mouse = {}

    mpos_mapped, inside = map_mpos(g_obj, mpos)
    at_mouse["mapped"] = mpos_mapped

    at_mouse["unit"] = None
    for u in g_obj.units:
        if u.pos == mpos_mapped:
            at_mouse["unit"] = u


    units = []
    for rad in range(1, 8):
        units.append([])
        for u in g_obj.units:
            if in_range(u.pos, mpos_mapped, rad):
                units[-1].append(u)

    at_mouse["units"] = units

    if inside:
        tiles, walkable = get_tiles_at_and_walkable(g_obj, mpos_mapped)
    else:
        tiles = []
        walkable = False

    if at_mouse["unit"] != None:
        walkable = False

    at_mouse["tiles"] = tiles
    at_mouse["walkable"] = walkable

    #print(at_mouse["mapped"], walkable)

    return at_mouse


def infinite_loop(func):
    def new_func():
        while True:
            func()
    return new_func


class CombatController:
    def __init__(self):
        self.state = "start combat"

        self.units_in_combat = []
        self.turn = 0

    def get_current_unit(self):
        return self.units_in_combat[self.turn]

    def update(self):
        if self.state == "start combat":
            self.state = "in combat"

        if self.state == "in combat":
            cu = self.get_current_unit()
            if cu.end_turn == True:
                self.turn += 1
                if self.turn >= len(self.units_in_combat):
                    self.turn = 0
                
                cu.finish_turn()

                nu = self.get_current_unit()
                nu.end_turn = False
                nu.ap.new_turn()


class Game:
    def __init__(self):
        self.w, self.h = 1800, 950
        self.scaling = 4
        self.qw, self.qh = int(self.w/self.scaling), int(self.h/self.scaling)
        self.qw, self.qh = self.w, self.h

        pygame.init()
        self.swin = pygame.Surface((self.qw, self.qh))
        self.win = pygame.display.set_mode((self.w, self.h))

        self.wsurf = pygame.Surface((16*self.scaling, 16*self.scaling))
        self.wsurf.set_alpha(200)
        self.nwsurf = pygame.Surface((16*self.scaling, 16*self.scaling))
        self.nwsurf.set_alpha(200)
        self.wsurf.fill((0,255,0))
        self.nwsurf.fill((255,0,0))

        self.clock = pygame.time.Clock()
        self.fps = 144

        self.ui = UI(self)
        self.at_mouse = None

        self.cam = Camera(self.w, self.h)        

        dungeon = Dungeon(self.scaling)
        dungeon.load_test_room("Training_Room.json")
        #dungeon.disable_layers(("UI", "Character_enter", "Character_inside"))
        #for l in dungeon.layers:
        #    print({k:l[k] for k in l.keys() if k != "data"})

        self.dungeon = dungeon

        self.units = []
        mc = MC()
        mc.set_pos((15, 15))
        self.units.append(mc)
        bat = Bat()
        bat.set_pos((20, 20))
        self.units.append(bat)
        zombie = Zombie()
        zombie.set_pos((21, 20))
        self.units.append(zombie)
        brute1 = Brute()
        brute1.set_pos((10, 13))
        self.units.append(brute1)
        brute2 = Brute()
        brute2.set_pos((11, 13))
        self.units.append(brute2)
        mage = Mage()
        mage.set_pos((20, 24))
        self.units.append(mage)
        tiny = Tiny()
        tiny.set_pos((15, 22))
        self.units.append(tiny)

        self.cc = CombatController()
        self.cc.units_in_combat = self.units

        self.draw_thread = StoppableThread(target=infinite_loop(self.draw))
        self.draw_thread.start()

        self.loop()

    def update(self):
        # get input
        mpos = pygame.mouse.get_pos()
        #print(mpos)
        mpress = pygame.mouse.get_pressed()
        at_mouse = get_mouse_hover(self, mpos)
        self.at_mouse = at_mouse

        # update stuff
        mouseover = self.ui.update(mpos, mpress, at_mouse)
        at_mouse["ui mouseover"] = mouseover

        self.cam.update(mpos)
        self.cc.update()

        units_turn = self.cc.get_current_unit()
        for u in self.units:
            if u == units_turn:
                yourturn = True
            else:
                yourturn = False
            u.update(mpos, mpress, at_mouse, yourturn, self.ui)
            if u.get_path:
                walkable_matrix = create_walkable_matrix(self.dungeon.walkable_map, self.units, u)
                node_map = get_node_map(walkable_matrix)
                sx, sy = u.pos
                start_node = node_map[sx][sy]
                ex, ey = u.destination
                end_node = node_map[ex][ey]
                path = A_Star(start_node, end_node)
                if path != None:
                    conv_path = list(reversed(list(map(lambda n: n.pos, path))))
                    conv_path.pop(0)
                    u.path = conv_path
                u.get_path = False
                u.first_move = True

    def draw(self):
        self.win.fill((0, 0, 0))
        self.swin.fill((0, 0, 0))
        draw_dungeon_layer(self, "Floors")#, wmap = self.dungeon.walkable_map)
        draw_dungeon_layer(self, "Dirt")#, wmap = self.dungeon.walkable_map)
        draw_units(self)
        draw_dungeon_layer(self, "Walls")#, wmap = self.dungeon.walkable_map)
        draw_dungeon_layer(self, "Skullz")#, wmap = self.dungeon.walkable_map)
        #view_tileset(self, 1)
        draw_projectiles(self)
        draw_ui(self)
        self.win.blit(self.swin, (0, 0))
        pygame.display.update()

    def loop(self):
        while True:
            self.update()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
 
                    pygame.quit()
                    return
            
            self.clock.tick(self.fps)


if __name__ == "__main__":
    g = Game()
    
