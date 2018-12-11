
class Controller:
    def __init__(self):
        self.state = "idle"
        self.last_action = "idle"

        self.controller_type = None

        self.unit = None

    def action(self, c_ap, c_hp_self, c_hp_enemy, cds, u_state, c_state, l_action, c_type):
        if c_state == "fleeing":
            pass # check if we have heal/buff available, then go into that state
            # otherwise stay in this state and keep running away.
        
        elif c_state == "idling":
            pass # check if enemy is within range, if so- go out of idle state.

        elif c_state == "approaching":
            pass # if you're too far away from enemy to attack - approach; walk toward
            # otherwise; go into attack state.

        elif c_state == "kiting":
            pass # if you're ranged and your range is greater than the enemies, then
            # move a little back, otherwise go into a state of attacking.

        elif c_state == "attacking":
            pass # here we can use a ranged or melee ability, or ranged or melee basic attack.

    def update(self, mc, mpos, mpress, ui, fighting):
        if self.unit.end_turn == True:
            return
        else:
            c_ap = self.unit.ap.get_ap()
            c_hp_self = self.unit.get_health()
            c_hp_enemy = mc.get_health()
            cds = []
            u_state = self.unit.state
            c_state = self.state
            l_action = self.last_action
            c_type = self.controller_type
            self.action(c_ap, c_hp_self, c_hp_enemy, cds, u_state, c_state, l_action, c_type)


# 4 action types
# use attack - ranged / melee
# use ability (4 ability categories)
# - heal
# - buff
# - ranged
# - melee
# walk
# pass

# state types
# idle
# approaching
# kiting
# attacking
# heal/buff
# fleeing