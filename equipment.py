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

        self.projectile_speed = 10

    def get_damage(self):
        dmg = randint(*self.base_damage)
        dmg *= self.quality_multiplier
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

    return w
    
def get_weapon_range(w):
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

