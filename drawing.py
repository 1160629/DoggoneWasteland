import pygame
from itertools import product
from logic import Rect, in_range, get_distance
from units import get_selected_ability
from math import radians


# functions for drawing

def update_display():
    pygame.display.update()


def draw_units(g_obj):
    dung = g_obj.dungeon
    room = dung.get_room()

    tw, th = room.tilesets.tw, room.tilesets.th

    ox, oy = g_obj.cam.get()

    for u in g_obj.units:
        frame = u.current_animation().get_frame()
        images = []
        for f in frame.tiles:
            ind, to = f[:3], f[3:]
            image = g_obj.tilesets.get_tile(*ind).image
            images.append((image, to))

        x, y = u.anim_pos
        rx, ry = ox + x * tw, oy + y * th

        x, y = u.anim_pos
        rx, ry = ox + x * tw, oy + y * th

        # direction that unit is facing
        if 1 != u.direction:
            xbool = 1
        else:
            xbool = 0
        uimgs = [(pygame.transform.flip(img, xbool, 0), to) for img, to in images]

        # if the unit is dead, draw it sideways
        if u.state == "dead" or u.knocked or u.state == "resting":
            uimgs = [(pygame.transform.rotate(uimg, 90), to) for uimg, to in uimgs]

        # melee attack
        aox, aoy = 0, 0
        if (u.state == "attacking" and u.attack_weapon.attack_type == "melee") or u.dashing:
            aox, aoy = u.projectile_pos

        for i, to in uimgs:
            tx, ty = to
            g_obj.swin.blit(i, (rx + aox + tx * tw, ry + aoy + ty * th * -1))


def draw_dungeon_nlayers(g_obj, nlayers):
    rl = g_obj.renderlogic

    pre = rl.prerendered

    pr = pre.rooms

    dung = g_obj.dungeon

    for room in dung.get_rooms():
        gx, gy = room.grid_pos

        tw, th = room.tilesets.tw, room.tilesets.th

        rw, rh = g_obj.rw, g_obj.rh
        raw, rah = rw * tw, rh * th

        ox, oy = g_obj.cam.get()

        rx, ry = gx * raw + ox, gy * rah + oy

        sw, sh = g_obj.w, g_obj.h

        buffer = max((2 * tw, 2 * th))
        screen_rect = Rect(-buffer, -buffer, sw + buffer * 2, sh + buffer * 2)

        room_rect = Rect(rx, ry, raw, rah)
        # print(room_rect.topleft)

        if not (screen_rect.colliderect(room_rect)):
            continue

        in_this_room = dung.get_room().room_id == room.room_id

        x, y = ox, oy
        nx, ny = 0, 0

        mw, mh = room.layout.w, room.layout.h

        floors_img = pr[room.room_id][nlayers]

        g_obj.swin.blit(floors_img, (rx, ry))


def draw_dungeon_botlayers(g_obj):
    draw_dungeon_nlayers(g_obj, "bot")


def draw_dungeon_toplayers(g_obj):
    draw_dungeon_nlayers(g_obj, "top")


