from pyglet_pygame.surface import Surface
import pyglet
#from pyglet.image.codecs.png import PNGImageDecoder

def load(image_path):
    image = pyglet.image.load(image_path)
    t = image.width, image.height
    surf = Surface(t)
    surf.image = image
    surf.sprite = pyglet.sprite.Sprite(image)
    return surf

def save(d, image_path):
    pyglet.image.get_buffer_manager().get_color_buffer().save(image_path)