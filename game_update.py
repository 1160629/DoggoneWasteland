import pygame
from ui import *
from logic import *

def update(self):
    # get input
    mpos = pygame.mouse.get_pos()
    mpress = pygame.mouse.get_pressed()

    # update stuff
    self.ui.update(mpos, mpress, self)
    #print(self.ui.at_mouse["walkable"])

    self.cam.update(mpos)
    self.cc.update()

    units_turn = self.cc.get_current_unit()
    for u in self.units:
        if u == units_turn:
            yourturn = True
        else:
            yourturn = False
        at_mouse = self.ui.at_mouse
        u.update(mpos, mpress, at_mouse, yourturn, self.ui)
        if u.get_path:
            walkable_map = create_walkable_matrix(self.dungeon.get_room().walkable_map, self.units, u)
            node_map = get_node_map(walkable_map)
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

    # misc pygame logic - if user exits window, fps limiter

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            self.quit = True

    self.clock.tick(self.fps)