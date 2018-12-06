class Stats:
    def __init__(self):
        self.intelligence = 0
        self.dexterity = 0
        self.strength = 0

    def print_stats(self):
        print("str:", self.strength)
        print("dex:", self.dexterity)
        print("int:", self.intelligence)

    def increase_stat(self, name):
        if name == "int":
            self.intelligence += 1
        elif name == "str":
            self.strength += 1
        elif name == "dex":
            self.dexterity += 1

        # self.print_stats()


class Node:
    def __init__(self, node_type, node_is):
        self.came_from = []
        self.points_to = []

        self.statted = False

        self.node_type = node_type
        self.node_is = node_is

        self.node_belongs = None

        self.gridx, self.gridy = None, None

        self.rect = None

        self.statted = False

    def add_dest(self, new_node):
        self.points_to.append(new_node)
        new_node.came_from.append(self)

    def set_gpos(self, *pos):
        if len(pos) == 2:
            self.gridx, self.gridy = pos
        elif len(pos) == 1:
            self.gridx, self.gridy = pos[0]

    def get_gpos(self):
        return self.gridx, self.gridy


class SkillTree:
    def __init__(self):
        self.brawler_start = None
        self.sharpshooter_start = None
        self.engineer_start = None

        self.all_nodes = []

        self.h = 13
        self.w = 15

    def get_all_nodes(self):
        return self.all_nodes

    def get_first_layer(self):
        return self.brawler_start, self.sharpshooter_start, self.engineer_start

    def stat_node(self, stat_node):
        for n in self.all_nodes:
            if n == stat_node and n.statted == False:
                prereq = list(map(lambda x: x.statted, n.came_from))
                ahead = list(map(lambda x: x.statted, n.points_to))
                nearby = prereq + ahead
                in_first_layer = stat_node in self.get_first_layer()
                if any(nearby) or in_first_layer:
                    # print(n.node_type, n.node_is)
                    n.statted = True
                    break
        else:
            return False

        return True


def get_class_layer_n(y_pos, layers, the_class):
    l = layers[y_pos]
    count = 0
    for i in l:
        if i in the_class:
            count += 1

    return count


