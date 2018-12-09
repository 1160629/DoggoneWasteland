from time import clock
from math import pi, sin
from random import random, shuffle, randint, choice
from logic import Rect
from prerendering import prerender_skilltree
from equipment_generation import create_weapon
from equipment import get_new_weapon_instance
import math


# Used in Animation, and used with states to time actions
class ActionTimer:
    def __init__(self, name=None, dt=None):
        self.name = ""
        if name != None:
            self.name = name
        self.dt = 0
        if dt != None:
            self.dt = dt
        self.clock = clock()

        self.ticked = False

    def get_progress(self):
        # returns progress until it ticks
        if self.dt == 0:
            return 0
        progress = (clock() - self.clock) / self.dt
        if progress > 1:
            progress = 1
        return progress

    def update(self):
        if self.ticked:
            return

        if clock() - self.clock > self.dt:
            self.ticked = True

    def reset(self):
        # reset timer
        self.clock = clock()
        self.ticked = False

    def set_tick(self):
        # override
        self.ticked = True


# animation class
# loops a series of frames with frame_timer.dt delay

class Frame:
    def __init__(self, dt, tiles):
        self.dt = dt
        self.tiles = tiles


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
            self.frame_timer.dt = self.get_frame().dt
            self.frame_timer.reset()

        self.frame_timer.update()

    def restart(self):
        self.frame_timer.dt = self.frames[0].dt
        self.frame_timer.reset()
        self.nframe = 0

    def get_frame(self):
        return self.frames[self.nframe]


class AnimationSetInitializer:
    def __init__(self, d=None):
        self.animations = {}
        if d != None:
            self.animations = d

    def new_animation_set_instance(self, name):
        aset = self.animations[name]

        d = {}
        for k in aset.keys():
            frames = []
            for fk in aset[k].keys():
                frame_raw = aset[k][fk]
                f_dt = frame_raw["dt"]
                f_tiles = frame_raw["tiles"]
                fobj = Frame(f_dt, f_tiles)

                frames.append(fobj)

            anim = Animation(frames)
            anim.restart()
            d[k] = anim

        return d


class LabelMgr:
    def __init__(self, w):
        self.labels = []
        self.w = w

    def update(self):
        remove_me = []
        indx = 0
        for l in self.labels:
            l.update()
            if l.timer.ticked:
                remove_me.append(indx)
            indx += 1

        for r in reversed(remove_me):
            self.labels.pop(r)

    def add_label(self, text, x, y, delay=0, color=None):
        if color == None:
            color = "white"
        if color == "white":
            c = 255, 255, 255
        elif color == "red":
            c = 255, 0, 0
        elif color == "green":
            c = 0, 255, 0
        new_label = Label("", text, x, y, self.w, delay=delay, color=c)
        self.labels.append(new_label)


class Label:
    def __init__(self, name, text, x_target, ypos, w, dt=None, color=None, delay=0):
        self.timer = ActionTimer()
        if dt is None:
            self.timer.dt = 0.75
        else:
            self.timer.dt = dt
        self.timer.reset()

        self.delay = delay
        if self.delay != 0:
            self.delay_timer = self.timer = ActionTimer("", delay)

        self.name = name
        self.text = text
        self.x_target = x_target
        self.ypos = ypos
        self.w = w

        if color is None:
            self.color = (255, 255, 255)
        else:
            self.color = color

        self.xpos = 0
        self.alpha = 1

        self.state = "approaching"

    def update(self):
        self.timer.update()

        if self.delay != 0:
            self.delay_timer.update()

            if self.delay_timer.ticked:
                self.delay = 0
                self.timer.reset()
            else:
                self.state = "waiting"
                return

        prog = self.timer.get_progress()
        zt = 0.2
        if prog <= zt:
            i = (prog / zt)
            self.xpos = i
            self.state = "approaching"
        elif prog >= 1 - zt:
            i = (1 - prog) / zt
            self.xpos = i
            self.state = "leaving"
        else:
            self.xpos = self.x_target
            self.state = "stopped"


