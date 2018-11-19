
class AP:
    def __init__(self):
        self.turn_ap = None # the AP remaining per turn

        self.current_ap = 0 # the AP recovered per turn

        self.base_ap = 5 # base AP of any unit
        self.max_ap = 10 # AP cap of all units

        self.fractional_point = 0

        self.end_turn = False

    def use_point(self):
        # used when attacking, and doing any other action that requires an entire AP
        self.turn_ap -= 1
        if self.turn_ap == 0:
            self.end_turn = True

    def use_fractional_point(self, f):
        # used when moving for instance, when moving a single space only requires a 
        # fraction of an AP
        self.fractional_point += f
        if self.fractional_point >= 1:
            self.fractional_point -= 1
            self.use_point()

    def new_turn(self):
        self.end_turn = False
        self.turn_ap = self.current_ap
        self.fractional_point = 0

    def get_ap(self):
        return self.turn_ap - self.fractional_point


# calculates how many AP a unit is given per turn
def calculate_ap(base_ap, max_ap, intelligence, weapons, gear, mutations):
    ap_int = int(intelligence / 3)

    ap_weapons = 0
    for w in weapons:
        for m in w.mods:
            if not m.name == "ap":
                continue
            ap_weapons += m.value

    ap_mutations = 0
    for m in mutations:
        if not m.mutation_to == "ap":
            continue
        ap_mutations += m.mutation_value

    ap = base_ap + ap_int + ap_weapons + ap_mutations

    capped_ap = min((ap, max_ap))

    return capped_ap


# this class keeps track of turn-taking in combat, and will be extended to contain other potential combat control elements

class CombatController:
    def __init__(self):
        self.state = "start combat"

        self.units_in_combat = []
        self.turn = 0

        self.start_of_turn = False

        self.pcu = None

    def init_combat(self):
        for nu in self.units_in_combat:
            nu.ap.current_ap = calculate_ap(nu.ap.base_ap, nu.ap.max_ap, nu.stats.intelligence, \
            nu.equipment.get_wielded_weapons(), \
            nu.equipment.get_worn_gear(), nu.mutations.get())
            nu.ap.new_turn()

    def get_current_unit(self):
        return self.units_in_combat[self.turn]

    def update(self):
        if self.state == "start combat":
            self.state = "in combat"
            self.init_combat()

        elif self.state == "in combat":
            cu = self.get_current_unit()
            if cu != self.pcu:
                self.start_of_turn = True
            else:
                self.start_of_turn
            self.pcu = cu
            if cu.end_turn == True:
                self.turn += 1
                if self.turn >= len(self.units_in_combat):
                    self.turn = 0
                
                cu.finish_turn()

                nu = self.get_current_unit()
                nu.end_turn = False
                nu.ap.new_turn()


