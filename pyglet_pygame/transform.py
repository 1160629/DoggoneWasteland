
from pyglet_pygame.surface import Surface

def scale(other_surf, scale_to):
    image = other_surf.image
    iw, ih = image.width, image.height

    new_surf = Surface(other_surf)

    height, width = scale_to

    scale_x, scale_y = width / iw, height / ih

    new_surf.scale = scale_x, scale_y
    new_surf.update_sprite()

    return new_surf

def rotate(other_surf, rotation):
    image = other_surf.image
    iw, ih = image.width, image.height

    new_surf = Surface(other_surf)

    #height, width = scale_to

    #scale_x, scale_y = width / iw, height / ih

    #new_image.scale = scale_x, scale_y

    new_surf.rotation = rotation
    new_surf.update_sprite()

    return new_surf

def flip(other_surf, xbool, ybool):
    image = other_surf.image
    iw, ih = image.width, image.height

    new_surf = Surface(other_surf)

    if xbool == 1:
        new_surf.scale = new_surf.scale[0] * -1, new_surf.scale[1]
    if ybool == 1:
        new_surf.scale = new_surf.scale[0], new_surf.scale[1] * -1

    new_surf.update_sprite()

    return new_surf