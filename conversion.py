import json


def get_object(i):
    if "properties" not in i:
        return None
    else:
        for p in i["properties"]:
            if p["name"] == "Object":
                return p["value"]
        return None


def get_anim_name(i):
    if "properties" not in i:
        return None
    else:
        for p in i["properties"]:
            if p["name"] == "Animation":
                return p["value"]
        return None


def get_anim_frame(i):
    if "animations" not in i:
        return None
    else:
        for p in i["properties"]:
            if p["name"] == "Animation":
                return p["value"]
        return None


def get_animation_names(k, tiles):
    anim_names = []
    for i in tiles:
        if get_object(i) != k:
            continue
        anim_name = get_anim_name(i)
        anim_names.append(anim_name)

    return anim_names


def get_animation_frames(k, an, tiles):
    for i in tiles:
        if "animation" not in i:
            continue
        if get_object(i) != k:
            continue
        if get_anim_name(i) != an:
            continue
        anim_frames = i["animation"]

    return anim_frames


def format_merge_and_unflatten(names, frames, tileset_name, from_flat):
    is_number = lambda x: x in "0123456789"
    actual_names = {}
    for n in names:
        if " " not in n:
            actual_names[n] = None
            continue
        split = n.split(" ")
        name, number = " ".join(split[:-1]), split[-1]
        l = list(number)
        if all(map(is_number, l)):
            if name in actual_names:
                actual_names[name].append("".join(number))
            else:
                actual_names[name] = ["".join(number)]

    new_names = list(actual_names.keys())

    new_frames = {}

    sandra_indexing_conversion = {
        "1": (0, 0),
        "2": (0, 1),
        "11": (1, 0),
        "22": (1, 1),
        "3": (0, 2),
        "33": (1, 2)
    }

    for name in new_names:
        frames_ = {}
        if actual_names[name] == None:
            k = name
            fset = frames[k]
            n = 0
            for f in fset:
                fn = "frame " + str(n + 1)
                tox, toy = 0, 0
                x, y = from_flat(f["tileid"])
                new_thing = ["main_set", x, y, tox, toy]
                if fn in frames_:
                    frames_[fn]["tiles"].append(new_thing)
                else:
                    new_d = {
                        "dt": f["duration"] / 1000,
                        "tiles": [new_thing]
                    }
                    frames_[fn] = new_d

                n += 1

        else:
            for c in actual_names[name]:

                k = name + " " + c
                fset = frames[k]
                n = 0
                for f in fset:
                    fn = "frame " + str(n + 1)
                    tox, toy = sandra_indexing_conversion[c]
                    x, y = from_flat(f["tileid"])
                    new_thing = ["main_set", x, y, tox, toy]
                    if fn in frames_:
                        frames_[fn]["tiles"].append(new_thing)
                    else:
                        new_d = {
                            "dt": f["duration"] / 1000,
                            "tiles": [new_thing]
                        }
                        frames_[fn] = new_d

                    n += 1

        new_frames[name] = frames_

    return new_frames


def convert_tileset_animations(objs, from_flat, tileset_name):
    animations = {}

    for k, i in objs.items():
        names = i["anim_names"]
        frames = i["anim_frames"]
        actual_frames = format_merge_and_unflatten(names, frames, tileset_name, from_flat)
        animations[k] = actual_frames

    return animations


def convert_animations():
    path_to_tileset = "tilesets/actual/UltimateTileset.json"
    path_to_animations = "json/animations.json"

    with open(path_to_tileset, "r") as f:
        d = json.load(f)

    imw, imh = d["imagewidth"], d["imageheight"]
    tw, th = d["tilewidth"], d["tileheight"]

    tilesx = int(imw / tw)
    tilesy = int(imh / th)

    from_flat = lambda f: (f % tilesx, f // tilesx)
    to_flat = lambda x, y: y * tilesx + x

    objects = {

    }

    tiles = d["tiles"]

    for i in tiles:
        # print(i)
        tid = i["id"]
        obj = get_object(i)
        if obj == None:
            continue
        objects[obj] = {}

    for k, i in objects.items():
        anim_names = get_animation_names(k, tiles)
        i["anim_names"] = anim_names

    for k, i in objects.items():
        if k not in objects:
            continue
        i["anim_frames"] = {}
        for an in i["anim_names"]:
            anim_frames = get_animation_frames(k, an, tiles)
            i["anim_frames"][an] = anim_frames

    tileset_name = "main set"
    animations = convert_tileset_animations(objects, from_flat, tileset_name)

    with open("json/animations.json", "w+") as f:
        json.dump(animations, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    convert_animations()
