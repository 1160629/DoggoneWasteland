
from equipment import Equipment, get_weapon_range
from abilities import Memory
from stats import Stats
from mutations import Mutations
from combat import AP
from control import ActionTimer, Animation
from logic import get_distance, in_range, one_tile_range, corrigated_path

import math

# Unit class 

class Unit:
    def __init__(self, pos = None):
        #self.in_room = 0

        self.pos = 0, 0
        if pos != None:
            self.pos = pos[0], pos[1]

        self.animations = {}
        self.anim_pos = self.pos
        self.anim_state = "standing"

        # variables related to movement - make a class to containerize movement stuff?
        self.next_pos = 0, 0
        self.path = None
        self.has_moved = 0
        self.use_points = []
        self.direction = 1
        self.destination = None
        self.get_path = False
        self.first_move = False

        # variables related to attacking - make projectile class (and attack class?)
        self.projectile_pos = 0, 0
        self.attacking = None
        self.attack_weapon = None
        self.projectile_angle = 0

        # control timers
        self.timers = {}
        self.timers["move_timer"] = ActionTimer("move_timer", 0.15)
        self.timers["attack_timer"] = ActionTimer("move_timer", 0.75)

        # size of unit
        self.area = 1

        # gear, stats, etc.
        self.equipment = Equipment()
        self.memory = Memory()
        self.mutations = Mutations()
        self.stats = Stats()
        self.ap = AP()

        self.health = 35
        self.max_health = 35

        self.statuses = []

        # basic state of the unit
        # used in general unit logic
        # current states include
        # idle, moving, attacking, dying, dead
        self.state = "idle"

        # set this to true, to end the units turn
        self.end_turn = False

        # initialise stuff
        self.init_attributes()

        self.init_health_and_base_ap()
        self.init_abilities()
        self.init_stats()
        self.init_equipment()

        self.init_anything_else()

    def init_attributes(self):
        pass

    def init_health_and_base_ap(self):
        pass

    def init_abilities(self):
        pass

    def init_stats(self):
        self.stats.strength = 0

    def init_equipment(self):
        pass

    def init_anything_else(self):
        pass


    def set_pos(self, pos):
        self.pos = pos
        self.anim_pos = pos
        self.next_pos = pos

    def finish_turn(self):
        if self.state == "dead" or self.state == "dying":
            return
        self.path = None
        self.state = "idle"

    def get_move_speed(self):
        self.stats.base_move_speed, self.stats.strength, self.statuses, self.mutations
        return self.stats.base_move_speed + self.stats.strength//2


    def get_damage(self):
        return self.attack_weapon.get_damage()

    def damage(self, damagee):
        damagee.health -= self.get_damage()
        if damagee.health <= 0:
            damagee.state = "dying"


    def launch_bomb(self, at_mouse):
        self.state = "attacking"
        self.attacking = at_mouse["units"][self.attack_weapon.blast_radius-2]
        projectile_speed_per_unit = self.attack_weapon.projectile_speed
        self.attack_to = at_mouse["mapped"]
        
        projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
        self.timers["attack_timer"].dt = projectile_distance
        self.timers["attack_timer"].reset()
        self.ap.use_point()
        self.ap.use_point()

    def fire_shot(self, at_mouse):
        self.state = "attacking"
        self.attacking = [at_mouse["unit"]]

        projectile_speed_per_unit = self.attack_weapon.projectile_speed
        self.attack_to = at_mouse["mapped"]
        
        projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
        self.timers["attack_timer"].dt = projectile_distance
        self.timers["attack_timer"].reset()
        self.ap.use_point()
        self.ap.use_point()

    def swing(self, at_mouse):
        self.state = "attacking"
        self.attacking = [at_mouse["unit"]]

        self.attack_to = at_mouse["mapped"]
        self.timers["attack_timer"].dt = 0.35
        self.timers["attack_timer"].reset()
        self.ap.use_point()
        self.ap.use_point()


    def update_general(self, mpos, mpress, at_mouse, ui):
        if self.state == "dying":
            self.state = "dead"

        if self.state == "dead":
            self.end_turn = True
            return

        for t in self.timers.values():
            t.update()

        for a in self.animations.values():
            a.update()


    def update_turn(self, mpos, mpress, at_mouse, ui):
        if ui.get_selected() == "right hand":
            self.attack_weapon = self.equipment.hand_one
        elif ui.get_selected() == "left hand":
            self.attack_weapon = self.equipment.hand_two
        else:
            self.attack_weapon = None

        if self.state and self.state == "idle" and not at_mouse["ui mouseover"]:
            # walking
            if at_mouse["walkable"] and self.path == None and ui.get_selected() == "move":
                if mpress[0] == 1:
                    self.get_path = True
                    self.destination = at_mouse["mapped"]
        
            # basic attack
            if self.attack_weapon != None and self.ap.get_ap() >= 2:
                if mpress[0] == 1:
                    if self.attack_weapon.attack_type == "bomb" and (at_mouse["walkable"] == True or \
                    at_mouse["unit"] != None):
                        if in_range(at_mouse["mapped"], self.pos, get_weapon_range(self.attack_weapon)):
                            self.launch_bomb(at_mouse)
                    elif self.attack_weapon.attack_type == "shot" and at_mouse["unit"] != None and \
                    at_mouse["unit"].state not in ("dead", "dying"):
                        if in_range(at_mouse["mapped"], self.pos, get_weapon_range(self.attack_weapon)):
                            self.fire_shot(at_mouse)
                    elif self.attack_weapon.attack_type == "melee" and at_mouse["unit"] != None and \
                    at_mouse["unit"].state not in ("dead", "dying"):
                        if in_range(at_mouse["mapped"], self.pos, one_tile_range):
                            self.swing(at_mouse)

        if self.state == "dead":
            self.end_turn = True
            return

        elif self.state == "idle":
            if self.ap.end_turn:
                self.end_turn = True
            if self.path != None:
                self.state = "moving"
            if ui.get_selected() == "end turn":
                self.end_turn = True
                ui.set_selected(None)
            self.anim_state = "standing"

        elif self.state == "moving":
            skip = False
            self.anim_state = "walking"
            if self.timers["move_timer"].ticked:
                if len(self.path) == 0:
                    self.pos = self.next_pos
                    self.anim_pos = self.pos
                    self.state = "idle"
                    self.path = None
                else:
                    
                    if not self.first_move:
                        X, Y = self.pos
                        NX, NY = self.next_pos
                        VX, VY = (NX-X), (NY-Y)

                        if VX < 0:
                            self.direction = -1
                        elif VX > 0:
                            self.direction = 1

                    else:
                        self.path, self.use_points = corrigated_path(self)

                    self.first_move = False
                    
                    if not skip:
                        self.pos = self.next_pos
                        self.next_pos = self.path.pop(0)
                        use_point = self.use_points.pop(0)
                        if use_point != 0:
                            self.ap.use_fractional_point(use_point)
                        self.timers["move_timer"].reset()
            
            if not skip:
                i = self.timers["move_timer"].get_progress()
                X, Y = self.pos
                NX, NY = self.next_pos
                VX, VY = (NX-X), (NY-Y)
                AX, AY = i * VX + X, i * VY + Y
                self.anim_pos = AX, AY
        
        elif self.state == "casting":
            pass
            
        elif self.state == "attacking":
            if not self.timers["attack_timer"].ticked:
                if self.attack_weapon.attack_type == "bomb":
                    i = self.timers["attack_timer"].get_progress()
                    df_pheight = 3
                    pheight = math.sin(i*math.pi) * df_pheight
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX-X), (NY-Y)
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_pos = AX, AY - pheight
                elif self.attack_weapon.attack_type == "shot":
                    i = self.timers["attack_timer"].get_progress()
                    df_pheight = 3
                    pheight = math.sin(i*math.pi) * df_pheight
                    pheight = 0
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX-X), (NY-Y)
                    self.projectile_angle = math.degrees(math.atan2(VY, VX))
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_pos = AX, AY - pheight
                elif self.attack_weapon.attack_type == "melee":
                    i = self.timers["attack_timer"].get_progress()
                    df_pheight = 5
                    pheight = math.sin(i*math.pi) * df_pheight
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX-X), (NY-Y)
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_angle = (math.atan2(VY, VX))
                    T = 32
                    qx, qy = math.cos(self.projectile_angle) * T, math.sin(self.projectile_angle) * T# - pheight
                    self.projectile_pos = qx, qy
            else:
                self.state = "idle"
                for u in self.attacking:
                    self.damage(u)

        elif self.state == "knocked":
            pass

        elif self.state == "dying":
            self.state = "dead"

    def update(self, mpos, mpress, at_mouse, yourturn, ui):
        if yourturn:
            self.update_turn(mpos, mpress, at_mouse, ui)
        self.update_general(mpos, mpress, at_mouse, ui)


    def current_animation(self):
        return self.animations[self.anim_state]





# Units

class MC(Unit):
    def init_attributes(self):
        self.unit_name = "MC"
        self.unit_class = "sharpshooter"

    def init_health_and_base_ap(self):
        self.health = 100
        self.max_health = 100

class Bat(Unit):
    def init_attributes(self):
        self.unit_name = "Bat"

class Zombie(Unit):
    def init_attributes(self):
        self.unit_name = "Zombie"

class Brute(Unit):
    def init_attributes(self):
        self.unit_name = "Brute"

class Mage(Unit):
    def init_attributes(self):
        self.unit_name = "Mage"

class Tiny(Unit):
    def init_attributes(self):
        self.unit_name = "Tiny"