def assign_skill_grid_positions(abin, mutn, strn, dexn, intn):
    l1 = [
        strn["0"], dexn["0"], intn["0"]
    ]

    l2 = [
        abin["bash"], abin["go"], abin["steady"], abin["try to leave"], abin["molotov"], abin["ready"]
    ]

    l3 = [
        strn["2"], strn["1"], abin["throw sand"], dexn["1"], abin["kneecapper"], abin["lead ammo"], \
        abin["flash bang"], intn["1"], abin["vaccine"]
    ]

    l4 = [
        abin["fart"]
    ]

    l5 = [
        strn["3"], mutn["anemic"], mutn["toxic"], dexn["2"], mutn["maniac"], mutn["shifty"], intn["2"]
    ]

    l6 = [
        mutn["nuclear"], mutn["snake skin"], dexn["3"], dexn["4"], mutn["nudist"], mutn["having a blast"]
    ]

    l7 = [
        strn["4"], intn["3"]
    ]

    l8 = [
        abin["dinner time"], abin["dash"], abin["first aid kit"], abin["tornado"], abin["land mine"],
        abin["rocket ride"]
    ]

    l9 = [
        strn["5"], dexn["5"], intn["4"]
    ]

    l10 = [
        abin["finisher"], abin["falcon punch"], abin["rip 'em a new one"], abin["dance off"], \
        abin["gotta hand it to 'em"], abin["holy hand grenade"]
    ]

    l11 = [
        strn["6"], strn["7"], dexn["6"], dexn["7"], intn["5"], intn["6"]
    ]

    l12 = [
        intn["7"]
    ]

    l13 = [
        mutn["third arm"], mutn["green"], mutn["addict"], mutn["third eye"], mutn["third time's the charm"],
        mutn["brainiac"]
    ]

    brawler = [
        strn["0"], strn["1"], strn["2"], strn["3"], strn["4"], strn["5"], strn["6"], strn["7"],
        abin["bash"], abin["go"], abin["throw sand"], abin["fart"],
        abin["dinner time"], abin["dash"],
        abin["finisher"], abin["falcon punch"],
        mutn["anemic"], mutn["nuclear"], mutn["snake skin"], mutn["third arm"], mutn["green"]
    ]

    sharpshooter = [
        dexn["0"], dexn["1"], dexn["2"], dexn["3"], dexn["4"], dexn["5"], dexn["6"], dexn["7"],
        abin["try to leave"], abin["steady"], abin["kneecapper"], abin["lead ammo"],
        abin["first aid kit"], abin["tornado"],
        abin["rip 'em a new one"], abin["dance off"],
        mutn["toxic"], mutn["maniac"], mutn["third eye"], mutn["addict"]
    ]

    engineer = [
        intn["0"], intn["1"], intn["2"], intn["3"], intn["4"], intn["5"], intn["6"], intn["7"],
        abin["molotov"], abin["ready"], abin["flash bang"], abin["vaccine"],
        abin["land mine"], abin["rocket ride"],
        abin["gotta hand it to 'em"], abin["holy hand grenade"],
        mutn["shifty"], mutn["nudist"], mutn["having a blast"], mutn["third time's the charm"], mutn["brainiac"]
    ]

    layers = l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13

    brawler_layers = [[] for i in layers]
    sharpshooter_layers = [[] for i in layers]
    engineer_layers = [[] for i in layers]

    strn["0"].set_gpos(2, 0)
    dexn["0"].set_gpos(7, 0)
    intn["0"].set_gpos(12, 0)
    strn["0"].node_belongs = "brawler"
    dexn["0"].node_belongs = "sharpshooter"
    intn["0"].node_belongs = "engineer"

    assigned = []
    unassigned = [strn["0"], dexn["0"], intn["0"]]

    while len(unassigned) > 0:
        n = unassigned.pop(0)

        for on in n.points_to:
            if on in assigned:
                continue
            unassigned.append(on)

        if n.get_gpos() != (None, None):
            assigned.append(n)
            continue

        indx = 0
        for l in layers:
            if n in l:
                break
            indx += 1
        else:
            raise Exception("All nodes should have an assigned layer.")

        y_pos = indx

        if n in brawler:
            which_class = 0
            base_x = 2
        elif n in sharpshooter:
            which_class = 1
            base_x = 7
        elif n in engineer:
            which_class = 2
            base_x = 12
        else:
            raise Exception("All nodes should have an assigned class.")

        classes = [
            brawler,
            sharpshooter,
            engineer
        ]
        classes_layers = [
            brawler_layers,
            sharpshooter_layers,
            engineer_layers
        ]
        the_class = classes[which_class]
        class_layers = classes_layers[which_class]

        class_names = [
            "brawler",
            "sharpshooter",
            "engineer"
        ]

        n.node_belongs = class_names[which_class]

        class_layer_n = get_class_layer_n(y_pos, layers, the_class)
        class_layer_assigned = len(class_layers[y_pos])

        if class_layer_n == 1:
            if y_pos == 3 and n.node_belongs == "brawler":
                off_x = 2
            else:
                off_x = 0
        elif class_layer_n == 2:
            if n.node_belongs == "engineer":
                if y_pos == 1:
                    if class_layer_assigned == 0:
                        off_x = -1
                    elif class_layer_assigned == 1:
                        off_x = 1
                else:
                    if class_layer_assigned == 0:
                        off_x = 1
                    elif class_layer_assigned == 1:
                        off_x = -1
            else:
                if class_layer_assigned == 0:
                    off_x = -1
                elif class_layer_assigned == 1:
                    off_x = 1
        elif class_layer_n == 3:
            if y_pos == 2:
                if class_layer_assigned == 0:
                    off_x = 0
                elif class_layer_assigned == 1:
                    off_x = -2
                elif class_layer_assigned == 2:
                    off_x = 2
            else:
                if class_layer_assigned == 0:
                    off_x = -2
                elif class_layer_assigned == 1:
                    off_x = 0
                elif class_layer_assigned == 2:
                    off_x = 2

        x_pos = base_x + off_x

        n.set_gpos(x_pos, y_pos)

        assigned.append(n)
        class_layers[y_pos].append(n)


