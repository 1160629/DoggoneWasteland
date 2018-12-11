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

        self.ability_type = None  # attack - melee, attack - ranged, buff - self, debuff - other

        self.applies = None

        self.any_sound = False

    def use(self):
        self.cooldown.use()

    def get_cooldown(self):
        return self.cooldown.cooldown


# All abilities for any unit will be contained within a Memory object

class Memory:
    def __init__(self):
        self.abilities = []

        self.max_abi = 5

        self.implemented_abilities = [
            # sharpshooter
            Steady,
            Kneecapper,
            LeadAmmo,
            # TryToLeave,
            FirstAidKit,
            DanceOff,
            # engineer
            Ready,
            FlashBang,
            Molotov,
            Vaccine,
            RocketRide,
            HolyHandGrenade,
            # GottaHandItToEm,
            # brawler
            Go,
            Fart,
            Bash,
            ThrowSand,
            Dash,
            DinnerTime,
            FalconPunch,
            Finisher
        ]

        self.ability_mapping = {}
        for c in self.implemented_abilities:
            o = c()
            self.ability_mapping[o.name.lower()] = c

    def get_next_slot(self):
        if len(self.abilities) == 0: 
            return "ability 1"
        n = 1
        for i in range(self.max_abi):
            txt = "ability " + str(n)
            if not self.is_filled(txt):
                return txt
            n += 1 

    def attach_latest_to_slot(self, slot):
        self.abilities[-1].connected_ui_slot = slot

    def is_full(self):
        if len(self.abilities) >= self.max_abi:
            return True
        return False

    def is_filled(self, n):
        for i in self.abilities:
            if i.connected_ui_slot == n:
                return True
        return False

    def get_learned(self, n):
        for i in self.abilities:
            if i.connected_ui_slot == n:
                return i
        return None

    def unlearn(self, abi):
        new_abilities = []
        for a in self.abilities:
            if a == abi:
                continue
            new_abilities.append(a)
        
        self.abilities = new_abilities

    def learn(self, abi, by_name=False):
        if by_name:
            lo = abi.lower()
            if lo not in self.ability_mapping:
                return False
            abi = self.ability_mapping[lo]()
        self.abilities.append(abi)
        return True

    def learn_all(self, abi_list, by_name=False):
        for abi in abi_list:
            self.learn(abi, by_name=by_name)

    def get_abilities(self):
        return self.abilities

    def lower_cds(self):
        for a in self.abilities:
            a.cooldown.lower_one()


class BasicAttack(Ability):  # unused?
    def __init__(self):
        Ability.__init__(self)

    def calculate_damage(self, weapon):
        pass

    def apply_effects(self, weapon):
        pass


# implemented:

# special:

