import pygame
from logic import Rect, in_range, get_distance
from itertools import product


def f_flat(f):
    rtw = 16
    ind = f % rtw, f // rtw
    return ind


def get_tile_img(g_obj, tileset, tilenr):
    tile = g_obj.tilesets.get_tile(tileset, tilenr[0], tilenr[1])
    tile_img = tile.image
    return tile_img


def prerender(g_obj, renderlogic):
    for room in g_obj.dungeon.get_rooms():
        bl = prerender_room(g_obj, room, g_obj.botlayers)
        tl = prerender_room(g_obj, room, g_obj.toplayers)

        renderlogic.prerendered.add_prerendered_room(room, bl, tl)

    torch_imgs = []
    for i in range(61):
        f = i / 60
        torch_imgs.append(prerender_torch(g_obj, f))

    renderlogic.prerendered.torches = torch_imgs

    dark_img = prerender_dark(g_obj)

    renderlogic.prerendered.darkness = dark_img

    skilltree_img = prerender_skilltree(g_obj)

    renderlogic.prerendered.skilltree = skilltree_img


def prerender_skilltree(self):
    s = pygame.Surface((self.w, self.h))
    s.fill((0, 0, 0))
    s.set_colorkey((0, 0, 0))
    r = pygame.Rect(0, 0, int(self.w / 2), self.h)
    # pygame.draw.rect(s, (1, 1, 1), r)

    tw, th = self.tw, self.th
    tset = "main_set"

    str_img = get_tile_img(self, tset, f_flat(187))
    dex_img = get_tile_img(self, tset, f_flat(186))
    int_img = get_tile_img(self, tset, f_flat(188))
    abi_b_img = get_tile_img(self, tset, f_flat(190))
    abi_s_img = get_tile_img(self, tset, f_flat(191))
    abi_e_img = get_tile_img(self, tset, f_flat(189))
    mut_img = get_tile_img(self, tset, f_flat(185))

    nodes = self.mc.skilltree.get_all_nodes()
    maxh = self.mc.skilltree.h * th

    ox = int(tw / 2)
    oy = int(th / 2)

    line_color = 254, 254, 254

    # draw connections
    for n in nodes:
        gx, gy = n.get_gpos()
        pos = gx * tw + ox, maxh - gy * th + oy
        for ton in n.points_to:
            gx, gy = ton.get_gpos()
            to_pos = gx * tw + ox, maxh - gy * th + oy
            spos, epos = pos, to_pos
            pygame.draw.line(s, line_color, spos, epos, 3)

    simg = pygame.Surface((tw, th))
    simg.set_colorkey((0, 0, 0))
    # draw actual nodes
    for n in nodes:
        if n.node_type == "ability":
            if n.node_belongs == "brawler":
                img = abi_b_img
            elif n.node_belongs == "sharpshooter":
                img = abi_s_img
            elif n.node_belongs == "engineer":
                img = abi_e_img
        elif n.node_type == "mutation":
            img = mut_img
        elif n.node_type == "stat":
            if n.node_is == "str":
                img = str_img
            elif n.node_is == "dex":
                img = dex_img
            elif n.node_is == "int":
                img = int_img

        gx, gy = n.get_gpos()
        pos = gx * tw, maxh - gy * th

        simg.fill((0, 0, 0))
        if n.statted:
            # pygame.draw.rect(s, line_color, n.rect)
            if n.node_belongs == "brawler":
                arr = pygame.surfarray.array3d(img)
                arr[::, ::, 1] = 0
                arr[::, ::, 2] = 0
                pxred = pygame.surfarray.make_surface(arr)
                pxred.set_colorkey((0, 0, 0))
                s.blit(pxred, pos)
            elif n.node_belongs == "sharpshooter":
                arr = pygame.surfarray.array3d(img)
                arr[::, ::, 0] = 0
                arr[::, ::, 2] = 0
                pxgreen = pygame.surfarray.make_surface(arr)
                pxgreen.set_colorkey((0, 0, 0))
                s.blit(pxgreen, pos)
            elif n.node_belongs == "engineer":
                arr = pygame.surfarray.array3d(img)
                arr[::, ::, 0] = 0
                arr[::, ::, 1] = 0
                pxblue = pygame.surfarray.make_surface(arr)
                pxblue.set_colorkey((0, 0, 0))
                s.blit(pxblue, pos)
        else:
            s.blit(img, pos)

    return s


