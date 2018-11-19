import effects
# abilities

class Cooldown:
    def __init__(self, cd):
        self.usage_cd = cd
        self.cooldown = 0

    def use(self):
        self.cooldown = self.usage_cd

    def lower_one(self):
        if self.cooldown != 0:
            self.cooldown -= 1

class Ability:
    def __init__(self):
        self.name = None
        self.connected_ui_slot = None
        self.cooldown = Cooldown(0)
        self.ap_cost = None

        self.ability_type = None # attack - melee, attack - ranged, buff - self, debuff - other

        self.applies = None

    def use(self):
        self.cooldown.use()

    def get_cooldown(self):
        return self.cooldown.cooldown

class BasicAttack(Ability):
    def __init__(self):
        Ability.__init__(self)

    def calculate_damage(self, weapon):
        pass

    def apply_effects(self, weapon):
        pass

# Sharpshooter

class Tornado(Ability):
    def __init__(self):
        Ability.__init__(self)

class FirstAidKit(Ability):
    def __init__(self):
        Ability.__init__(self)

class RipEmANewOne(Ability):
    def __init__(self):
        Ability.__init__(self)

class DanceOff(Ability):
    def __init__(self):
        Ability.__init__(self)

class Kneecapper(Ability):
    def __init__(self):
        Ability.__init__(self)

class TryToLeave(Ability):
    def __init__(self):
        Ability.__init__(self)

class LeadAmmo(Ability):
    def __init__(self):
        Ability.__init__(self)

# implement ^ - next on the menu: Kneecapper
# maybe after this, implement dungeon gen, including remapping of room tiles
# since some abilities (at least Try To Escape) need information like this
# or at least add information about where doors are!

# implemented:

class Steady(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.name = "Steady"
        self.connected_ui_slot = None
        self.cooldown = Cooldown(5)
        self.ap_cost = 1
        self.ability_type = "buff - self"
        self.applies = effects.gen_effect_mod(effects.Steady, 3)

# All abilities for any unit will be contained within a Memory object

class Memory:
    def __init__(self):
        self.abilities = []

        self.max_abi = 5

    def learn(self, abi):
        self.abilities.append(abi)

    def get_abilities(self):
        return self.abilities

    def lower_cds(self):
        for a in self.abilities:
            a.cooldown.lower_one()