class TeleportAnywhere(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "God"

        self.name = "Teleport Anywhere"
        self.cooldown = Cooldown(0)
        self.ap_cost = 0
        self.ability_type = "reloc - instant"

        self.any_sounds = False

class DestroyAnything(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "God"

        self.name = "Destroy Anything"
        self.cooldown = Cooldown(0)
        self.ap_cost = 0
        self.ability_type = "attack - ranged"

        self.any_sounds = False

# sharpshooter

class Steady(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Sharpshooter"

        self.name = "Steady"
        self.cooldown = Cooldown(5)
        self.ap_cost = 1
        self.ability_type = "buff - self"
        self.applies = effects.gen_effect_mod(effects.Steady, 3)

        self.any_sounds = True
        self.sound_names = ["buff"]


class FirstAidKit(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Sharpshooter"

        self.name = "First Aid Kit"
        self.cooldown = Cooldown(3)
        self.ap_cost = 2
        self.ability_type = "heal - self"

        self.heal_type = "percentage"
        self.heal_by = 0.25

        self.any_sounds = True
        self.sound_names = ["heal"]


class Kneecapper(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Sharpshooter"

        self.name = "Kneecapper"
        self.cooldown = Cooldown(4)
        self.ap_cost = 2
        self.ability_type = "attack - ranged - debuff"
        self.applies = effects.gen_effect_mod(effects.Slowed, 3)

        self.any_sounds = True
        self.sound_names = ["slow"]


class LeadAmmo(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Sharpshooter"

        self.name = "Lead Ammo"
        self.cooldown = Cooldown(3)
        self.ap_cost = 2
        self.ability_type = "attack - ranged - debuff"
        self.applies = effects.gen_effect_mod(effects.Knocked, 1)

        self.any_sounds = True
        self.sound_names = ["knock"]


class DanceOff(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Sharpshooter"

        self.name = "Dance Off"
        self.cooldown = Cooldown(5)
        self.ap_cost = 3
        self.ability_type = "debuff - others"
        self.applies = effects.gen_effect_mod(effects.Blinded, 2)

        self.any_sounds = True
        self.sound_names = ["blind"]


class TryToLeave(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Sharpshooter"

        self.name = "Try To Leave"
        self.cooldown = Cooldown(4)
        self.ap_cost = 3
        self.ability_type = "reloc - instant"

        self.any_sounds = False


# engineer

class Ready(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Engineer"

        self.name = "Ready"
        self.cooldown = Cooldown(5)
        self.ap_cost = 1
        self.ability_type = "buff - self"
        self.applies = effects.gen_effect_mod(effects.Ready, 3)

        self.any_sounds = True
        self.sound_names = ["buff"]


class FlashBang(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Engineer"

        self.name = "Flash Bang"
        self.cooldown = Cooldown(4)
        self.ap_cost = 3
        self.ability_type = "debuff - others - double"
        self.applies = effects.gen_effect_mod(effects.Slowed, 2)
        self.also_applies = effects.gen_effect_mod(effects.Blinded, 2)

        self.ability_range = 10
        self.blast_radius = 4

        self.any_sounds = True
        self.sound_names = ["slow", "blind"]


class Molotov(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Engineer"

        self.name = "Molotov"
        self.cooldown = Cooldown(2)
        self.ap_cost = 2
        self.ability_type = "attack - ranged - debuff"
        self.applies = effects.gen_effect_mod(effects.Burning, 4)

        self.ability_range = 10
        self.blast_radius = 5

        self.any_sounds = True
        self.sound_names = ["burning"]


class Vaccine(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Engineer"

        self.name = "Vaccine"
        self.cooldown = Cooldown(5)
        self.ap_cost = 2
        self.ability_type = "clear - self"

        self.ability_range = 10
        self.blast_radius = 5

        self.any_sounds = True
        self.sound_names = ["heal"]


class RocketRide(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Engineer"

        self.name = "Rocket Ride"
        self.cooldown = Cooldown(4)
        self.ap_cost = 3
        self.ability_type = "reloc"

        self.ability_range = 10
        self.blast_radius = 4

        self.applies = effects.gen_effect_mod(effects.Knocked, 1)

        self.any_sounds = True
        self.sound_names = ["knock"]


class HolyHandGrenade(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Engineer"

        self.name = "Holy Hand Grenade"
        self.cooldown = Cooldown(5)
        self.ap_cost = 4
        self.ability_type = "attack - ranged - debuff"
        self.applies = effects.gen_effect_mod(effects.Knocked, 1)

        self.ability_range = 8
        self.blast_radius = 5

        self.any_sounds = True
        self.sound_names = ["knock"]


class GottaHandItToEm(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Engineer"

        self.name = "GottaHandItToEm"
        self.cooldown = Cooldown(2)
        self.ap_cost = 2
        self.ability_type = "attack - ranged - debuff"
        self.applies = effects.gen_effect_mod(effects.Burning, 4)

        self.ability_range = 10
        self.blast_radius = 5

        self.any_sounds = True
        self.sound_names = ["burning"]


# brawler

class Go(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Brawler"

        self.name = "Go"
        self.cooldown = Cooldown(5)
        self.ap_cost = 1
        self.ability_type = "buff - self"
        self.applies = effects.gen_effect_mod(effects.Go, 3)

        self.any_sounds = True
        self.sound_names = ["buff"]


class Bash(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Brawler"

        self.name = "Bash"
        self.cooldown = Cooldown(2)
        self.ap_cost = 2
        self.ability_type = "attack - melee - debuff"
        self.applies = effects.gen_effect_mod(effects.Knocked, 2)

        self.any_sounds = True
        self.sound_names = ["knock"]


class Fart(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Brawler"

        self.name = "Fart"
        self.cooldown = Cooldown(2)
        self.ap_cost = 1
        self.ability_type = "debuff - other - double"
        self.applies = effects.gen_effect_mod(effects.Irradiated, 2)
        self.also_applies = effects.gen_effect_mod(effects.Poisoned, 3)

        self.ability_range = 4

        self.any_sounds = True
        self.sound_names = ["poison"]


class ThrowSand(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Brawler"

        self.name = "Throw Sand"
        self.cooldown = Cooldown(2)
        self.ap_cost = 2
        self.ability_type = "debuff - other"
        self.applies = effects.gen_effect_mod(effects.Blinded, 3)

        self.ability_range = 3

        self.any_sounds = True
        self.sound_names = ["blind"]


class DinnerTime(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Brawler"

        self.name = "Dinner Time"
        self.cooldown = Cooldown(3)
        self.ap_cost = 3
        self.ability_type = "attack - melee"

        self.any_sounds = False


class Dash(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Brawler"

        self.name = "Dash"
        self.cooldown = Cooldown(3)
        self.ap_cost = 3
        self.ability_type = "reloc"

        self.ability_range = 7

        self.any_sounds = False


class FalconPunch(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Brawler"

        self.name = "Falcon Punch"
        self.cooldown = Cooldown(5)
        self.ap_cost = 5
        self.ability_type = "attack - melee - aoe"

        self.ability_range = 4

        self.any_sounds = False


class Finisher(Ability):
    def __init__(self):
        Ability.__init__(self)
        self.abi_class = "Brawler"

        self.name = "Finisher"
        self.cooldown = Cooldown(4)
        self.ap_cost = 5
        self.ability_type = "attack - melee"

        self.any_sounds = False
