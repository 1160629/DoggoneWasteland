from time import clock
from math import pi, sin
from random import random, shuffle, randint
from logic import Rect
from prerendering import prerender_skilltree


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
            pass  # return

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
        self.pos = None, None
        self.item = None

    def update(self):
        pass


class LootSpawner:
    # weapons, shields, gear, syringes
    def __init__(self, pos, available_spots):
        self.spawn_timer = ActionTimer("", 0.5)
        self.pos = pos
        self.available_spots = available_spots

        self.loot = []

        self.unspawned = []

        self.spawned = []

        self.make_some_loot()

        self.done_spawning = False

    def get_available_spot(self):
        self.available_spots.pop(0)

    def make_some_loot(self, loot_rating):
        n_loot_pieces_range = 2, 5
        n_loot_pieces = randint(*n_loot_pieces_range)
        for n in range(n_loot_pieces):
            l = Loot()
            l.item = None
            l.pos = self.get_available_spot()
            if l.pos == None:
                break
            self.loot.append(l)

        self.unspawned = [i for i in self.loot]

    def get_positions_of_spawned(self):
        return [i.pos for i in self.spawned]

    def get_pos_of_spawning(self):
        x1, y1 = self.pos
        x2, y2 = self.current_one.pos

        x = x1 + (x2 - x1) * self.i
        y = y1 + (y2 - y1) * self.i

        return x, y

    def get_positions_of_loot(self):
        return [i.pos for i in self.loot]

    def update(self, mpos, mpress, ui, fighting):
        if not self.done_spawning:
            if self.spawn_timer.ticked():
                self.spawned.append(self.current_one)

                if len(self.loot) != 0:
                    self.current_one = self.unspawned.pop(0)
                    self.spawn_timer.reset()
                else:
                    self.done_spawning = True
            else:
                self.i = self.spawn_timer.get_progress()
        else:
            pass  # loot pickup logic


class LootMgr:
    def __init__(self):
        pass


class Tooltips:
    def __init__(self):
        self.active_tooltips = []

    def load_tooltips(self, loader, path):
        self.tooltips = loader(path)

    def update(self, mpos, mpress, ui):
        mat = ui.at_mouse
        u = mat["unit"]
        s = mat["skill tree node"]

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
