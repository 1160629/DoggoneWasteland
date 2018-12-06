

# status effects

class StatusEffect:
    def __init__(self):
        self.name = None
        self.stacks = None
        self.finished = False

    def tick(self):
        if self.finished:
            return
        if self.stacks == 0:
            self.finished = True
        self.stacks -= 1

    def is_active(self):
        return True - self.finished

def has_status_effect(target, effect_name):
    for i in target.statuses:
        if i.name == effect_name:
            return True
    
    return False

def get_relevant_status_effect(target, effect_name):
    for i in target.statuses:
        if i.name == effect_name:
            return i
    
    return None

def remove_status_effect(target, effect_name):
    n = 0
    for i in target.statuses:
        if i.name == effect_name:
            break
        n += 1
    else:
        return False

    target.statuses.pop(n)

    return True

def add_status_effect(target, effect):
    target.statuses.append(effect)

class NonStackingEffect(StatusEffect):
    def __init__(self):
        StatusEffect.__init__(self)
        self.is_stacking = False

class StackingEffect(StatusEffect):
    def __init__(self):
        StatusEffect.__init__(self)
        self.is_stacking = True

class Burning(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "burning"

class Bleeding(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "bleeding"

class Knocked(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "knocked"

class Slowed(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "slowed"

class Blinded(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "blinded"

class Steady(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "steady"

class Ready(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "steady"

class Go(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "steady"


class Poisoned(StackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "poisoned"
        self.damage = 5

class Irradiated(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "irradiated"

def gen_effect_mod(effect, stacks):
    class Effect(effect):
        def __init__(self):
            effect.__init__(self)
            self.stacks = stacks
            #self.name = effect().name
    
    return Effect