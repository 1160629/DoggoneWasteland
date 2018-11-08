
# abilities

class Ability:
    def __init__(self):
        pass

class BasicAttack(Ability):
    def __init__(self):
        Ability.__init__(self)

    def calculate_damage(self, weapon):
        pass

    def apply_effects(self, weapon):
        pass

# Sharpshooter
class Kneecapper(Ability):
    def __init__(self):
        Ability.__init__(self)

class TryToLeave(Ability):
    def __init__(self):
        Ability.__init__(self)

class LeadAmmo(Ability):
    def __init__(self):
        Ability.__init__(self)

class Steady(Ability):
    def __init__(self):
        Ability.__init__(self)

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



# All abilities for any unit will be contained within a Memory object

class Memory:
    def __init__(self):
        self.abilities = [None for i in range(6)]
