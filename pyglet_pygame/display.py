import pyglet
from pyglet import clock
from pyglet.window import key
from pyglet.gl import *
pyglet.options['debug_gl'] = False
from threading import Thread


glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
# fix filtering
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


global window
window = None
global mm
mm = None


class Window(pyglet.window.Window):
    def __init__(self, width = None, height = None):
        super(Window, self).__init__(width, height, resizable=False, fullscreen=False, caption="")
        self.clear()

        self.dt_count = clock.tick()
        self.fps_display = pyglet.clock.ClockDisplay()

        self.clear_me = False

        self.mpos = 0, 0
        self.mpressed = [0, 0, 0]

    def update(self):
        self.dt_count += clock.tick()

        if self.dt_count >= 0.025:
            self.dt_count = 0

    def draw(self, sprites = None):
        if sprites != None:
            for s in sprites:
                s.draw()

        self.fps_display.draw()

        self.flip()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.close()

    def on_mouse_motion(self, x, y, dx, dy):
        mx, my = x, y
        self.mpos = mx, my

    def on_mouse_press(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            self.mpressed[0] = 1
        elif button == pyglet.window.mouse.MIDDLE:
            self.mpressed[1] = 1
        elif button == pyglet.window.mouse.RIGHT:
            self.mpressed[2] = 1

        mx, my = x, y
        self.mpos = mx, my

    def on_mouse_release(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            self.mpressed[0] = 0
        elif button == pyglet.window.mouse.MIDDLE:
            self.mpressed[1] = 0
        elif button == pyglet.window.mouse.RIGHT:
            self.mpressed[2] = 0

        mx, my = x, y
        self.mpos = mx, my

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.LEFT:
            self.mpressed[0] = 1
        elif buttons & pyglet.window.mouse.MIDDLE:
            self.mpressed[1] = 1
        elif buttons & pyglet.window.mouse.RIGHT:
            self.mpressed[2] = 1

        mx, my = x, y
        self.mpos = mx, my

class WindowManager:
    def __init__(self, width = None, height = None):
        self.window = Window(width = width, height = height)

        self.to_blit = []

    def fill(self, color):
        c = color[0]/255, color[1]/255, color[2]/255, 1
        pyglet.gl.glClearColor(*c)
        self.window.clear()

    def blit(self, other_surf, pos):
        x, y = pos

        ow, oh = other_surf.get_size()

        ypos = self.window.height - y - oh

        scale = other_surf.scale
        if scale[0] < 0:
            x = x + ow
        if scale[1] < 0:
            y = y + oh

        rot = -other_surf.rotation 

        #old_sprite = other_surf.get_sprite()
        new_sprite = pyglet.sprite.Sprite(other_surf.image, x, ypos)
        new_sprite.scale_x = scale[0]
        new_sprite.scale_y = scale[1]
        new_sprite.rotation = rot
        new_sprite.opacity = other_surf.alpha
        
        self.to_blit.insert(0, new_sprite)

    def set_caption(self, caption):
        self.window.set_caption(caption)

    def get_width(self):
        return self.window.width

    def get_height(self):
        return self.window.height


def set_mode(t, flags):
    global window
    global mm
    window = WindowManager(width=t[0], height=t[1])
    mm.window = window
    mm.start()
    return window

def set_caption(caption):
    pass

def update():
    global window
    window.window.update()
    window.window.draw(window.to_blit)
    for s in window.to_blit:
        s.delete()
    window.to_blit = []


# sprites can be freely modified even after being added to a batch!