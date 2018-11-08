from drawing import *

def draw(self):
    # clear surface -- draw everything black
    self.swin.fill((0, 0, 0))

    # draw floors and decorative layers
    draw_dungeon_layer(self, "Floors")
    draw_dungeon_layer(self, "Dirt")

    # units drawn on top of floors, but beneath walls and other decorative layers
    draw_units(self)

    # draw walls, other collidables, and decorative layers
    draw_dungeon_layer(self, "Walls")
    draw_dungeon_layer(self, "Skullz")
    
    # draw projectiles over tiles & units
    draw_projectiles(self)

    # draw ui over everything thus far
    draw_combat_ui(self)

    # and menus over everything
    draw_menus(self)
    
    # put on display surface, and update
    self.win.blit(self.swin, (0, 0))
    update_display()