

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

    def apply(self, target):
        # so in here i first to a check to see if the status effect is currently applied
        # in the case of a "non stacking effect" you only want to apply it if the new
        # effect has more stacks than the currently applied one
        # hence i return if that is not the case
        if has_status_effect(target, self.name) and \
        get_relevant_status_effect(target, self.name).stacks >= self.stacks:
            return

        # otherwise i apply it
        remove_status_effect(target, self.name)
        add_status_effect(target, self)

class Burning(NonStackingEffect):
    def __init__(self):
        NonStackingEffect.__init__(self)
        self.name = "burning"

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

def gen_effect_mod(effect, stacks):
    class Effect(effect):
        def __init__(self):
            effect.__init__(self)
            self.stacks = stacks
            #self.name = effect().name
    
    return Effect