class Torches:
    def __init__(self):
        self.timer = ActionTimer("torches", 3)

        self.intensities = [(random() * 0.25 + 0.75) for i in range(40)]

    def update(self):
        self.timer.update()
        if self.timer.ticked:
            self.timer.reset()
            shuffle(self.intensities)

    def get_torch_intensity(self, seed):
        t = self.timer.get_progress()
        l = len(self.intensities) - 1

        indx = int(t * l)

        sindx = int(indx + seed[0] + seed[1]) % l

        i = self.intensities[sindx]

        return i


class RenderLogic:
    def __init__(self):
        self.torches = Torches()
        self.prerendered = Prerendering()

    def update(self):
        self.torches.update()


class Prerendering:
    def __init__(self):
        self.rooms = {}
        self.torches = []
        self.darkness = None

        self.skilltree = None

    def add_prerendered_room(self, room, bot_layers_render, top_layers_render):
        d = {
            "bot": bot_layers_render,
            "top": top_layers_render
        }

        self.rooms[room.room_id] = d


class SkillTreeMgr:
    def __init__(self, tree, tw, th, h, g_obj):
        self.g_obj = g_obj

        self.tree = tree

        self.tw, self.th = tw, th

        self.h = h

        self.mover_node = None

        self.stat_points = 0

        self.last_known_level = 0

    def setup(self):
        maxh = self.tree.h * self.th
        for n in self.tree.get_all_nodes():
            gx, gy = n.get_gpos()
            x, y = gx * self.tw, gy * self.th
            r = Rect(x, maxh - y, self.tw, self.th)
            n.rect = r

    def update(self, mpos, mpress, ui, fighting, lkl):
        ui.at_mouse["skill tree node"] = None

        if fighting:
            return

        if not ui.get_selected() == "skill tree":
            return

        if lkl != self.last_known_level:
            self.stat_points += lkl - self.last_known_level
            self.last_known_level = lkl

        at_mouse = ui.at_mouse

        mx, my = mpos[0], mpos[1]

        self.mover_node = None

        for n in self.tree.get_all_nodes():
            if n.rect.collidepoint((mx, my)):
                mover_node = n
                break
        else:
            return

        self.mover_node = mover_node
        ui.at_mouse["skill tree node"] = mover_node

        if mpress[0] != 1:
            return

        if self.stat_points == 0:
            return

        result = self.tree.stat_node(self.mover_node)
        if result:
            self.g_obj.renderlogic.prerendered.skilltree = prerender_skilltree(self.g_obj)
            self.stat_points -= 1
            return self.mover_node

        return


class Loot:
    def __init__(self):
        self.spawner_pos = None, None
        self.target_pos = None, None
        self.pos = None, None
        self.item = None
        self.cost = 0
        self.visible = False

        self.type = None

    def get_pos(self):
        return self.pos

    def update(self, state, i = None):
        if state == "spawning":
            df_pheight = 3
            pheight = math.sin(i * math.pi) * df_pheight
            sx, sy = self.spawner_pos
            tx, ty = self.target_pos
            vx, vy = tx-sx, ty-sy
            ix = sx + vx * i
            iy = sy + vy * i
            self.pos = ix, iy - pheight
        elif state == "spawned":
            self.pos = self.target_pos

def my_weighed_choice(d):
    rand = random()

    S = 0
    for k in d.keys():
        S += d[k]
        if rand <= S:
            return k