def lighting_pass(g_obj):
    dung = g_obj.dungeon

    for room in dung.get_rooms():
        gx, gy = room.grid_pos

        tw, th = room.tilesets.tw, room.tilesets.th

        rw, rh = g_obj.rw, g_obj.rh
        raw, rah = rw * tw, rh * th

        rx, ry = gx * raw, gy * rah

        sw, sh = g_obj.w, g_obj.h

        buffer = max((2 * tw, 2 * th))
        screen_rect = Rect(-buffer, -buffer, sw + buffer * 2, sh + buffer * 2)

        ox, oy = g_obj.cam.get()

        room_rect = Rect(rx + ox, ry + oy, raw, rah)
        # print(room_rect.topleft)

        if not (screen_rect.colliderect(room_rect)):
            continue

        in_this_room = dung.get_room().room_id == room.room_id

        x, y = ox, oy
        nx, ny = 0, 0

        mw, mh = room.layout.w, room.layout.h

        if not in_this_room:
            g_obj.swin.blit(g_obj.renderlogic.prerendered.darkness, (rx + ox, ry + oy))

        tindx_x_l = [8, 9, 10, 11, 12, 13, 14, 15]
        tindx_y = 9

        torches = []

        for tx, ty, n in product(range(mw), range(mh), room.layout.layers.keys()):
            add_torch = False
            if n == "Torches":
                tile_index = room.layout.get_tile_index(n, tx, ty)
                if tile_index != None:  # transparent tile
                    # tile = room.tilesets.get_tile(*tile_index)
                    tilex, tiley = tile_index[1:]
                    # print(tilex, tiley)
                    if tindx_y == tiley and tilex in tindx_x_l:
                        add_torch = True
            x, y = tx * tw + ox + rx, ty * th + oy + ry
            if add_torch:
                torches.append((x, y))

        for t in torches:
            xt, yt = t
            tseed = (t[0], t[1])
            tintensity = g_obj.renderlogic.torches.get_torch_intensity(tseed)

            actual_intensity = int(tintensity * 60)

            torch_img = g_obj.renderlogic.prerendered.torches[actual_intensity]

            g_obj.swin.blit(torch_img, (int(xt - tw * 2.5), int(yt - th * 2)))


def f_flat(f):
    rtw = 16
    ind = f % rtw, f // rtw
    return ind


def draw_projectiles(g_obj):
    cu = g_obj.cc.get_current_unit()
    if cu == None or not (cu.state == "attacking" or cu.state == "casting"):
        return

    proj_tset = "main_set"
    bomb_frame = f_flat(351)  # + 16*4-1, + 16*4-2
    arrow_frame = f_flat(300)
    bullet_frame = f_flat(299)

    if cu.state == "attacking":
        ox, oy = g_obj.cam.get()
        x, y = cu.projectile_pos
        if cu.attack_weapon.attack_type == "bomb":
            img = get_tile_img(g_obj, proj_tset, bomb_frame)
            g_obj.swin.blit(img, (x * g_obj.scale * 16 + ox, y * g_obj.scale * 16 + oy))

        elif cu.attack_weapon.attack_type == "shot":
            if cu.attack_weapon.projectile_type == "arrow":
                img = get_tile_img(g_obj, proj_tset, arrow_frame)
            elif cu.attack_weapon.projectile_type == "bullet":
                img = get_tile_img(g_obj, proj_tset, bullet_frame)

            img = pygame.transform.rotate(img, 90 - cu.projectile_angle)

            g_obj.swin.blit(img, (x * g_obj.scale * 16 + ox, y * g_obj.scale * 16 + oy))
    elif cu.state == "casting" and cu.casting_projectile:
        ox, oy = g_obj.cam.get()
        x, y = cu.projectile_pos
        if cu.attack_type == "bomb":
            img = get_tile_img(g_obj, proj_tset, bomb_frame)
            g_obj.swin.blit(img, (x * g_obj.scale * 16 + ox, y * g_obj.scale * 16 + oy))

        elif cu.attack_type == "shot":
            if cu.projectile_type == "arrow":
                img = get_tile_img(g_obj, proj_tset, arrow_frame)
            elif cu.projectile_type == "bullet":
                img = get_tile_img(g_obj, proj_tset, bullet_frame)

            img = pygame.transform.rotate(img, 90 - cu.projectile_angle)

            g_obj.swin.blit(img, (x * g_obj.scale * 16 + ox, y * g_obj.scale * 16 + oy))


def draw_labels(g_obj):
    labs = g_obj.labels

    font = g_obj.font

    ox, oy = g_obj.cam.get()

    tw, th = g_obj.tw, g_obj.th
    tile_hw, tile_hh = int(tw / 2), int(th / 2)

    w, h = g_obj.w, g_obj.h

    for l in labs.labels:
        if l.state == "stopped":
            x, y = l.xpos * tw + ox, l.ypos * th + oy
        elif l.state == "approaching":
            x, y = 0 + (l.x_target * tw + ox) * l.xpos, l.ypos * th + oy
        elif l.state == "leaving":
            x, y = (l.x_target * tw + ox) + (w - (l.x_target * tw + ox)) * (1 - l.xpos), l.ypos * th + oy
        elif l.state == "waiting":
            continue
        else:
            x, y = 0, -100

        img = font.render(l.text, 1, l.color)
        text_hw = int(img.get_width() / 2)
        text_hh = int(img.get_height() / 2)
        g_obj.swin.blit(img, (x - text_hw + tile_hw, y - text_hh + tile_hh))


