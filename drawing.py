import pygame
from itertools import product
from logic import Rect

# functions for drawing

def update_display():
    pygame.display.update()

def draw_units(g_obj):
    dung = g_obj.dungeon
    room = dung.get_room()

    tw, th = room.tilesets.tw, room.tilesets.th

    ox, oy = g_obj.cam.get()

    for u in g_obj.units:
        img = g_obj.tilesets.get_tile(*u.current_animation().get_frame()).image
        
        x, y = u.anim_pos
        rx, ry = ox+x*tw, oy+y*th


        # direction that unit is facing
        if -1 != u.direction:
            xbool = 1
        else:
            xbool = 0
        uimg = pygame.transform.flip(img, xbool, 0)

        # if the unit is dead, draw it sideways
        if u.state == "dead":
            uimg = pygame.transform.rotate(uimg, 90)

        # melee attack
        aox, aoy = 0, 0
        if u.state == "attacking" and u.attack_weapon.attack_type == "melee":
            aox, aoy = u.projectile_pos

        g_obj.swin.blit(uimg, (rx+aox, ry+aoy))

def draw_dungeon_layer(g_obj, name, wmap = None):
    dung = g_obj.dungeon
    room = dung.get_room()
    layer = room.layout.get_layer(name)
    ox, oy = g_obj.cam.get()

    sw, sh = g_obj.w, g_obj.h

    x, y = ox, oy
    tw, th = room.tilesets.tw, room.tilesets.th
    nx, ny = 0, 0

    mw, mh = room.layout.w, room.layout.h

    buffer = max((2*tw, 2*th))
    screen_rect = Rect(-buffer, -buffer, sw+buffer*2, sh+buffer*2)

    #somesurf_red = g_obj.nwsurf
    #somesurf_green = g_obj.wsurf

    for tx, ty, n in product(range(mw), range(mh), room.layout.layers.keys()):
        if n != name: # draw only specified layer
            continue
        tile_index = room.layout.get_tile_index(n, tx, ty)
        if tile_index == None: # transparent tile
            continue
        tile = room.tilesets.get_tile(*tile_index)
        x, y = tx * tw + ox, ty * th + oy
        cr = Rect(x, y, tw, th)
        if not screen_rect.colliderect(cr):
            continue
        g_obj.swin.blit(tile.image, (x, y))
        #if wmap != None:
        #    if 0 <= tx < len(wmap) and 0 <= ty < len(wmap[0]):
        #        walkable = wmap[tx][ty]
        #        if walkable:
        #            g_obj.swin.blit(somesurf_green, (x, y))
        #        else:
        #            g_obj.swin.blit(somesurf_red, (x, y))

def f_flat(f):
    rtw = 16
    ind = f%rtw, f//rtw
    return ind

def draw_projectiles(g_obj):
    cu = g_obj.cc.get_current_unit()
    if not (cu.state == "attacking"):
        return

    proj_tset = "set1"
    bomb_frame = f_flat(47+16) # + 16*4-1, + 16*4-2
    arrow_frame = f_flat(166)
    bullet_frame = f_flat(166+16*3)

    ox, oy = g_obj.cam.get()
    x, y = cu.projectile_pos
    if cu.attack_weapon.attack_type == "bomb":
        img = get_tile_img(g_obj, proj_tset, bomb_frame)
        g_obj.swin.blit(img, (x*g_obj.scaling*16+ox, y*g_obj.scaling*16+oy))
        
    elif cu.attack_weapon.attack_type == "shot":
        if cu.attack_weapon.projectile_type == "arrow":
            img = get_tile_img(g_obj, 1, arrow_frame)
        elif cu.attack_weapon.projectile_type == "bullet":
            img = get_tile_img(g_obj, 1, bullet_frame)
        
        img = pygame.transform.rotate(img, 90-cu.projectile_angle)

        g_obj.swin.blit(img, (x*g_obj.scale*16+ox, y*g_obj.scale*16+oy))


def draw_labels(g_obj):
    labs = g_obj.labels

    font = g_obj.font

    ox, oy = g_obj.cam.get()

    w = g_obj.w

    for l in labs:
        x, y = l.xpos * w + ox, l.ypos + oy

        img = font.render(l.text, 1, l.color)
        g_obj.swin.blit(img, (x, y))


def get_tile_img(g_obj, tileset, tilenr):
    tile = g_obj.tilesets.get_tile(tileset, tilenr[0], tilenr[1])
    tile_img = tile.image
    return tile_img

def draw_combat_ui(g_obj):
    # draw informational ui

    turns_w = int(g_obj.w/2) - int(16*g_obj.scaling * 4.5)
    turns_h = 16*g_obj.scale

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
        img = g_obj.tilesets.get_tile(*f).image

        px += 16*g_obj.scaling
        g_obj.swin.blit(img, (px, py))

        if i == draw_turns:
            break
        

    cu = g_obj.cc.get_current_unit()
    if g_obj.ui.at_mouse["unit"] != None:
        cu = g_obj.ui.at_mouse["unit"] 
    ca = int(cu.ap.current_ap)
    ta = cu.ap.get_ap()
    #if ta % 1 > 0:
        #ta = (round(ta + 0.5))
    ta = int(ta)
    
    ap_green = get_tile_img(g_obj, "set1", f_flat(216))
    ap_yellow = get_tile_img(g_obj, "set1", f_flat(218))

    x_spot = 128 * 5 + 16*g_obj.scaling

    uiinfo_w = 16

    apx = x_spot
    apy = 16*g_obj.scaling + 64

    for i in range(0, uiinfo_w*ca, uiinfo_w):
        g_obj.swin.blit(ap_yellow, (apx+i, apy))
    for i in range(0, uiinfo_w*ta, uiinfo_w):
        g_obj.swin.blit(ap_green, (apx+i, apy))

    
    mhp = cu.get_health()
    dmg = cu.damage_taken
    hp = mhp - dmg
    
    h_repr = 5

    hpx = g_obj.w - x_spot - 16
    hpy = 16*g_obj.scaling + 64

    hp_red = get_tile_img(g_obj, "set1", f_flat(215))
    hp_yellow = ap_yellow

    for i in range(0, uiinfo_w*h_repr, uiinfo_w):
        g_obj.swin.blit(hp_yellow, (hpx-i, hpy))
    for i in range(0, uiinfo_w*int((h_repr*hp)/mhp), uiinfo_w):
        g_obj.swin.blit(hp_red, (hpx-i, hpy))

    midx = (apx + hpx) // 2
    img = g_obj.tilesets.get_tile(*cu.animations["standing"].frames[0]).image
    g_obj.swin.blit(img, (midx, hpy))

    # draw interactive ui
    ui_ = g_obj.ui.ui1
    for k in ui_.ui_elements.keys():
        ele = ui_.ui_elements[k]

        pos = ele.box.topleft
        f = ele.get_frame()
        img = g_obj.tilesets.get_tile(*f).image
        draw_x = int(g_obj.cam.cw/2) + 64
        draw_y = - int(g_obj.cam.ch/2) - 128 - 32 + 8*g_obj.scaling
        ele.draw_x = draw_x
        ele.draw_y = draw_y
        
        g_obj.swin.blit(img, (pos[0] + draw_x, pos[1] + draw_y))

def draw_menus(self):
    pass