def build_skill_tree():
    abilities = [
        "bash",
        "go",
        "throw sand",
        "fart",
        "dash",
        "dinner time",
        "falcon punch",
        "finisher",
        "try to leave",
        "kneecapper",
        "steady",
        "lead ammo",
        "first aid kit",
        "tornado",
        "rip 'em a new one",
        "dance off",
        "flash bang",
        "molotov",
        "ready",
        "vaccine",
        "rocket ride",
        "land mine",
        "gotta hand it to 'em",
        "holy hand grenade"
    ]

    mutations = [
        "anemic",
        "toxic",
        "maniac",
        "shifty",
        "nudist",
        "having a blast",
        "nuclear",
        "snake skin",
        "third arm",
        "green",
        "third eye",
        "addict",
        "third time's the charm",
        "brainiac"
    ]

    abin = {i: Node("ability", i) for i in abilities}
    mutn = {i: Node("mutation", i) for i in mutations}
    strn = {str(i): Node("stat", "str") for i in range(8)}
    dexn = {str(i): Node("stat", "dex") for i in range(8)}
    intn = {str(i): Node("stat", "int") for i in range(8)}

    # okay. let's do the brawlers tree!

    brawler_start = strn["0"]

    strn["0"].add_dest(abin["bash"])
    strn["0"].add_dest(abin["go"])
    strn["0"].add_dest(strn["1"])

    abin["bash"].add_dest(strn["2"])
    abin["go"].add_dest(abin["throw sand"])
    abin["throw sand"].add_dest(abin["fart"])

    strn["1"].add_dest(strn["3"])
    strn["1"].add_dest(mutn["anemic"])
    mutn["anemic"].add_dest(mutn["toxic"])

    strn["3"].add_dest(mutn["nuclear"])
    strn["3"].add_dest(mutn["snake skin"])

    mutn["nuclear"].add_dest(strn["4"])
    mutn["snake skin"].add_dest(strn["4"])

    strn["4"].add_dest(abin["dash"])
    strn["4"].add_dest(abin["dinner time"])

    abin["dinner time"].add_dest(strn["5"])
    abin["dash"].add_dest(strn["5"])

    strn["5"].add_dest(abin["falcon punch"])
    strn["5"].add_dest(abin["finisher"])

    abin["finisher"].add_dest(strn["6"])
    abin["falcon punch"].add_dest(strn["7"])

    strn["6"].add_dest(mutn["third arm"])
    strn["7"].add_dest(mutn["green"])

    # okay. let's do the sharpshooters tree!

    sharpshooter_start = dexn["0"]

    dexn["0"].add_dest(abin["try to leave"])
    dexn["0"].add_dest(abin["steady"])
    dexn["0"].add_dest(dexn["1"])

    abin["try to leave"].add_dest(abin["kneecapper"])
    abin["steady"].add_dest(abin["lead ammo"])

    dexn["1"].add_dest(mutn["toxic"])
    mutn["toxic"].add_dest(mutn["anemic"])

    dexn["1"].add_dest(dexn["2"])
    abin["kneecapper"].add_dest(dexn["2"])
    abin["lead ammo"].add_dest(mutn["maniac"])
    mutn["maniac"].add_dest(mutn["shifty"])
    mutn["maniac"].add_dest(dexn["2"])

    dexn["2"].add_dest(dexn["3"])
    dexn["2"].add_dest(dexn["4"])
    dexn["3"].add_dest(abin["first aid kit"])
    dexn["4"].add_dest(abin["tornado"])

    abin["first aid kit"].add_dest(dexn["5"])
    abin["tornado"].add_dest(dexn["5"])

    dexn["5"].add_dest(abin["rip 'em a new one"])
    dexn["5"].add_dest(abin["dance off"])

    abin["rip 'em a new one"].add_dest(dexn["6"])
    abin["dance off"].add_dest(dexn["7"])

    dexn["7"].add_dest(mutn["addict"])
    dexn["6"].add_dest(mutn["third eye"])

    # okay. let's do the engineers tree!

    engineer_start = intn["0"]

    intn["0"].add_dest(abin["molotov"])
    intn["0"].add_dest(abin["ready"])
    intn["0"].add_dest(intn["1"])

    abin["molotov"].add_dest(abin["flash bang"])
    abin["ready"].add_dest(abin["vaccine"])

    intn["1"].add_dest(intn["2"])
    intn["1"].add_dest(mutn["shifty"])
    mutn["shifty"].add_dest(mutn["maniac"])

    abin["vaccine"].add_dest(intn["2"])

    intn["2"].add_dest(mutn["nudist"])
    intn["2"].add_dest(mutn["having a blast"])

    mutn["nudist"].add_dest(intn["3"])
    mutn["having a blast"].add_dest(intn["3"])

    intn["3"].add_dest(abin["land mine"])
    intn["3"].add_dest(abin["rocket ride"])

    abin["land mine"].add_dest(intn["4"])
    abin["rocket ride"].add_dest(intn["4"])

    intn["4"].add_dest(abin["gotta hand it to 'em"])
    intn["4"].add_dest(abin["holy hand grenade"])

    abin["holy hand grenade"].add_dest(intn["5"])
    abin["gotta hand it to 'em"].add_dest(intn["6"])

    intn["5"].add_dest(intn["7"])

    intn["7"].add_dest(mutn["brainiac"])
    intn["6"].add_dest(mutn["third time's the charm"])

    assign_skill_grid_positions(abin, mutn, strn, dexn, intn)

    tree = SkillTree()
    tree.brawler_start = brawler_start
    tree.sharpshooter_start = sharpshooter_start
    tree.engineer_start = engineer_start

    abinl = list(abin.values())
    mutnl = list(mutn.values())
    strnl = list(strn.values())
    dexnl = list(dexn.values())
    intnl = list(intn.values())
    all_nodes = abinl + mutnl + strnl + dexnl + intnl

    tree.all_nodes = all_nodes

    return tree
