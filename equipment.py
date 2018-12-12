from random import randint


# weapons

class Weapon:
    def __init__(self):
        self.name = ""
        self.weapon_type = ""
        self.weapon_class = ""
        self.handedness = ""

        self.attack_type = ""
        self.projectile_type = ""
        self.projectile_speed = 0

        self.base_damage = 0, 0
        self.range = 0
        self.crit = 0

        self.quality = None
        self.quality_multiplier = None
        self.mods = []

        self.rarity = None

        self.projectile_speed = 10

        self.last_attack_crit = False  # for if we ever want to show whether an attack was a critical hit or not

    def get_damage(self, stats, statuses, must_crit=0):
        dex_based_damage_bonus = dex_based_crit_bonus = 0
        int_based_damage_bonus = int_based_crit_bonus = 0
        str_based_damage_bonus = 0
        if self.weapon_class == "Sharpshooter":
            dex_based_damage_bonus = stats.dexterity
            dex_based_crit_bonus = stats.dexterity * 0.02
        elif self.weapon_class == "Brawler":
            str_based_damage_bonus = stats.strength * 1.5
        elif self.weapon_class == "Engineer":
            int_based_damage_bonus = stats.intelligence
            int_based_crit_bonus = stats.intelligence * 0.01

        steady_bonus = 1
        for s in statuses:
            if s.name == "Steady" and s.is_active():
                steady_bonus = 2

        actual_crit = (self.crit + dex_based_crit_bonus + int_based_crit_bonus) * steady_bonus

        dmg = randint(*self.base_damage) + dex_based_damage_bonus + int_based_damage_bonus + str_based_damage_bonus
        dmg *= self.quality_multiplier
        if (randint(0, 100) <= actual_crit * 100) or must_crit:
            dmg *= 2
            self.last_attack_crit = True
        else:
            self.last_attack_crit = False
        return dmg


def get_new_weapon_instance(weapon_type, weapons):
    w = Weapon()

    weapon = weapons[weapon_type]
    w.weapon_type = weapon_type
    w.attack_type = weapon["attack_type"]
    if "projectile_type" in weapon:
        w.projectile_type = weapon["projectile_type"]
    if "projectile_speed" in weapon:
        w.projectile_speed = weapon["projectile_speed"]
    w.base_damage = weapon["base_damage"]
    w.range = weapon["range"]
    w.crit = weapon["crit"]

    w.handedness = weapon["handedness"]
    w.weapon_class = weapon["weapon_class"]

    if "blast_radius" in weapon:
        w.blast_radius = weapon["blast_radius"]

    if "widget_frame" in weapon:
        w.widget_frame = weapon["widget_frame"]

    return w


def get_weapon_range(w):
    if w == None:
        return 0
    weapon = w
    base_range = weapon.range

    mod_range = 0
    for m in weapon.mods:
        if m.name == "range":
            mod_range += m.value

    return base_range + mod_range


# Gear

# Syringes

# All equipment for any unit will be contained within an Equipment object

class Equipment:
    def __init__(self):
        self.hand_one = None
        self.hand_two = None
        self.hand_three = None

        self.hand_one_cd = False
        self.hand_two_cd = False
        self.hand_three_cd = False

        self.head = None
        self.torso = None
        self.legs = None

        self.syringes = [None for i in range(5)]

    def get_wielded_weapons(self):
        # returns currently equipped weapons
        return [i for i in [self.hand_one, self.hand_two, self.hand_three] if i != None]

    def get_worn_gear(self):
        # returns currently equipped gear
        return [i for i in [self.head, self.torso, self.legs] if i != None]