class LootSpawner:
    # weapons, shields, gear, syringes
    def __init__(self, pos, available_spots, loot_rating, sound, weapons, use_cost = False, discount = 0):
        self.sound = sound

        self.weapons = weapons
        self.weapon_names = list(self.weapons.keys())

        self.spawn_timer = ActionTimer("", 0.25)
        self.pos = pos
        self.available_spots = available_spots

        self.unspawned = []

        self.spawned = []

        self.use_cost = use_cost
        self.discount = discount

        self.make_some_loot(loot_rating)

        self.done_spawning = False

        self.current_one = None

        self.i = 0
    

    def get_available_spot(self):
        return self.available_spots.pop(0)

    def make_items(self, loot_rating, n_loot_pieces):
        items = []
        cost_estimates = []
        types = []

        item_rating_likelihoods = {
            "common": {"common": 0.8, "rare": 0.15, "legendary": 0.05},
            "rare": {"common": 0.4, "rare": 0.5, "legendary": 0.1},
            "legendary": {"common": 0.2, "rare": 0.5, "legendary": 0.3} # with a guarantee of a legendary in this case
        }

        item_type_likelihoods = {
            "weapon": 0.4,
            "gear": 0.5,
            "shield": 0.1
        }

        quality_likelihoods = {
            "crappy": 0.2,
            "regular": 0.6,
            "good": 0.2
        }

        items_costs = {
            "common": 20,
            "rare": 50,
            "legendary": 150
        }

        item_type_likelihoods["weapon"] = 1 # a little hack, for now

        any_legendary = False

        for n in range(n_loot_pieces):
            rating = my_weighed_choice(item_rating_likelihoods[loot_rating])
            if rating == "legendary":
                any_legendary = True
            quality = my_weighed_choice(quality_likelihoods)
            item_type = my_weighed_choice(item_type_likelihoods)
            if item_type == "weapon":
                types.append("weapon")
                weapon_name = choice(self.weapon_names)
                item = create_weapon(rating, quality, get_new_weapon_instance(weapon_name, self.weapons))
            elif item_type == "gear":
                pass
            elif item_type == "shield":
                pass
            
            items.append(item)

            cost = items_costs[rating]
            if quality == "good":
                cost *= 1.25
            elif quality == "crappy":
                cost *= 0.5

            cost_estimates.append(cost)

        if loot_rating == "legendary" and any_legendary == False:
            items.pop(0)
            cost_estimates.pop(0)

            rating = "legendary"

            quality = my_weighed_choice(quality_likelihoods)
            item_type = my_weighed_choice(item_type_likelihoods)
            if item_type == "weapon":
                types.append("weapon")
                weapon_name = choice(self.weapon_names)
                item = create_weapon(rating, quality, get_new_weapon_instance(weapon_name, self.weapons))
            elif item_type == "gear":
                pass
            elif item_type == "shield":
                pass
            
            items.append(item)

            cost = items_costs[rating]
            if quality == "good":
                cost *= 1.25
            elif quality == "crappy":
                cost *= 0.5

            cost_estimates.append(cost)

        return items, cost_estimates, types

    def make_some_loot(self, loot_rating):
        n_loot_pieces_range = 2, 5
        n_loot_pieces = randint(*n_loot_pieces_range)

        items, cost_estimates, types = self.make_items(loot_rating, n_loot_pieces)

        loot = []
        for item, cost, t in zip(items, cost_estimates, types):
            l = Loot()
            l.item = item
            l.type = t
            if self.use_cost == True:
                l.cost = int(round(cost * (1-self.discount), 0))
            l.spawner_pos = self.pos
            l.target_pos = self.get_available_spot()
            if l.target_pos == None:
                break
            loot.append(l)

        self.unspawned = [i for i in loot]

    def get_positions_of_spawned(self):
        return [i.pos for i in self.spawned]

    def get_pos_of_spawning(self):
        x1, y1 = self.pos
        x2, y2 = self.current_one.pos

        x = x1 + (x2 - x1) * self.i
        y = y1 + (y2 - y1) * self.i

        return x, y

    def get_drawable(self):
        if self.current_one != None:
            return self.spawned + [self.current_one]
        else:
            return self.spawned

    def update(self, mpos, mpress, ui, fighting):
        self.spawn_timer.update()

        if not self.done_spawning:
            if self.spawn_timer.ticked:
                if self.current_one != None:
                    self.spawned.append(self.current_one)

                if len(self.unspawned) != 0:
                    self.current_one = self.unspawned.pop(0)
                    self.i = 0
                    self.spawn_timer.reset()
                    self.sound.play_sound_now("loot spawn")
                else:
                    self.done_spawning = True
                    self.current_one = None
            else:
                self.i = self.spawn_timer.get_progress()

        for n in self.spawned:
            n.update("spawned")
        
        if self.current_one != None:
            self.current_one.update("spawning", self.i)