def get_tile_img(g_obj, tileset, tilenr):
    tile = g_obj.tilesets.get_tile(tileset, tilenr[0], tilenr[1])
    tile_img = tile.image
    return tile_img


def draw_combat_ui(g_obj):
    # draw informational ui

    tw, th = g_obj.tw, g_obj.th

    turns_w = int(g_obj.w / 2) - int(16 * g_obj.scale * 4.5)
    turns_h = 16 * g_obj.scale

    px, py = turns_w, turns_h

    draw_turns = 8
    units = g_obj.cc.use_list
    n = g_obj.cc.turn
    i = 0
    while len(units) > 0:
        unit = units[n]
        n += 1
        if n >= len(units):
            n = 0
        if unit.state == "dead":
            continue

        i += 1

        f = unit.animations["Idle"].get_frame()

        frame = unit.animations["Idle"].get_frame()
        images = []
        for f in frame.tiles:
            ind, to = f[:3], f[3:]
            image = g_obj.tilesets.get_tile(*ind).image
            images.append((image, to))

        px += 16 * g_obj.scale

        for img, to in images:
            tx, ty = to
            g_obj.swin.blit(img, (px + tx * tw, py + ty * th * -1))

        if i == draw_turns:
            break

    # draw ap and hp for the unit the is mouse overed, 
    # otherwise draw the one that's currently taking his turn

    cu = g_obj.cc.get_current_unit()
    if g_obj.ui.at_mouse["unit"] != None:
        cu = g_obj.ui.at_mouse["unit"]

    if cu != None:
        ca = int(cu.ap.current_ap)
        ta = cu.ap.get_ap()
        # if ta % 1 > 0:
        # ta = (round(ta + 0.5))
        ta = int(ta)

        ap_green = get_tile_img(g_obj, "main_set", f_flat(254))
        ap_yellow = get_tile_img(g_obj, "main_set", f_flat(255))

        x_spot = 128 * 5 + 16 * g_obj.scale

        uiinfo_w = 16

        apx = x_spot

        apy = 16 * g_obj.scale + 64

        for i in range(0, uiinfo_w * ca, uiinfo_w):
            g_obj.swin.blit(ap_yellow, (apx + i, apy))
        for i in range(0, uiinfo_w * ta, uiinfo_w):
            g_obj.swin.blit(ap_green, (apx + i, apy))

        mhp = cu.get_health()
        dmg = cu.damage_taken
        hp = mhp - dmg

        h_repr = 5

        hpx = g_obj.w - x_spot - 16

        hpy = 16 * g_obj.scale + 64

        hp_red = get_tile_img(g_obj, "main_set", f_flat(252))
        hp_yellow = ap_yellow

        for i in range(0, uiinfo_w * h_repr, uiinfo_w):
            g_obj.swin.blit(hp_yellow, (hpx - i, hpy))
        for i in range(0, uiinfo_w * int((h_repr * hp) / mhp + 0.5), uiinfo_w):
            g_obj.swin.blit(hp_red, (hpx - i, hpy))

        statuses = cu.statuses

        # draw the dude under mouse position

        frame = cu.current_animation().get_frame()
        images = []
        for f in frame.tiles:
            ind, to = f[:3], f[3:]
            image = g_obj.tilesets.get_tile(*ind).image
            images.append((image, to))

        midx = (apx + hpx) // 2
        for i, to in images:
            tx, ty = to
            g_obj.swin.blit(i, (midx + tx * tw, hpy + ty * th * -1))

    gray = 100, 100, 100
    blue = 135, 206, 250

    # draw interactive ui
    ui_ = g_obj.ui.ui1
    for k in ui_.ui_elements.keys():
        ele = ui_.ui_elements[k]

        pos = ele.box.topleft

        frame = ele.get_frame()
        images = []
        for f in frame.tiles:
            ind, to = f[:3], f[3:]
            image = g_obj.tilesets.get_tile(*ind).image
            images.append((image, to))

        for i, to in images:
            tx, ty = to
            # draw_x = int(g_obj.cam.cw/2) + 64
            # draw_y = - int(g_obj.cam.ch/2) - 128 - 32 + 8*g_obj.scale
            draw_x = 16
            draw_y = -16 - th
            ele.draw_x = draw_x
            ele.draw_y = draw_y

            px, py = (pos[0] + draw_x + tx * tw, pos[1] + draw_y + ty * th * -1)
            g_obj.swin.blit(i, (px, py))

            if "ability" in ele.name:
                abi = get_selected_ability(ele.name, g_obj.mc.memory)
                if abi != None and abi.cooldown.cooldown != 0:
                    rect = Rect(px, py, tw, th)
                    f = abi.cooldown.cooldown / abi.cooldown.usage_cd
                    sa = radians(360 - 360 * (f))
                    ea = radians(360)
                    radius = int(tw / 2 - 1)
                    pygame.draw.arc(g_obj.swin, blue, rect, sa, ea, radius)

    # draw xp, level

    mc = g_obj.mc
    xp = mc.xp
    xpup = mc.xp_to_lup

    w, h = 50, 20

    b = 10

    bx = g_obj.w - w * 5 - 50 - b * 5
    by = g_obj.h - 50

    x, y = bx, by

    for i in range(xpup):
        r = Rect(x, y, w, h)
        x += w + b
        pygame.draw.rect(g_obj.swin, gray, r)

    x, y = bx, by

    for i in range(xp):
        r = Rect(x, y, w, h)
        x += w + b
        pygame.draw.rect(g_obj.swin, blue, r)

    # draw bullets
    white = 255, 255, 255
    text = "x {0}".format(mc.currency)
    img = g_obj.font.render(text, 0, white)

    bullet = get_tile_img(g_obj, "main_set", f_flat(299))

    bpos = bx - 225, by - 15
    tpos = bx - 175, by - 15
    g_obj.swin.blit(bullet, bpos)
    g_obj.swin.blit(img, tpos)


