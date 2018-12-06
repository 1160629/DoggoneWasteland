from logic import Rect, in_range
from control import ActionTimer, Animation
import pygame
from events import NEWGAMEEVENT


# User interface


# camera class; keeps track of an offset, which is used in drawing

class Camera:
    def __init__(self, w, h):
        self.x, self.y = 0, 0
        self.w, self.h = w, h

        self.update_step = 1

        cw, ch = 180, 180

        self.cw, self.ch = cw, ch

        self.border_left = Rect((0, 0), (cw, h))
        self.border_bot = Rect((0, h - ch), (w, ch))
        self.border_right = Rect((w - cw, 0), (cw, h))
        self.border_top = Rect((0, 0), (w, ch))

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
                D = ((1 - ((self.w - mx)) / self.cw) * 3) ** 2.5
            elif v == (0, -1):
                D = ((((self.ch - my)) / self.ch) * 3) ** 2.5
            elif v == (0, 1):
                D = ((1 - (self.h - my) / self.ch) * 3) ** 2.5
            else:
                D = 1
            self.x, self.y = self.x + -1 * v[0] * self.update_step * D, self.y + -1 * v[1] * self.update_step * D

    def get(self):
        return int(self.x), int(self.y)


# Basic combat interace

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

        x, y = x - self.draw_x, y - self.draw_y

        mouseover = False
        curr_select = False
        if self.box.collidepoint((x, y)):
            mouseover = True
            if self.select_timer.ticked and mpress[0] == 1:
                curr_select = True
                self.selected = True - self.selected
                self.select_timer.reset()

        if self.selected:
            self.anim = self.animations["sel"]
        else:
            self.anim = self.animations["desel"]

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


def create_ui_interactive(self, g_obj):
    # set commands for creating UI

    creation_commands = [
        ["uielement", "end turn", "uibtn_endturn"],
        ["spacing"],
        ["uielement", "move", "uibtn_move"],
        ["spacing"],
        ["uielement", "right hand", "uibtn_righthand"],
        ["spacing"],
        ["uielement", "left hand", "uibtn_lefthand"],
        ["spacing"]
    ]

    for i in range(5):
        command_name = "ability {0}".format(str(i + 1))
        animation_name = "uibtn_ability"

        gen_command = ["uielement", command_name, animation_name]

        creation_commands.append(gen_command)

    creation_commands.append(["spacing"])

    for i in range(5):
        command_name = "syringe {0}".format(str(i + 1))
        animation_name = "uibtn_syringe"

        gen_command = ["uielement", command_name, animation_name]

        creation_commands.append(gen_command)

    # now initialize it

    ui_start_x, ui_start_y = 0, g_obj.h - 0
    ui_x = ui_start_x
    ui_y = ui_start_y

    ui_w, ui_h = 16 * g_obj.scaling, 16 * g_obj.scaling  # scaled tile size

    ui_b = 0  # border
    ui_s = 8  # spacing value

    for command in creation_commands:
        if command[0] == "uielement":
            name, animation_name = command[1:]
            ele = UIInteractiveElement()
            ele.box = Rect(ui_x, ui_y, ui_w, ui_h)
            ele.animations = g_obj.animations.new_animation_set_instance(animation_name)
            self.ui_elements[name] = ele
            ui_x += ui_w
        elif command[0] == "spacing":
            ui_x += ui_s

        ui_x += ui_b


class UIInformational:
    def __init__(self):
        pass

    def update(self, mpos, mpress, at_mouse):
        pass


class UI:
    def __init__(self, g_obj):
        self.ui1 = UIInteractive(g_obj)
        create_ui_interactive(self.ui1, g_obj)
        self.ui2 = UIInformational()

        self.at_mouse = None

    def update(self, mpos, mpress, g_obj):
        self.at_mouse = get_mouse_hover(g_obj, mpos)
        self.ui2.update(mpos, mpress, self.at_mouse)
        mouseover = self.ui1.update(mpos, mpress, self.at_mouse)
        self.at_mouse["ui mouseover"] = mouseover

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


class PauseButton:

    def __init__(self, text):
        self.text = text
        self.rect = None

    def on_mouse_click(self):
        pass


class NewGameButton(PauseButton):
    def __init__(self):
        text = "New Game"
        PauseButton.__init__(self, text)

    def on_mouse_click(self):
        pygame.event.post(pygame.event.Event(NEWGAMEEVENT))


class ContinueButton(PauseButton):
    def __init__(self):
        text = "Continue"
        PauseButton.__init__(self, text)


class ExitButton(PauseButton):
    def __init__(self):
        text = "Exit"
        PauseButton.__init__(self, text)

    def on_mouse_click(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))


class Menu:
    def __init__(self, g_obj):
        self.menu_items = []
        # instantiate buttons
        self.menu_items.append(NewGameButton())
        self.menu_items.append(ContinueButton())
        self.menu_items.append(ExitButton())
        self.menu_items.reverse()

        self.timer = ActionTimer("", 0.25)

    def update(self, mpos, mpress, ui):
        self.timer.update()

        if mpress[0] == 0 or not ui.get_selected("in game menu"):
            return

        for mi in self.menu_items:
            if mi.rect == None:
                continue
            if mi.rect.collidepoint(mpos) and self.timer.ticked:
                mi.on_mouse_click()
                self.timer.reset()


# mouse cursor logic

def map_mpos(g_obj, mpos):
    room = g_obj.dungeon.get_room()
    ox, oy = g_obj.cam.get()

    tw, th = g_obj.tilesets.tw, g_obj.tilesets.th

    mw, mh = room.layout.w, room.layout.h

    bs, g_obj.scale = g_obj.scale, 1

    mx = ((mpos[0] // g_obj.scale - ox) // (tw))
    my = ((mpos[1] // g_obj.scale - oy) // (th))

    g_obj.scale = bs

    inside = False
    if ((0 <= mx < mw) and (0 <= my < mh)):
        inside = True

    return (mx, my), inside


def get_tiles_at_and_walkable(g_obj, mpos_mapped):
    nx, ny = mpos_mapped

    room = g_obj.dungeon.get_room()
    tile_walkable = room.walkable_map[nx][ny]
    layout = room.layout
    tile_indexes = [layout.get_tile_index(k, nx, ny) for k in layout.layers.keys()]

    return tile_indexes, tile_walkable


def get_mouse_hover(g_obj, mpos):
    at_mouse = {}

    # map the mouse position to a tile
    # and see if it's inside the room
    mpos_mapped, inside = map_mpos(g_obj, mpos)
    at_mouse["mapped"] = mpos_mapped

    # get unit at the tile
    at_mouse["unit"] = None
    for u in g_obj.units:
        if u.pos == mpos_mapped:
            at_mouse["unit"] = u

    # create a list of units within various ranges
    # from the tile
    units = []
    for rad in range(1, 8):
        units.append([])
        for u in g_obj.units:
            if in_range(u.pos, mpos_mapped, rad):
                units[-1].append(u)

    at_mouse["units"] = units

    # get the tile index, from each layer
    # and whether it is walkable or not
    if inside:
        tiles, walkable = get_tiles_at_and_walkable(g_obj, mpos_mapped)
    else:
        tiles = []
        walkable = False

    # if there is a unit occupying the tile
    # then it is not walkable
    if at_mouse["unit"] != None:
        walkable = False

    at_mouse["tiles"] = tiles
    at_mouse["walkable"] = walkable

    return at_mouse


def create_buttons(g_obj):
    # add buttons
    g_obj.pause_buttons
