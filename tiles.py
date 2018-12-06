class Tile:
    def __init__(self):
        self.image = None
        self.walkable = None


class Tileset:
    def __init__(self):
        self.source = ""

        self.nw, self.nh = None, None
        self.tw, self.th = None, None
        self.tiles = []
        self.walkable = []


class Tilesets:
    def __init__(self):
        self.tw, self.th = None, None
        self.tilesets = {}

    def get_tile(self, tset, x, y):
        return self.tilesets[tset].tiles[x][y]


class Layout:
    def __init__(self):
        self.w, self.h = None, None
        self.layers = None

    def get_layer(self, name):
        return self.layers[name]

    def get_tile_index(self, name, x, y):
        return self.get_layer(name)["data"][x][y]

    def change_layer_status(self, names, to):

        for n in names:
            i = 0
            for l in self.layers:
                if self.layers[i]["name"] == n:
                    self.layers[i]["visible"] = to
                i += 1

    def disable_layers(self, names):
        self.change_layer_status(names, False)

    def enable_layers(self, names):
        self.change_layer_status(names, True)