def change_it_up(tt, ml):
    texts = []
    words = tt.split(" ")
    while len(words) > 0:
        curr = ""
        while len(words) > 0:
            new_word = words[0]
            if len(curr + " " + new_word) + 1 > ml:
                texts.append(" " + curr)
                curr = ""
                break
            else:
                curr += " " + words.pop(0)

        if len(curr) != 0:
            texts.append(curr)

    return texts


def draw_tooltips(self):
    # consider a black background? :-)
    tts = self.tooltips.active_tooltips

    white = 255, 255, 255

    max_len = 35

    y = 0
    for title, tt in tts:
        if "\n" not in tt:
            texts = change_it_up(tt, max_len)
        else:
            texts_ = tt.split("\n")
            texts = []
            for n in texts_:
                if len(n) > max_len:
                    changed = change_it_up(n, max_len)
                else:
                    changed = [n]
                texts += changed
        for text in [title] + [""] + texts:
            img = self.smallfont.render(text, 0, white)
            x = self.w - img.get_width()
            self.swin.blit(img, (x, y))
            y += img.get_height()



def draw_skilltree(self):
    ui = self.ui
    if not ui.get_selected() == "skill tree":
        return

    self.swin.blit(self.renderlogic.prerendered.skilltree, (0, 0))

    text = "SP: {0}".format(self.skilltree_mgr.stat_points)
    white = 255, 255, 255
    img = self.font.render(text, 0, white)

    self.swin.blit(img, (25, self.h - 50 - self.th - 25))


