class AP:
    def __init__(self):
        self.turn_ap = 0  # the AP remaining per turn

        self.current_ap = 0  # the AP recovered per turn

        self.base_ap = 4  # base AP of any unit
        self.max_ap = 10  # AP cap of all units

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

        self.state = "out of combat"

        self.units_in_combat = []
        self.units_in_room = []
        self.turn = 0

        self.start_of_turn = False

        self.use_list = None

        self.transition = True

        self.new_room = True
        self.old_room = None

    def set_units_in_room(self, g_obj):
        room = g_obj.dungeon.get_room()

        if room == self.old_room:
            self.new_room = False
        else:
            self.new_room = True

        self.old_room = room

        units = g_obj.units

        gx, gy = room.grid_pos

        rw, rh = g_obj.rw, g_obj.rh

        units_in_room = []

        for u in units:
            ux, uy = u.pos
            gux, guy = ux//rw, uy//rh

            if (gux, guy) == (gx, gy):
                units_in_room.append(u)

        self.units_in_room = units_in_room

    def set_living_count(self):
        self.living_count = 0
        for u in self.use_list:
            if not (u.state == "dead"):
                self.living_count += 1


    def init_units(self):
        for nu in self.use_list:
            nu.ap.current_ap = calculate_ap(nu.ap.base_ap, nu.ap.max_ap, nu.stats.intelligence, \
                                            nu.equipment.get_wielded_weapons(), \
                                            nu.equipment.get_worn_gear(), nu.mutations.get())
            nu.ap.new_turn()

    def init_combat(self):
        self.init_units()
        self.turn = 0

        self.set_living_count()

        for u in self.units_in_room:
            u.labels.add_label("Go!", u.pos[0], u.pos[1])

    def get_current_unit(self):
        if self.turn < len(self.use_list):
            return self.use_list[self.turn]
        return None

    def update(self, g_obj):
        #print(self.state, self.turn, self.use_list)
        if self.state == "out of combat":
            self.set_units_in_room(g_obj)
            self.use_list = self.units_in_room
            self.set_living_count()

            if self.new_room == True:
                self.turn = 0
                self.init_units()



            if (len(self.units_in_room) > 1 and g_obj.mc in self.units_in_room) and self.living_count > 1:
                self.state = "start combat"
            
        elif self.state == "start combat":
            self.units_in_combat = self.units_in_room
            self.use_list = self.units_in_combat

            self.init_combat()

            self.state = "in combat"

        elif self.state == "in combat":
            self.set_living_count()
            self.use_list = self.units_in_combat

            if self.living_count == 1:
                self.state = "end combat"

        elif self.state == "end combat":
            self.turn = 0

            self.use_list = self.units_in_room

            self.state = "out of combat"

        cu = self.get_current_unit()

        if cu != None:
            if cu.end_turn == True:
                self.turn += 1
                if self.turn >= len(self.use_list):
                    self.turn = 0

                cu.finish_turn()

                nu = self.get_current_unit()
                nu.end_turn = False
                nu.ap.new_turn()
                self.start_of_turn = True
            else:
                self.start_of_turn = False
