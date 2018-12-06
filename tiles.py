class Tile:
    def __init__(self):
        self.image = None
        self.walkable = None
        self.triggerable = None


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

    def has_layer(self, name):
        if name in self.layers.keys():
            return True
        return False

    def get_layer(self, name):
        return self.layers[name]

    def get_tile_index(self, name, x, y):
        data = self.get_layer(name)["data"][x][y]
        if data == None:
            return None
        return data[:3]

    def get_tile_orient(self, name, x, y):
        data = self.get_layer(name)["data"][x][y]
        if data == None:
            return None
        return data[3:]

    def set_tile_index(self, name, x, y, to):
        self.get_layer(name)["data"][x][y] = to

    def set_tile_index_and_orient(self, name, x, y, to, ori):
        if to == None or ori == None:
            set_to = None
            # print("This should not happen:", name, x, y, to, ori)
        else:
            set_to = to + ori
            # print("ey")
        self.get_layer(name)["data"][x][y] = set_to

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