def draw_dungeon_interactables(self):
    dung = self.dungeon
    chests = dung.chests
    shopkeepers = dung.shopkeepers
    spawners = self.lootmgr
    ox, oy = self.cam.get()

    tw, th = self.tw, self.th
    for c in chests:
        cx, cy = c.pos
        rx, ry = cx * tw + ox, cy * th + oy
        cframe = c.frame
        chest_img = get_tile_img(self, "main_set", f_flat(cframe))
        self.swin.blit(chest_img, (rx, ry))

    for k in shopkeepers:
        kx, ky = k.pos
        rx, ry = kx * tw + ox, ky * th + oy
        kframe = k.frame
        keeper_img = get_tile_img(self, "main_set", f_flat(kframe))
        self.swin.blit(keeper_img, (rx, ry))

    for s in spawners.loot_spawners:
        for i in s.get_drawable():
            px, py = i.get_pos()
            f = i.item.widget_frame
            weapon_img = get_tile_img(self, "main_set", f_flat(f))
            rx, ry = px * tw + ox, py * th + oy
            self.swin.blit(weapon_img, (rx, ry))

def draw_dungeon_doors(self):
    dung = self.dungeon
    doors = dung.doors

    for d in doors:
        lout = d.get_layout()
        bx, by = d.pos
        ox, oy = d.get_off()
        roomx, roomy = d.room_pos
        tsw, tsh = d.get_ts_size()
        draw_door(self, lout, bx, by, roomx, roomy, ox, oy, tsw, tsh)





def draw_door(self, lout, bx, by, roomx, roomy, ox, oy, tsw, tsh):
    tw, th = self.tw, self.th

    cam = self.cam
    cx, cy = cam.get()
    # print(cx, cy)

    rw, rh = self.rw, self.rh

    rx = tw * roomx * rw
    ry = th * roomy * rh

    for dx, dy in product(range(tsw), range(tsh)):
        tindx = lout.get_tile_index("Door", dx, dy)
        tile = self.tilesets.get_tile(*tindx)
        img = tile.image

        at = rx + (bx - ox + dx) * tw + cx, ry + (by - oy + dy) * th + cy
        # at = (bx+dx) * tw, (by+dy) * th
        self.swin.blit(img, at)


def draw_dungeon_layer(g_obj, name, wmap=None):
    dung = g_obj.dungeon

    for room in dung.get_rooms():
        gx, gy = room.grid_pos

        tw, th = room.tilesets.tw, room.tilesets.th

        rw, rh = g_obj.rw, g_obj.rh
        raw, rah = rw * tw, rh * th

        rx, ry = gx * raw, gy * rah

        sw, sh = g_obj.w, g_obj.h

        buffer = max((2 * tw, 2 * th))
        screen_rect = Rect(-buffer, -buffer, sw + buffer * 2, sh + buffer * 2)

        ox, oy = g_obj.cam.get()

        room_rect = Rect(rx + ox, ry + oy, raw, rah)
        # print(room_rect.topleft)

        if not (screen_rect.colliderect(room_rect)):
            continue

        layer = room.layout.get_layer(name)

        in_this_room = dung.get_room().room_id == room.room_id

        x, y = ox, oy
        nx, ny = 0, 0

        mw, mh = room.layout.w, room.layout.h

        somesurf_red = g_obj.nwsurf
        somesurf_green = g_obj.wsurf

        for tx, ty, n in product(range(mw), range(mh), room.layout.layers.keys()):
            if n != name:  # draw only specified layer
                continue
            tile_index = room.layout.get_tile_index(n, tx, ty)
            if tile_index == None:  # transparent tile
                continue
            tile = room.tilesets.get_tile(*tile_index)
            x, y = tx * tw + ox + rx, ty * th + oy + ry
            cr = Rect(x, y, tw, th)
            if not screen_rect.colliderect(cr):
                continue
            # g_obj.swin.blit(tile.image, (x, y))
            tx, ty = tx + rw, ty + rh
            if wmap != None:
                if 0 <= tx < len(wmap) and 0 <= ty < len(wmap[0]):
                    walkable = wmap[tx][ty]
                    if walkable:
                        g_obj.swin.blit(somesurf_green, (x, y))
                    else:
                        g_obj.swin.blit(somesurf_red, (x, y))


