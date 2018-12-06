import pygame
from ui import *
from logic import *


def update(self):
    # get input
    mpos = pygame.mouse.get_pos()
    mpress = pygame.mouse.get_pressed()

    # update stuff
    self.sound.update()
    self.music.current_stage = self.stage
    self.music.update()

    self.ui.update(mpos, mpress, self)
    #print(self.ui.at_mouse["walkable"])

    #print(self.ui.at_mouse)

    px, py = self.mc.pos
    centerpos = -(px * self.tw - int(self.w/2)), -(py * self.th - int(self.h/2))
    self.cam.update(mpos, mpress, centerpos, self.ui)
    #print(self.cam.get())
    self.renderlogic.update()

    self.cc.update()

    self.labels.update()

    fighting = self.cc.state == "in combat"
    lkl = self.mc.level
    result = self.skilltree_mgr.update(mpos, mpress, self.ui, fighting, lkl)
    if result != None:
        self.mc.new_skill(result)

    self.dungeon.update((px, py), self, mpos, mpress, self.ui, fighting)

    self.tooltips.update(mpos, mpress, self.ui)

    units_turn = self.cc.get_current_unit()
    if self.cc.start_of_turn == True:
        units_turn.start_turn()
    else:
        pass

    for u in self.units:
        u.current_room = self.dungeon.get_room()
        if u == units_turn:
            yourturn = True
        else:
            yourturn = False
        at_mouse = self.ui.at_mouse
        u.update(mpos, mpress, at_mouse, yourturn, self.ui, self.cc.units_in_combat)
        if u.get_path:
            nx, ny = at_mouse["mapped"]
            room = self.dungeon.which_room(u, self)
            rw, rh = self.rw, self.rh
            gx, gy = room.grid_pos
            rx = nx - gx * rw
            ry = ny - gy * rh
            walkable_map = create_walkable_matrix(room, self.units, u, at_mouse, self)
            self.walkable_map = walkable_map
            node_map = get_node_map(walkable_map)
            sx, sy = u.pos
            rsx = sx - gx * rw + rw
            rsy = sy - gy * rh + rh
            #print(rsx, rsy)
            start_node = node_map[rsx][rsy]
            ex, ey = rx+rw, ry+rh
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

    # misc pygame logic - if user exits window, fps limiter

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            self.quit = True

    self.clock.tick(self.fps)
    pygame.display.set_caption(str(int(self.clock.get_fps())))