class LootMgr:
    def __init__(self):
        self.loot_spawners = []

    def new_spawner(self, pos, avail, rating, snd, weapons, use_cost = False, discount = 0):
        ls = LootSpawner(pos, avail, rating, snd, weapons, use_cost = use_cost, discount = discount)
        self.loot_spawners.append(ls)
        return ls

    def update(self, mpos, mpress, ui, fighting):
        for ls in self.loot_spawners:
            ls.update(mpos, mpress, ui, fighting)


class Tooltips:
    def __init__(self):
        self.active_tooltips = []

    def load_tooltips(self, loader, path):
        self.tooltips = loader(path)

    def update(self, mpos, mpress, ui):
        mat = ui.at_mouse
        u = mat["unit"]
        s = mat["skill tree node"]
        e = mat["loot"]
        m = mat["mouse ui item"]

        self.active_tooltips = []

        if u != None:
            for se in u.statuses:
                ttname = se.name.lower()
                section = "Status Effect"
                what = ttname.capitalize()
                title = "{0}: {1}".format(section, what)
                tt = self.tooltips["status effects"][ttname]
                self.active_tooltips.append((title, tt))

        if s != None:
            trans = {
                "stat": "stats",
                "ability": "abilities",
                "mutation": "mutations"
            }

            section = trans[s.node_type.lower()]
            if section == "stats":
                trans_stat = {
                    "str": "strength",
                    "dex": "dexterity",
                    "int": "intelligence"
                }
                what = trans_stat[s.node_is.lower()]
            else:
                what = s.node_is.lower()
            title = "{0}: {1}".format(section.capitalize(), what.capitalize())
            tt = self.tooltips[section][what]
            self.active_tooltips.append((title, tt))

        if e != None:
            section = "equipment"
            what = e.item.weapon_type
            title = "{0}: {1}".format(section.capitalize(), what.capitalize())

            if e.type == "weapon":
                tt_comments = self.tooltips["weapons"][e.item.weapon_type.lower()]
                qual = e.item.quality.capitalize()
                rarity = e.item.rarity

                dmg_range = e.item.base_damage
                fire_range = e.item.range
                crit_chance = e.item.crit * 100

                if qual == "Regular":
                    sign = "+"
                    per = 0
                    mul = 1
                elif qual == "Good":
                    sign = "+"
                    per = 50
                    mul = 1.5
                elif qual == "Crappy":
                    sign = "-"
                    per = 50
                    mul = 0.5

                if e.cost != 0:
                    main_cost = "Cost: {0} bullets\n\n".format(e.cost)
                else:
                    main_cost = ""

                main = "Rarity: {1}\n Quality: {0} ({4}{5}% damage)\n Damage: {2} to {3} ({0} quality)\n Range: {6}\n Crit: {7}%\n\n"
                actual_main = main_cost + main.format(qual, rarity, dmg_range[0]*mul, dmg_range[1]*mul, sign, per, fire_range, crit_chance)

                per_mods = [
                    "Blind",
                    "Burn",
                    "Poison",
                    "Bleed",
                    "Slow",
                    "Knock",
                    "Crit"

                ]

                apply_mods = [
                    "Blind",
                    "Burn",
                    "Poison",
                    "Bleed",
                    "Slow",
                    "Knock"
                ]

                bonus_mods = [
                    "AP",
                    "Crit",
                    "Range"
                ]

                if len(e.item.mods) != 0:
                    mods_text = "Mods:\n"
                    for mod in e.item.mods:
                        name = mod.name.capitalize()
                        if name == "Ap":
                            name = "AP"

                        tier = mod.tier
                        value = mod.value

                        if name in per_mods:
                            percent = "% chance"
                            value_mod = 100
                        else:
                            percent = ""
                            value_mod = 1

                        if name in apply_mods:
                            pretext = "Apply "
                        elif name in bonus_mods:
                            pretext = "Bonus "
                        else:
                            pretext = ""
                        
                        mods_text += "{2}{0}: {1}{3}\n".format(name, value * value_mod, pretext, percent)

                    mods_text += "\n"
                else:
                    mods_text = ""

                tt = actual_main + mods_text + tt_comments

            self.active_tooltips.append((title, tt))