def lighting_pass_old(g_obj):
    dung = g_obj.dungeon

    for room in dung.get_rooms():
        gx, gy = room.grid_pos

        tw, th = room.tilesets.tw, room.tilesets.th

        rw, rh = g_obj.rw, g_obj.rh
        raw, rah = rw * tw, rh * th

        rx, ry = gx * raw, gy * rah

        sw, sh = g_obj.w, g_obj.h

        buffer = max((2 * tw, 2 * th))
        screen_rect = Rect(-buffer, -buffer, sw + buffer * 2, sh + buffer * 2)

        ox, oy = g_obj.cam.get()

        room_rect = Rect(rx + ox, ry + oy, raw, rah)
        # print(room_rect.topleft)

        if not (screen_rect.colliderect(room_rect)):
            continue

        in_this_room = dung.get_room().room_id == room.room_id

        x, y = ox, oy
        nx, ny = 0, 0

        mw, mh = room.layout.w, room.layout.h

        tindx_x_l = [8, 9, 10, 11, 12, 13, 14, 15]
        tindx_y = 9

        torches = []

        for tx, ty, n in product(range(mw), range(mh), room.layout.layers.keys()):
            add_torch = False
            if n == "Torches":
                tile_index = room.layout.get_tile_index(n, tx, ty)
                if tile_index != None:  # transparent tile
                    tile = room.tilesets.get_tile(*tile_index)
                    tilex, tiley = tile_index[1:]
                    # print(tilex, tiley)
                    if tindx_y == tiley and tilex in tindx_x_l:
                        add_torch = True

            x, y = tx * tw + ox + rx, ty * th + oy + ry
            cr = Rect(x, y, tw, th)
            if not screen_rect.colliderect(cr):
                continue
            if not in_this_room:
                g_obj.swin.blit(g_obj.darktile, (x, y))

            if add_torch:
                torches.append((x, y))

        td = 6

        wtr = td
        htr = td

        tcx, tcy = 2.5, 2.5

        for t in torches:
            for xtr, ytr in product(range(wtr), range(htr)):
                if not in_range((tcx, tcy), (xtr, ytr), int(td / 2)):
                    continue
                dist = get_distance((tcx, tcy), (xtr, ytr))
                xt, yt = t[0] + (xtr - tcx) * tw, t[1] + (ytr - tcy) * th
                intensity = 0
                for i in range(3):
                    if i > dist:
                        break
                    intensity += 1
                tseed = (t[0], t[1])
                tintensity = g_obj.renderlogic.torches.get_torch_intensity(tseed)
                g_obj.lighttile.set_alpha(int((60 - intensity * 20) * tintensity))
                g_obj.swin.blit(g_obj.lighttile, (xt, yt))


def draw_menus(g_obj):
    # pause menu
    rect_width = 800
    rect_height = 600
    pause_rect = Rect(0, 0, rect_width, rect_height)
    pause_rect.center = (g_obj.w / 2, g_obj.h / 2)

    if g_obj.ui.get_selected()=="in game menu":
        # draw background
        pygame.draw.rect(g_obj.swin, pygame.Color(100, 100, 100, 255), pause_rect)
        # draw buttons
        button_height = rect_height / 4
        for b in g_obj.menu.menu_items:
            b_rect = Rect(0, 0, 600, 100)
            b_rect.center = (g_obj.w / 2, g_obj.h / 2 + button_height)
            pygame.draw.rect(g_obj.swin, pygame.Color(40, 40, 40, 255), b_rect)
            b.rect = b_rect
            # text here
            font = g_obj.font
            img = font.render(b.text, 1, pygame.Color(255, 255, 255, 255))
            g_obj.swin.blit(img,
                            (g_obj.w / 2 - img.get_width() / 2, (g_obj.h / 2 + button_height) - img.get_height() / 2))
            button_height -= 150
    pass