def prerender_dark(g_obj):
    rw, rh = g_obj.rw, g_obj.rh
    tw, th = g_obj.tw, g_obj.th

    new_surf = pygame.Surface((rw * tw, rh * th), flags=pygame.HWSURFACE)
    new_surf.fill((0, 0, 0))
    new_surf.set_alpha(180)

    return new_surf


def prerender_torch(g_obj, actual_intensity):
    t = 3, 3
    tw, th = g_obj.tw, g_obj.th

    new_surf = pygame.Surface((t[0] * 2 * tw, t[1] * 2 * th), flags=pygame.HWSURFACE)
    new_surf.fill((0, 0, 0))
    new_surf.set_colorkey((0, 0, 0))

    td = 5

    wtr = td
    htr = td

    tcx, tcy = 2.5, 2.5

    color = 255, 200, 200

    for xtr, ytr in product(range(wtr), range(htr)):
        if not in_range((tcx, tcy), (xtr, ytr), int(td / 2)):
            continue
        dist = get_distance((tcx, tcy), (xtr, ytr))
        xt, yt = t[0] + (xtr) * tw, t[1] + (ytr) * th
        intensity = 0
        for i in range(4):
            if i > dist:
                break
            intensity += 1

        tintensity = (1 - actual_intensity * (intensity / 3)) * 0.7 + 0.3
        # print(tintensity)

        col = list(map(lambda x: x * tintensity, color))

        torch_img = g_obj.lighttile
        torch_img.fill(col)
        torch_img.set_alpha(255)

        new_surf.blit(torch_img, (xt, yt))
        # new_surf.set_alpha(actual_intensity)

    new_surf.set_alpha(80)

    return new_surf


def prerender_room(g_obj, room, layers):
    rw, rh = g_obj.rw, g_obj.rh
    tw, th = g_obj.tw, g_obj.th
    sw, sh = tw * rw, th * rh
    new_surf = pygame.Surface((sw, sh), flags=pygame.HWSURFACE)
    new_surf.set_colorkey((0, 0, 0))
    new_surf.fill((0, 0, 0))
    for name in layers:
        dung = g_obj.dungeon

        gx, gy = room.grid_pos

        tw, th = room.tilesets.tw, room.tilesets.th

        # rw, rh = g_obj.rw, g_obj.rh
        # raw, rah = rw * tw, rh * th

        # rx, ry = gx * raw, gy * rah

        sw, sh = g_obj.w, g_obj.h

        buffer = max((2 * tw, 2 * th))
        screen_rect = Rect(-buffer, -buffer, sw + buffer * 2, sh + buffer * 2)

        ox, oy = 0, 0

        # room_rect = Rect(rx+ox, ry+oy, raw, rah)

        # layer = room.layout.get_layer(name)

        # in_this_room = dung.get_room().room_id == room.room_id

        # x, y = ox, oy
        # nx, ny = 0, 0

        mw, mh = room.layout.w, room.layout.h

        for tx, ty, n in product(range(mw), range(mh), room.layout.layers.keys()):
            if n != name:  # draw only specified layer
                continue
            tile_index = room.layout.get_tile_index(n, tx, ty)
            tile_orient = room.layout.get_tile_orient(n, tx, ty)
            if tile_index == None:  # transparent tile
                continue
            tile = room.tilesets.get_tile(*tile_index)
            x, y = tx * tw + ox, ty * th + oy
            cr = Rect(x, y, tw, th)
            if not screen_rect.colliderect(cr):
                continue
            img = tile.image
            if tile_orient[0] == 1:
                img = pygame.transform.flip(img, 1, 0)
            if tile_orient[1] == 1:
                img = pygame.transform.flip(img, 0, 1)
            if tile_orient[2] == 1:
                # img = pygame.transform.flip(img, 1, 1)
                img = pygame.transform.rotate(img, 270)

            # img = tile.image
            new_surf.blit(img, (x, y))

    return new_surf
