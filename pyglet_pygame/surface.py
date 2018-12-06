import pyglet
from itertools import product
from pyglet.gl import *
import numpy
from pyglet_pygame.rect import Rect


class Surface:
    def __init__(self, t, flags = None):  
        if isinstance(t, tuple):
            w, h = t

            self.rotation = 0
            self.scale = 1.0, 1.0
            self.alpha = 255

            self.image = pyglet.image.Texture.create(w, h)

            self.sprite = pyglet.sprite.Sprite(self.image, 0, 0)


        elif isinstance(t, Surface):
            w, h = t.image.width, t.image.height

            self.rotation = t.rotation
            self.scale = t.scale
            self.alpha = t.alpha

            self.image = pyglet.image.Texture.create(w, h)
            self.blit(t, (0, 0))

            self.sprite = pyglet.sprite.Sprite(self.image, 0, 0)




        #img_data = numpy.zeros((w * h * 4), numpy.uint8)
        #img_data[3::4] = 1
        #img_data[::4] = 1
        #data = img_data
        
        #tex_data = (GLubyte * data.size)( *data )

        #textureIDs = (pyglet.gl.GLuint * 1) ()

        #glGenTextures(1, textureIDs)
        #texture_id = textureIDs[0]
        #glBindTexture(GL_TEXTURE_2D, texture_id)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        #glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, (image_width), (image_height), 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

        #self.image = pyglet.image.Texture(w, h, GL_TEXTURE_2D, texture_id)

        #format_size = 4
        #bytes_per_channel = 1

        #self.image = pyglet.image.ImageData(
        #    dimensions[ 0 ],
        #    dimensions[ 1 ],
        #    "RGBA",
        #    tex_data
        #    )

    #def init_cleaner(self, t, flags = None):
    #    w, h = t
    #    texture_id = glGenTextures(1)
    #    self.image = pyglet.image.Texture(w, h, GL_TEXTURE_2D, texture_id)
    #    self.image.create(w, h)

    def update_sprite(self):
        sprite = self.sprite
        sprite.opacity = self.alpha
        sprite.scale_x = self.scale[0]
        sprite.scale_y = self.scale[1]
        sprite.rotation = self.rotation

    def get_width(self):
        return abs(int(self.image.width * self.scale[0]))

    def get_height(self):
        return abs(int(self.image.height * self.scale[1]))

    def get_size(self):
        return self.get_width(), self.get_height()

    def convert_alpha(self):
        return self

    def set_colorkey(self, c):
        pass

    def get_colorkey(self):
        pass

    def set_alpha(self, a):
        self.alpha = a

    def get_alpha(self):
        return self.alpha

    def fill(self, c):
        return

    def get(self):
        return self.image

    def get_sprite(self):
        return self.sprite

    def blit(self, other_surf, pos):
        x, y = pos
        w, h = other_surf.get_size()

        thisw, thish = self.get_size()

        y = thish - y - h

        if not (0 <= x <= thisw and 0 <= y <= thish and 0 <= x+w <= thisw and 0 <= y+h <= thish):
            return

        if isinstance(other_surf.image, pyglet.image.Texture):
            self.image.blit_into(other_surf.image.get_image_data(), x, y, 0)
        else:
            self.image.blit_into(other_surf.image, x, y, 0)

    def subsurface(self, rect):
        w, h = rect.w, rect.h
        ypos = self.get_height() - rect.y - rect.h
        #ypos = rect.y
        new_surf = Surface((w, h))
        new_surf.image = self.image.get_region(x=rect.x, y=ypos, width=w, height=h)
        new_surf.rotation = self.rotation
        new_surf.scale = self.scale
        new_surf.alpha = self.alpha
        new_surf.sprite = pyglet.sprite.Sprite(new_surf.image, 0, 0)
        new_surf.update_sprite()
        return new_surf