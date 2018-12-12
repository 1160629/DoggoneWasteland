import pygame
from ui import *
from logic import *
import events
from game_loader import load_b

def update(self):
    # get input
    mpos = pygame.mouse.get_pos()
    mpress = pygame.mouse.get_pressed()

    # update stuff
    self.sound.update()
    self.music.current_stage = self.stage
    self.music.update()

    self.ui.update(mpos, mpress, self)
    self.menu.update(mpos, mpress, self.ui)
    # print(self.ui.at_mouse["walkable"])

    # print(self.ui.at_mouse)

    px, py = self.mc.pos
    centerpos = -(px * self.tw - int(self.w / 2)), -(py * self.th - int(self.h / 2))
    rw, rh = self.rw, self.rh
    gx, gy = self.dungeon.get_room().grid_pos
    tw, th = self.tw, self.th

    roomcenterpos = -(rw * gx * tw - self.w//2 + (rw * tw) // 2), -(rh * gy * th - self.h // 2 + (rh * th) // 2)
    self.cam.update(mpos, mpress, centerpos, roomcenterpos, self.ui)
    # print(self.cam.get())
    self.renderlogic.update()

    self.cc.update(self)

    self.labels.update()

    fighting = self.cc.state != "out of combat"
    lkl = self.mc.level
    result = self.skilltree_mgr.update(mpos, mpress, self.ui, fighting, lkl)
    if result != None:
        self.mc.new_skill(result)

    self.dungeon.update((px, py), self, mpos, mpress, self.ui, fighting)

    self.lootmgr.update(mpos, mpress, self.ui, fighting)

    self.tooltips.update(self, mpos, mpress, self.ui)
    
    self.effmgr.update(self, mpos, mpress, self.ui)

    units_turn = self.cc.get_current_unit()
    if self.cc.start_of_turn == True and units_turn != None:
        units_turn.start_turn()
    else:
        pass

    for u in self.units:
        u.current_room = self.dungeon.get_room()
        if units_turn != None and u == units_turn:
            yourturn = True
        else:
            yourturn = False
        at_mouse = self.ui.at_mouse
        if u.has_controller:
            u.controller.update(self, self.mc, mpos, mpress, self.ui, fighting)
            con_act = u.controller.con_act
            #at_mouse = {"units": [[],[],[],[],[],[],[],[]], "unit": None, "mapped": (0, 0), \
            #"mouse ui item": None, "loot": None, "walkable": None, "tiles": None, "room": None, \
            #"ui mouseover": None}
            at_mouse["ui mouseover"] = None
        else:
            con_act = {"do": "nothing"}
        u.update(mpos, mpress, at_mouse, yourturn, self.ui, self.cc.use_list, self.lootmgr, con_act)
        if u.get_path:
            if u.has_controller:
                nx, ny = u.controller.l_move_con_act["dest"]
            else:
                nx, ny = at_mouse["mapped"]
            room = self.dungeon.which_room(u, self)
            rw, rh = self.rw, self.rh
            gx, gy = room.grid_pos
            rx = nx - gx * rw
            ry = ny - gy * rh
            print(rx, ry)
            walkable_map = create_walkable_matrix(room, self.units, u, self)
            self.walkable_map = walkable_map
            node_map = get_node_map(walkable_map)
            sx, sy = u.pos
            rsx = sx - gx * rw + rw
            rsy = sy - gy * rh + rh
            # print(rsx, rsy)
            start_node = node_map[rsx][rsy]
            ex, ey = rx + rw, ry + rh
            if 0 <= ex <= len(node_map) and 0 <= ey <= len(node_map[ex]):
                end_node = node_map[ex][ey]
                path = A_Star(start_node, end_node)
                if path != None:
                    conv_path_rel = list(reversed(list(map(lambda n: n.pos, path))))
                    conv_path_rel.pop(0)
                    conv_path_abs = list()
                    for x, y in conv_path_rel:
                        ax = x + gx * rw - rw
                        ay = y + gy * rh - rh
                        apos = ax, ay
                        conv_path_abs.append(apos)
                    u.path = conv_path_abs
                u.get_path = False
                u.first_move = True
            else:
                path = None
                u.get_path = False

    # misc pygame logic - if user exits window, fps limiter

    self.back_to_top = False
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            # save logic
            pygame.quit()
            self.quit = True
        if e.type == events.NEWGAMEEVENT:
            load_b(self)
            self.back_to_top = True
        if e.type == events.EXITMENUEVENT:
            self.ui.set_selected(None)

    self.clock.tick(self.fps)

    pygame.display.set_caption(str(int(self.clock.get_fps())))
