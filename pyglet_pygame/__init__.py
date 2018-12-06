from pyglet_pygame.surface import Surface
from pyglet_pygame.rect import Rect
from pyglet_pygame.locals import *
import pyglet_pygame.time
import pyglet_pygame.font
import pyglet_pygame.image
import pyglet_pygame.transform
import pyglet_pygame.event
import pyglet_pygame.display
import pyglet_pygame.mouse
import pyglet_pygame.mixer
import pyglet_pygame.draw


from threading import Thread
from time import sleep


class ModuleManager:
    def __init__(self):
        self.window = None

    def start(self):
        t = Thread(target=self.update)
        t.start()

    def update(self):
        while True:
            pyglet_pygame.event.window = pyglet_pygame.display.window
            pyglet_pygame.mouse.window = pyglet_pygame.display.window
            if pyglet_pygame.display.window != None:
                break

global mm
mm = None

def init():
    global mm
    mm = ModuleManager()
    pyglet_pygame.display.mm = mm
    return

def quit():
    global mm
    mm.close()
