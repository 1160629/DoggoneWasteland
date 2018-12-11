from equipment import Equipment, get_weapon_range
from abilities import Memory
from stats import Stats, build_skill_tree
from mutations import Mutations
from combat import AP
from control import ActionTimer, Animation, Label
from logic import get_distance, in_range, one_tile_range, corrigated_path

from random import randint, choice
import math
from itertools import product


# Unit class

def get_selected_ability(ui_slot, memory):
    for abi in memory.get_abilities():
        if abi.connected_ui_slot == ui_slot:
            return abi

    return None


def add_status(statuses, status, tick=False):
    # for a non stacking effect:
    # check if the status is currently applied
    # if its not, apply status
    # if it is, and the number of stacks left is less than
    # the number of stacks on the new ability
    # then remove the old status, and apply the new one
    # for a stacking effect:
    # check if the status is applied
    # otherwise apply it
    # if it is applied, just add the stacks
    # of new status effect to current status effect 
    o = status()
    if tick:
        o.tick()

    if o.is_stacking:
        for s in statuses:
            if s.name == o.name and s.is_active():
                s.stacks += o.stacks
                break
        else:
            statuses.append(o)

        return
    else:
        i = 0
        do_nothing = True
        for s in statuses:
            if s.name == o.name:
                if s.stacks > o.stacks:
                    do_nothing = False
                indx = i
                break
            i += 1
        else:
            # status is not currently applied
            statuses.append(o)
            return

        # old status has same number of, or more, stacks
        if do_nothing:
            return

        # new status has more stacks
        statuses.pop(indx)
        statuses.append(o)
        return


class Unit:
    def __init__(self):
        self.xp = 0
        self.xp_to_lup = 1

        self.level = 0

        self.currency = 0  # currency - bullets

        self.skilltree = build_skill_tree()

        self.sound = None #sound
        self.labels = None # labels
        self.lootmgr = None

        self.knocked = False
        self.dashing = False

        self.current_room = None

        self.pos = 0, 0

        self.animations = {}
        self.anim_pos = self.pos
        self.anim_state = "Idle"

        self.attack_type = None
        self.projectile_type = None
        self.casting_projectile = False

        # variables related to movement - make a class to containerize movement stuff?
        self.base_move_speed = 2

        self.next_pos = self.pos
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

        # variables related to casting
        self.selected_ability = None

        # control timers
        self.timers = {}
        self.timers["move_timer"] = ActionTimer("move_timer", 0.15)
        self.timers["attack_timer"] = ActionTimer("move_timer", 0.75)
        self.timers["casting_timer"] = ActionTimer("casting_timer", 1)
        self.death_timer_reset = False
        self.death_timer = ActionTimer("death_timer", 2.5)
        self.timers["death_timer"] = self.death_timer

        # size of unit
        self.area = 1

        # gear, stats, etc.
        self.equipment = Equipment()
        self.memory = Memory()
        self.mutations = Mutations()
        self.stats = Stats()
        self.ap = AP()

        self.damage_taken = 0
        self.base_health = 100

        self.statuses = []

        # basic state of the unit
        # used in general unit logic
        # current states include
        # idle, moving, attacking, dying, dead
        self.state = "idle"

        # set this to true, to end the units turn
        self.end_turn = False

        #
        self.unit_class = None
        #
        self.spawn_in_room = None
        #
        self.current_bed = None

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
        self.stats.intelligence = 0
        self.stats.dexterity = 0

    def init_equipment(self):
        pass

    def init_anything_else(self):
        pass

    def get_x_weapon(self, x):
        for w in (self.equipment.hand_one, self.equipment.hand_two):
            if w != None and w.weapon_class == x:
                return w

    def get_melee_weapon(self):
        return self.get_x_weapon("Brawler")

    def get_shooter_weapon(self):
        return self.get_x_weapon("Sharpshooter")

    def get_banger_weapon(self):
        return self.get_x_weapon("Engineer")

    def have_melee_weapon(self):
        return self.get_melee_weapon() != None

    def have_shooter_weapon(self):
        return self.get_shooter_weapon() != None

    def have_banger_weapon(self):
        return self.get_banger_weapon() != None

    def get_xp(self, amount):
        rates = [
            1,
            1,
            1,
            1,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            2,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3,
            3
        ]

        self.xp += amount
        while self.xp >= self.xp_to_lup:
            #print("Stuck")
            self.xp = self.xp - self.xp_to_lup
            if self.level >= len(rates):
                rate = 4
            else:
                rate = rates[self.level]
            self.xp_to_lup = rate
            self.level += 1
            self.labels.add_label("Level Up!", self.pos[0], self.pos[1], delay = 0)
            self.sound.play_sound_now("level up")

    def new_skill(self, node):
        if node.node_type == "stat":
            self.stats.increase_stat(node.node_is)
        elif node.node_type == "mutation":
            self.mutations.mutate(node.node_is)
        elif node.node_type == "ability":
            pass
            #self.memory.learn(node.node_is, by_name=True)

    def set_pos(self, pos):
        self.pos = pos
        self.anim_pos = pos
        self.next_pos = pos

    def finish_turn(self):
        if self.state == "dead" or self.state == "dying":
            return
        self.path = None
        self.state = "idle"
        self.anim_state = "Idle"

    def check_statuses(self, name):
        active = False
        for s in self.statuses:
            if s.name == name:
                if s.is_active():
                    active = True
                else:
                    active = False

        return active

    def get_range_bonus(self):
        if self.check_statuses("ready"):
            range_bonus = 3
        else:
            range_bonus = 0
        return range_bonus

    def get_range(self, other=0, using_weapon=True):
        bonus = self.get_range_bonus()

        if using_weapon:
            base_range = get_weapon_range(self.attack_weapon)
        else:
            base_range = 0

        r = bonus + base_range + other

        if self.check_statuses("blinded"):
            actual_range = r // 4
        else:
            actual_range = r

        if actual_range < 0:
            actual_range = 0

        return actual_range

    def get_move_speed(self):
        if self.check_statuses("go"):
            ms_bonus = 1
        else:
            ms_bonus = 0

        ms = self.base_move_speed + self.stats.strength // 2 + ms_bonus

        if self.check_statuses("slowed"):
            actual_ms = ms // 2
        else:
            actual_ms = ms

        return actual_ms

    def get_health(self):
        return self.base_health + self.stats.strength * 2

    def get_dodge(self, damagee):
        dex_based_dodge_chance = (self.stats.dexterity * 5) / (2 * 100)  # 5% for every 2 pts
        dodge_chance = (damagee.mutations.get_dodge_chance() + dex_based_dodge_chance)
        return dodge_chance

    def get_currency_range(self):
        return 1, 3

    def get_damage(self, must_crit=0, dmg_per_bonus=0, dmg_val_bonus=0):
        return (self.attack_weapon.get_damage(self.stats, self.statuses, must_crit) + dmg_val_bonus) * (
                    dmg_per_bonus / 100 + 1)

    def damage(self, damagee, dmg, can_dodge=True, weapon_used=None, lab_delay=0):
        if can_dodge and (randint(0, 100) <= damagee.get_dodge(damagee) * 100):
            self.labels.add_label("Dodge", damagee.pos[0], damagee.pos[1], delay=lab_delay)
            return
        else:
            if weapon_used != None:
                if weapon_used.last_attack_crit:
                    self.labels.add_label("Crit", damagee.pos[0], damagee.pos[1])
                    lab_delay += 0.5
            damagee.damage_taken += dmg
            self.labels.add_label("{0}".format(int(dmg)), damagee.pos[0], damagee.pos[1], delay=lab_delay, color="red")
            if damagee.get_health() - damagee.damage_taken <= 0 and damagee.state != "dead":
                damagee.state = "dying"
                self.currency += choice(damagee.get_currency_range())

        if not (damagee.unit_name in ("Jon Vegg", "Stella")):
            self.sound.play_sound_now("monster hit")
        else:
            self.sound.play_sound_now("MC hit")

    def heal(self, ht, hb, delay = 0):
        if ht == "percentage":
            heal = self.get_health() * hb
            self.damage_taken -= heal
        elif ht == "value":
            heal = hb
            self.damage_taken -= heal
        if self.damage_taken < 0:
            self.damage_taken = 0

        self.labels.add_label("" + str(int(heal)), self.pos[0], self.pos[1], color="green", delay = delay)

    def launch_bomb(self, at_mouse):
        self.state = "attacking"
        self.attacking = at_mouse["units"][self.attack_weapon.blast_radius - 2]
        projectile_speed_per_unit = self.attack_weapon.projectile_speed
        self.attack_to = at_mouse["mapped"]

        projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
        self.timers["attack_timer"].dt = projectile_distance
        self.timers["attack_timer"].reset()
        self.ap.use_point()
        self.ap.use_point()

        self.sound.play_sound_now("bomb lobbed")

        # self.labels.add_label("Lob", self.pos[0], self.pos[1])

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

        if self.attack_weapon.projectile_type == "bullet":
            self.sound.play_sound_now("bullet shot")
        elif self.attack_weapon.projectile_type == "arrow":
            self.sound.play_sound_now("arrow shot")

        # self.labels.add_label("Fire", self.pos[0], self.pos[1])

    def swing(self, at_mouse):
        self.state = "attacking"
        self.attacking = [at_mouse["unit"]]

        self.attack_to = at_mouse["mapped"]
        self.timers["attack_timer"].dt = 0.35
        self.timers["attack_timer"].reset()
        self.ap.use_point()
        self.ap.use_point()

        self.sound.play_sound_now("melee swing")

        # self.labels.add_label("Swing", self.pos[0], self.pos[1])

    def start_casting(self, at_mouse):
        self.animations["Attack"].restart()
        sabi = self.casting_ability
        sabi.use()
        self.timers["casting_timer"].dt = 0.6
        self.timers["casting_timer"].reset()
        for i in range(sabi.ap_cost):
            self.ap.use_point()

        text = sabi.name
        self.labels.add_label(text, self.pos[0], self.pos[1])

        if sabi.name in ("Steady", "Ready", "Go"):
            pass

        elif sabi.name == "First Aid Kit":
            pass

        elif sabi.name == "Bash":
            self.attack_weapon = self.equipment.hand_one
            self.attacking = [at_mouse["unit"]]
            self.attack_to = at_mouse["mapped"]
            self.sound.play_sound_now("melee swing")

        elif sabi.name == "Finisher":
            self.attack_weapon = self.equipment.hand_one
            self.attacking = [at_mouse["unit"]]
            self.attack_to = at_mouse["mapped"]
            self.sound.play_sound_now("melee swing")

        elif sabi.name == "Dinner Time":
            self.attack_weapon = self.equipment.hand_one
            self.attacking = [at_mouse["unit"]]
            self.attack_to = at_mouse["mapped"]
            self.sound.play_sound_now("melee swing")

        elif sabi.name == "Falcon Punch":
            self.attack_weapon = self.equipment.hand_one
            abirange = self.get_range(other=sabi.ability_range, using_weapon=False)
            if abirange < 2:
                self.attacking = []
            else:
                self.attacking = at_mouse["units"][abirange - 2]
                self.attacking.pop(self.attacking.index(self))
            self.attack_to = at_mouse["mapped"]
            self.sound.play_sound_now("melee swing")

        elif sabi.name == "Throw Sand":
            self.throwing_at = at_mouse["unit"]

        elif sabi.name == "Fart":
            abirange = self.get_range(other=sabi.ability_range, using_weapon=False)
            self.sound.play_sound_now("fart")
            if abirange < 2:
                self.attacking = []
            else:
                self.attacking = at_mouse["units"][abirange - 2]
                self.attacking.pop(self.attacking.index(self))

        elif sabi.name == "Dash":
            self.dashing = True
            self.dashing_to = at_mouse["mapped"]
            self.timers["casting_timer"].dt = 0.2
            self.timers["casting_timer"].reset()

        elif sabi.name == "Kneecapper":
            self.attacking = [at_mouse["unit"]]

            projectile_speed_per_unit = self.attack_weapon.projectile_speed
            self.attack_to = at_mouse["mapped"]

            projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
            self.timers["attack_timer"].dt = projectile_distance
            self.timers["attack_timer"].reset()
            # self.ap.use_point()
            # self.ap.use_point()

            if self.attack_weapon.projectile_type == "bullet":
                self.sound.play_sound_now("bullet shot")
            elif self.attack_weapon.projectile_type == "arrow":
                self.sound.play_sound_now("arrow shot")

            self.state = "casting"
            self.timers["casting_timer"].dt = self.timers["attack_timer"].dt
            self.timers["casting_timer"].reset()

            self.attack_type = self.attack_weapon.attack_type
            self.projectile_type = self.attack_weapon.attack_type

            self.casting_projectile = True

        elif sabi.name == "Lead Ammo":
            self.attacking = [at_mouse["unit"]]

            projectile_speed_per_unit = self.attack_weapon.projectile_speed
            self.attack_to = at_mouse["mapped"]

            projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
            self.timers["attack_timer"].dt = projectile_distance
            self.timers["attack_timer"].reset()
            # self.ap.use_point()
            # self.ap.use_point()

            if self.attack_weapon.projectile_type == "bullet":
                self.sound.play_sound_now("bullet shot")
            elif self.attack_weapon.projectile_type == "arrow":
                self.sound.play_sound_now("arrow shot")
            self.state = "casting"
            self.timers["casting_timer"].dt = self.timers["attack_timer"].dt
            self.timers["casting_timer"].reset()

            self.attack_type = self.attack_weapon.attack_type
            self.projectile_type = self.attack_weapon.attack_type

            self.casting_projectile = True

        elif sabi.name == "Dance Off":
            self.timers["casting_timer"].dt = 2
            self.timers["casting_timer"].reset()

        elif sabi.name == "Flash Bang":
            # self.state = "attacking"
            # self.attacking = at_mouse["units"][self.attack_weapon.blast_radius-2]
            projectile_speed_per_unit = self.attack_weapon.projectile_speed
            self.attack_to = at_mouse["mapped"]

            projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
            self.timers["attack_timer"].dt = projectile_distance
            self.timers["attack_timer"].reset()
            # self.ap.use_point()
            # self.ap.use_point()
            self.timers["casting_timer"].dt = self.timers["attack_timer"].dt
            self.timers["casting_timer"].reset()
            self.sound.play_sound_now("bomb lobbed")
            abirange = self.get_range(other=sabi.blast_radius, using_weapon=False)
            if abirange < 2:
                self.attacking = []
            else:
                self.attacking = at_mouse["units"][abirange - 2]
                # self.attacking.pop(self.attacking.index(self))

            self.attack_type = "shot"
            self.projectile_type = "bullet"

            self.casting_projectile = True

        elif sabi.name == "Molotov":
            # self.state = "attacking"
            # self.attacking = at_mouse["units"][self.attack_weapon.blast_radius-2]
            projectile_speed_per_unit = self.attack_weapon.projectile_speed
            self.attack_to = at_mouse["mapped"]

            projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
            self.timers["attack_timer"].dt = projectile_distance
            self.timers["attack_timer"].reset()
            # self.ap.use_point()
            # self.ap.use_point()
            self.timers["casting_timer"].dt = self.timers["attack_timer"].dt
            self.timers["casting_timer"].reset()
            self.sound.play_sound_now("bomb lobbed")
            abirange = self.get_range(other=sabi.blast_radius, using_weapon=False)
            if abirange < 2:
                self.attacking = []
            else:
                self.attacking = at_mouse["units"][abirange - 2]
                # self.attacking.pop(self.attacking.index(self))

            self.attack_type = "bomb"

            self.casting_projectile = True

        elif sabi.name == "Rocket Ride":
            self.dashing = True
            self.dashing_to = at_mouse["mapped"]
            self.timers["casting_timer"].dt = 1.5
            self.timers["casting_timer"].reset()
            abirange = self.get_range(other=sabi.blast_radius, using_weapon=False)
            if abirange < 2:
                self.attacking = []
            else:
                self.attacking = at_mouse["units"][abirange - 2]
                # self.attacking.pop(self.attacking.index(self))

            self.sound.play_sound_now("bomb lobbed")

        elif sabi.name == "Vaccine":
            pass

        elif sabi.name == "Holy Hand Grenade":
            # self.state = "attacking"
            # self.attacking = at_mouse["units"][self.attack_weapon.blast_radius-2]
            projectile_speed_per_unit = self.attack_weapon.projectile_speed
            self.attack_to = at_mouse["mapped"]

            projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
            self.timers["attack_timer"].dt = projectile_distance
            self.timers["attack_timer"].reset()
            # self.ap.use_point()
            # self.ap.use_point()
            self.timers["casting_timer"].dt = self.timers["attack_timer"].dt
            self.timers["casting_timer"].reset()
            self.sound.play_sound_now("bomb lobbed")
            abirange = self.get_range(other=sabi.blast_radius, using_weapon=False)
            if abirange < 2:
                self.attacking = []
            else:
                self.attacking = at_mouse["units"][abirange - 2]
                # self.attacking.pop(self.attacking.index(self))

            self.attack_type = "bomb"

            self.casting_projectile = True

        elif sabi.name == "Try To Leave":
            self.dashing = True
            self.dashing_to = at_mouse["mapped"]
            self.timers["casting_timer"].dt = 0.08
            self.timers["casting_timer"].reset()

        elif sabi.name == "Teleport Anywhere":
            self.dashing = True
            self.dashing_to = at_mouse["mapped"]
            self.timers["casting_timer"].dt = 0.1
            self.timers["casting_timer"].reset()
            
        elif sabi.name == "Destroy Anything":
            self.attacking = [at_mouse["unit"]]

            self.old_proj = self.attack_weapon.projectile_type
            self.attack_weapon.projectile_type = "arrow"
            self.old_speed = self.attack_weapon.projectile_speed
            self.attack_weapon.projectile_speed = 50

            projectile_speed_per_unit = self.attack_weapon.projectile_speed
            self.attack_to = at_mouse["mapped"]

            projectile_distance = get_distance(self.pos, self.attack_to) / projectile_speed_per_unit
            self.timers["attack_timer"].dt = projectile_distance
            self.timers["attack_timer"].reset()
            # self.ap.use_point()
            # self.ap.use_point()

            if self.attack_weapon.projectile_type == "bullet":
                self.sound.play_sound_now("bullet shot")
            elif self.attack_weapon.projectile_type == "arrow":
                self.sound.play_sound_now("arrow shot")

            self.state = "casting"
            self.timers["casting_timer"].dt = self.timers["attack_timer"].dt
            self.timers["casting_timer"].reset()

            self.attack_type = self.attack_weapon.attack_type
            self.projectile_type = self.attack_weapon.attack_type

            self.casting_projectile = True


    def update_general(self, mpos, mpress, at_mouse, ui):
        if self.state == "dying":
            self.state = "dead"
            if not (self.unit_name in ("Jon Vegg", "Stella")):
                self.sound.play_sound_with_delay("monster dying", 0.1)
            else:
                self.sound.play_sound_with_delay("MC dying", 0.1)
            self.anim_state = "Dies"
            if self.death_timer_reset == False:
                self.death_timer_reset = True
                self.death_timer.reset()
            elif self.death_timer.ticked:
                self.state = "dead"

        if self.state == "dead":
            self.end_turn = True
            self.statuses = []
            return

        for t in self.timers.values():
            t.update()

        for a in self.animations.values():
            a.update()

    def pick_up(self, lootmgr):
        pick_me_up = None
        for ls in lootmgr.loot_spawners:
            for l in ls.spawned:
                if l.pick_up == True:
                    pick_me_up = l
                    break

        if pick_me_up == None:
            return

        if not in_range(pick_me_up.pos, self.pos, 2):
            pick_me_up.dont_grab()
            self.labels.add_label("Too far away!", pick_me_up.pos[0], pick_me_up.pos[1])
            return
        

        available_slot = False
        for i in (self.equipment.hand_one, self.equipment.hand_two):
            if i == None:
                available_slot = True
                break

        if available_slot == False:
            pick_me_up.dont_grab()
            self.labels.add_label("No room!", pick_me_up.pos[0], pick_me_up.pos[1])
            return
        
        if pick_me_up.cost > self.currency:
            pick_me_up.dont_grab()
            self.labels.add_label("Can't afford!", pick_me_up.pos[0], pick_me_up.pos[1])
            return
        else:
            if pick_me_up.cost == 0:
                self.labels.add_label("Got!", pick_me_up.pos[0], pick_me_up.pos[1])
                self.sound.play_sound_now("buy")
            else:
                self.currency -= pick_me_up.cost
                self.labels.add_label("Bought!", pick_me_up.pos[0], pick_me_up.pos[1])
                self.sound.play_sound_now("buy")

            pick_me_up.grab()

        if self.equipment.hand_one == None:
            self.equipment.hand_one = pick_me_up.item
        elif self.equipment.hand_two == None:
            self.equipment.hand_two = pick_me_up.item

    def drop(self, at_mouse, mpress):
        if at_mouse["mouse ui item"] == None:
            return
        if mpress[2] != 1:
            return
        #print(at_mouse["mouse ui item"].name)
        
        if at_mouse["mouse ui item"].name == "left hand" and self.equipment.hand_two != None:
            item = self.equipment.hand_two
            self.equipment.hand_two = None
        elif at_mouse["mouse ui item"].name == "right hand" and self.equipment.hand_one != None:
            item = self.equipment.hand_one
            self.equipment.hand_one = None
        else:
            return

        avail = []
        for px, py in product(range(-2, 3, 1), range(-2, 3, 1)):
            if (0, 0) == (px, py):
                continue
            x, y = px + self.pos[0], py + self.pos[1]
            avail.append((x, y))

        self.lootmgr.new_spawner(self.pos, avail, "common", self.sound, None, \
        use_cost = False, discount = 0, assign_loot = True, loot = [(item, "weapon")])

    def learn_ability(self):
        equip_node = None
        for i in self.skilltree.all_nodes:
            if i.equip_me == True:
                equip_node = i
                break

        if equip_node == None:
            return

        equip_node.equip_me = False

        if equip_node.node_type != "ability":
            return

        if equip_node.equipped:
            return

        if self.memory.is_full():
            self.labels.add_label("No memory slots!", self.pos[0], self.pos[1])
            return
        
        name = equip_node.node_is
        
        next_slot = self.memory.get_next_slot()
        result = self.memory.learn(name, by_name = True)
        if result:
            equip_node.equipped = True
            self.memory.attach_latest_to_slot(next_slot)
            self.labels.add_label("Learned!", self.pos[0], self.pos[1])
        else:
            self.labels.add_label("Unimplemented!", self.pos[0], self.pos[1])


    def unlearn_ability(self, at_mouse, mpress):
        if mpress[2] == 0:
            return

        if at_mouse["mouse ui item"] == None:
            return

        if not ("ability" in at_mouse["mouse ui item"].name):
            return

        abi_n = at_mouse["mouse ui item"].name
        
        abi = get_selected_ability(abi_n, self.memory)
        
        if abi == None:
            return

        self.memory.unlearn(abi)

        for i in self.skilltree.all_nodes:
            if i.node_is == abi.name.lower():
                i.equipped = False
                break

        self.labels.add_label("Forget!", self.pos[0], self.pos[1])

    def update_turn(self, mpos, mpress, at_mouse, ui, in_combat, lootmgr):
        self.pick_up(lootmgr)
        self.drop(at_mouse, mpress)
        self.learn_ability()
        self.unlearn_ability(at_mouse, mpress)

        if ui.get_selected() == "right hand":
            self.attack_weapon = self.equipment.hand_one
        elif ui.get_selected() == "left hand":
            self.attack_weapon = self.equipment.hand_two

        if ui.get_selected() in ("right hand", "left hand"):
            basic_attack = True
        else:
            basic_attack = False

        if self.state == "idle" and not at_mouse["ui mouseover"]:
            # walking
            if at_mouse["walkable"] and self.path == None and ui.get_selected() == "move":
                if mpress[0] == 1:
                    self.get_path = True
                    self.destination = at_mouse["mapped"]

            # basic attack
            if self.attack_weapon != None and self.ap.get_ap() >= 2 and basic_attack and at_mouse["unit"] != self:
                if mpress[0] == 1:
                    if self.attack_weapon.attack_type == "bomb" and (at_mouse["walkable"] == True or \
                                                                     at_mouse["unit"] != None):
                        if in_range(at_mouse["mapped"], self.pos, self.get_range()):
                            self.launch_bomb(at_mouse)
                    elif self.attack_weapon.attack_type == "shot" and at_mouse["unit"] != None and \
                            at_mouse["unit"].state not in ("dead", "dying"):
                        if in_range(at_mouse["mapped"], self.pos, self.get_range()):
                            self.fire_shot(at_mouse)
                    elif self.attack_weapon.attack_type == "melee" and at_mouse["unit"] != None and \
                            at_mouse["unit"].state not in ("dead", "dying"):
                        if in_range(at_mouse["mapped"], self.pos, one_tile_range):
                            self.swing(at_mouse)

            ui_selected = ui.get_selected()
            if mpress[0] == 1 and ui_selected != None and "ability" in ui_selected:
                selected_ability = get_selected_ability(ui_selected, self.memory)
                if selected_ability != None:
                    if self.ap.get_ap() >= selected_ability.ap_cost:
                        if selected_ability.get_cooldown() == 0:
                            if selected_ability.name == "Steady":
                                if at_mouse["unit"] == self:
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "Ready":
                                if at_mouse["unit"] == self:
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "Go":
                                if at_mouse["unit"] == self:
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "First Aid Kit":
                                if at_mouse["unit"] == self:
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "Bash" and self.have_melee_weapon():
                                have_weapon = True
                                if self.have_melee_weapon():
                                    self.attack_weapon = self.get_melee_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if at_mouse["unit"] != self and in_range(at_mouse["mapped"], self.pos, one_tile_range):
                                        self.state = "casting"
                                        self.casting_ability = selected_ability
                                        self.start_casting(at_mouse)
                                else:
                                    self.labels.add_label("No brawler weapon equipped!", at_mouse["unit"].pos[0], at_mouse["unit"].pos[1])
                            elif selected_ability.name == "Finisher" and self.have_melee_weapon():
                                have_weapon = True
                                if self.have_melee_weapon():
                                    self.attack_weapon = self.get_melee_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if at_mouse["unit"] != self and in_range(at_mouse["mapped"], self.pos, one_tile_range):
                                        self.state = "casting"
                                        self.casting_ability = selected_ability
                                        self.start_casting(at_mouse)
                                else:
                                    self.labels.add_label("No brawler weapon equipped!", self.pos[0], self.pos[1])
                            elif selected_ability.name == "Dinner Time" and self.have_melee_weapon():
                                have_weapon = True
                                if self.have_melee_weapon():
                                    self.attack_weapon = self.get_melee_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if at_mouse["unit"] != self and in_range(at_mouse["mapped"], self.pos, one_tile_range):
                                        self.state = "casting"
                                        self.casting_ability = selected_ability
                                        self.start_casting(at_mouse)
                                else:
                                    self.labels.add_label("No brawler weapon equipped!", self.pos[0], self.pos[1])
                            elif selected_ability.name == "Falcon Punch" and self.have_melee_weapon():
                                have_weapon = True
                                if self.have_melee_weapon():
                                    self.attack_weapon = self.get_melee_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if at_mouse["unit"] == self:
                                        self.state = "casting"
                                        self.casting_ability = selected_ability
                                        self.start_casting(at_mouse)
                                else:
                                    self.labels.add_label("No brawler weapon equipped!", self.pos[0], self.pos[1])
                            elif selected_ability.name == "Throw Sand":
                                if in_range(at_mouse["mapped"], self.pos, self.get_range(other= \
                                                                                                selected_ability.ability_range,
                                                                                        using_weapon=False)):
                                    if at_mouse["room"] == self.current_room:
                                        self.state = "casting"
                                        self.casting_ability = selected_ability
                                        self.start_casting(at_mouse)
                                else:
                                    self.labels.add_label("Not in range!", at_mouse["mapped"][0], at_mouse["mapped"][1])
                            elif selected_ability.name == "Fart":
                                if at_mouse["unit"] == self:
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "Dash":
                                if in_range(at_mouse["mapped"], self.pos, \
                                                self.get_range(other=selected_ability.ability_range, using_weapon=False)):
                                    if at_mouse["unit"] == None and at_mouse["walkable"] == True and \
                                            at_mouse["room"] == self.current_room:
                                        self.state = "casting"
                                        self.casting_ability = selected_ability
                                        self.start_casting(at_mouse)
                                else:
                                    self.labels.add_label("Not in range!", at_mouse["mapped"][0], at_mouse["mapped"][1])
                            elif selected_ability.name == "Kneecapper" and self.have_shooter_weapon():
                                have_weapon = True
                                if self.have_shooter_weapon():
                                    self.attack_weapon = self.get_shooter_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if in_range(at_mouse["mapped"], self.pos, self.get_range()):
                                        if at_mouse["unit"] != None and at_mouse["room"] == self.current_room:
                                            self.state = "casting"
                                            self.casting_ability = selected_ability
                                            self.start_casting(at_mouse)
                                    else:
                                        self.labels.add_label("Not in range!", at_mouse["unit"].pos[0], at_mouse["unit"].pos[1])
                                else:
                                    self.labels.add_label("No sharpshooter weapon equipped!", self.pos[0], self.pos[1])
                            elif selected_ability.name == "Lead Ammo" and self.have_shooter_weapon():
                                have_weapon = True
                                if self.have_shooter_weapon():
                                    self.attack_weapon = self.get_shooter_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if in_range(at_mouse["mapped"], self.pos, self.get_range()):
                                        if at_mouse["unit"] != None and at_mouse["room"] == self.current_room:
                                            self.state = "casting"
                                            self.casting_ability = selected_ability
                                            self.start_casting(at_mouse)
                                    else:
                                        self.labels.add_label("Not in range!", at_mouse["unit"].pos[0], at_mouse["unit"].pos[1])
                                else:
                                    self.labels.add_label("No sharpshooter weapon equipped!", self.pos[0], self.pos[1])
                            elif selected_ability.name == "Dance Off":
                                if at_mouse["unit"] == self:
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "Flash Bang" and self.have_banger_weapon():
                                have_weapon = True
                                if self.have_banger_weapon():
                                    self.attack_weapon = self.get_banger_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if in_range(at_mouse["mapped"], self.pos, \
                                                        self.get_range(other=selected_ability.ability_range,
                                                                        using_weapon=False)):
                                        if \
                                            at_mouse["room"] == self.current_room:
                                            self.state = "casting"
                                            self.casting_ability = selected_ability
                                            self.start_casting(at_mouse)
                                    else:
                                        self.labels.add_label("Not in range!", at_mouse["mapped"][0], at_mouse["mapped"][1])
                                else:
                                    self.labels.add_label("No engineer weapon equipped!", self.pos[0], self.pos[1])
                            elif selected_ability.name == "Molotov" and self.have_banger_weapon():
                                have_weapon = True
                                if self.have_banger_weapon():
                                    self.attack_weapon = self.get_banger_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if in_range(at_mouse["mapped"], self.pos, \
                                                        self.get_range(other=selected_ability.ability_range,
                                                                        using_weapon=False)):
                                        if at_mouse["room"] == self.current_room:
                                            self.state = "casting"
                                            self.casting_ability = selected_ability
                                            self.start_casting(at_mouse)
                                    else:
                                        self.labels.add_label("Not in range!", at_mouse["mapped"][0], at_mouse["mapped"][1])
                                else:
                                    self.labels.add_label("No engineer weapon equipped!", self.pos[0], self.pos[1])
                            elif selected_ability.name == "Rocket Ride":
                                if in_range(at_mouse["mapped"], self.pos, \
                                                self.get_range(other=selected_ability.ability_range, using_weapon=False)):
                                    if at_mouse["unit"] == None and at_mouse["walkable"] == True and \
                                            at_mouse["room"] == self.current_room:
                                        self.state = "casting"
                                        self.casting_ability = selected_ability
                                        self.start_casting(at_mouse)
                                else:
                                    self.labels.add_label("Not in range!", at_mouse["mapped"][0], at_mouse["mapped"][1])
                            elif selected_ability.name == "Vaccine":
                                if at_mouse["unit"] == self:
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "Holy Hand Grenade":
                                have_weapon = True
                                if self.have_banger_weapon():
                                    self.attack_weapon = self.get_banger_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                        if at_mouse["room"] == self.current_room:
                                            if in_range(at_mouse["mapped"], self.pos, \
                                                                self.get_range(other=selected_ability.ability_range,
                                                                                using_weapon=False)):
                                                self.state = "casting"
                                                self.casting_ability = selected_ability
                                                self.start_casting(at_mouse)
                                            else:
                                                self.labels.add_label("Not in range!", at_mouse["mapped"][0], at_mouse["mapped"][1])
                                else:
                                    self.labels.add_label("No engineer weapon equipped!", self.pos[0], self.pos[1])
                            elif selected_ability.name == "Try To Leave":
                                if at_mouse["unit"] == None and at_mouse["walkable"] == True and \
                                        at_mouse["room"] == self.current_room and \
                                        at_mouse["mapped"] in self.current_room.get_door_positions():
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "Teleport Anywhere":
                                if at_mouse["unit"] == None and at_mouse["walkable"] == True:
                                    self.state = "casting"
                                    self.casting_ability = selected_ability
                                    self.start_casting(at_mouse)
                            elif selected_ability.name == "Destroy Anything":
                                have_weapon = True
                                if self.have_melee_weapon():
                                    self.attack_weapon = self.get_melee_weapon()
                                elif self.have_shooter_weapon():
                                    self.attack_weapon = self.get_shooter_weapon()
                                elif self.have_banger_weapon():
                                    self.attack_weapon = self.get_banger_weapon()
                                else:
                                    have_weapon = False
                                if have_weapon:
                                    if at_mouse["unit"] != None and at_mouse["unit"] != self:
                                        self.state = "casting"
                                        self.casting_ability = selected_ability
                                        self.start_casting(at_mouse)
                                else:
                                    self.labels.add_label("No weapon!", self.pos[0], self.pos[1])
                            else:
                                pass
                        else:
                            self.labels.add_label("On cooldown!", self.pos[0], self.pos[1]) # cd
                    else:
                        self.labels.add_label("Not enough AP!", self.pos[0], self.pos[1]) # no ap


        if self.state == "dead":
            self.end_turn = True
            return

        elif self.state == "idle":

            if self.check_statuses("knocked"):
                self.knocked = True
                self.end_turn = True
            else:
                self.knocked = False
                self.end_turn = False

            if self.ap.end_turn:
                self.end_turn = True
            if self.path != None:
                self.state = "moving"
            if ui.get_selected() == "end turn":
                self.end_turn = True
                ui.set_selected(None)
            self.anim_state = "Idle"

        elif self.state == "moving":
            skip = False
            self.anim_state = "Walking"
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
                        VX, VY = (NX - X), (NY - Y)

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
                            self.sound.play_sound_now("walk")
                            self.ap.use_fractional_point(use_point)
                        self.timers["move_timer"].reset()

            if not skip:
                i = self.timers["move_timer"].get_progress()
                X, Y = self.pos
                NX, NY = self.next_pos
                VX, VY = (NX - X), (NY - Y)
                AX, AY = i * VX + X, i * VY + Y
                self.anim_pos = AX, AY

        elif self.state == "casting":
            self.anim_state = "Attack"

            if self.casting_ability.name in ("Flash Bang", "Molotov", "Holy Hand Grenade"):
                i = self.timers["attack_timer"].get_progress()
                df_pheight = 3
                pheight = math.sin(i * math.pi) * df_pheight
                X, Y = self.pos
                NX, NY = self.attack_to
                VX, VY = (NX - X), (NY - Y)
                AX, AY = i * VX + X, i * VY + Y
                self.projectile_pos = AX, AY - pheight
            elif self.casting_ability.name == "Rocket Ride":
                i = self.timers["casting_timer"].get_progress()
                df_pheight = 2
                pheight = math.sin(i * math.pi) * df_pheight
                # pheight = 5
                X, Y = self.pos
                NX, NY = self.dashing_to
                VX, VY = (NX - X), (NY - Y)
                AX, AY = i * VX + X, i * VY + Y
                self.projectile_angle = (math.atan2(VY, VX))
                T = 48 * (VX ** 2 + VY ** 2) ** 0.5
                qx, qy = math.cos(self.projectile_angle) * T * i, (
                    math.sin(self.projectile_angle)) * T * i - pheight * T
                self.projectile_pos = qx, qy
            elif self.casting_ability.ability_type == "reloc - instant" or \
                    self.casting_ability.ability_type == "reloc":
                i = self.timers["casting_timer"].get_progress()
                df_pheight = 5
                pheight = math.sin(i * math.pi) * df_pheight
                pheight = 0
                X, Y = self.pos
                NX, NY = self.dashing_to
                VX, VY = (NX - X), (NY - Y)
                AX, AY = i * VX + X, i * VY + Y
                self.projectile_angle = (math.atan2(VY, VX))
                T = 48 * (VX ** 2 + VY ** 2) ** 0.5
                qx, qy = math.cos(self.projectile_angle) * T * i, math.sin(self.projectile_angle) * T * i  # - pheight
                self.projectile_pos = qx, qy
            elif self.casting_ability.ability_type == "attack - melee - debuff" or \
                    self.casting_ability.ability_type == "attack - melee":
                i = self.timers["casting_timer"].get_progress()
                df_pheight = 5
                pheight = math.sin(i * math.pi) * df_pheight
                X, Y = self.pos
                NX, NY = self.attack_to
                VX, VY = (NX - X), (NY - Y)
                AX, AY = i * VX + X, i * VY + Y
                self.projectile_angle = (math.atan2(VY, VX))
                T = 48
                qx, qy = math.cos(self.projectile_angle) * T, math.sin(self.projectile_angle) * T  # - pheight
                self.projectile_pos = qx, qy

            elif self.casting_ability.ability_type == "attack - ranged - debuff" or \
                    self.casting_ability.ability_type == "attack - ranged":
                i = self.timers["casting_timer"].get_progress()
                df_pheight = 3
                pheight = math.sin(i * math.pi) * df_pheight
                pheight = 0
                X, Y = self.pos
                NX, NY = self.attack_to
                VX, VY = (NX - X), (NY - Y)
                self.projectile_angle = math.degrees(math.atan2(VY, VX))
                AX, AY = i * VX + X, i * VY + Y
                self.projectile_pos = AX, AY - pheight

            if not self.timers["casting_timer"].ticked:
                pass
            else:
                self.state = "idle"

                if self.casting_ability.name == "Finisher":
                    hp = self.attacking[0].get_health()
                    dmg = self.attacking[0].damage_taken
                    if dmg / hp >= 0.7:
                        self.damage(self.attacking[0], self.get_damage(dmg_val_bonus=1000000))
                elif self.casting_ability.name == "Dinner Time":
                    self.attack_weapon = self.equipment.hand_one
                    dmg1 = self.get_damage(must_crit=1)
                    dmg2 = 0
                    if self.equipment.hand_two != None:
                        self.attack_weapon = self.equipment.hand_two
                        dmg2 = self.get_damage()
                    dmg = dmg1 + dmg2
                    self.damage(self.attacking[0], dmg, weapon_used=self.attack_weapon)
                elif self.casting_ability.name == "Falcon Punch":
                    dmg = self.get_damage(must_crit=1)
                    for u in self.attacking:
                        self.damage(u, dmg, weapon_used=self.attack_weapon)
                elif self.casting_ability.name == "Throw Sand":
                    if self.throwing_at != None:
                        add_status(self.throwing_at.statuses, self.casting_ability.applies)
                        self.labels.add_label("Blinded", self.throwing_at.pos[0], self.throwing_at.pos[1])
                elif self.casting_ability.name == "Fart":
                    for u in self.attacking:
                        add_status(u.statuses, self.casting_ability.applies)
                        add_status(u.statuses, self.casting_ability.also_applies)
                        u.labels.add_label("Poisoned", u.pos[0], u.pos[1])
                        u.labels.add_label("Irradiated", u.pos[0], u.pos[1], delay=0.5)
                elif self.casting_ability.name == "Dash":
                    self.dashing = False
                    self.set_pos(self.dashing_to)
                elif self.casting_ability.name == "Bash":
                    self.damage(self.attacking[0], self.get_damage())
                    self.attacking[0].knocked = True
                    add_status(self.attacking[0].statuses, self.casting_ability.applies)
                    self.labels.add_label("Knocked", self.attacking[0].pos[0], self.attacking[0].pos[1], delay=0.5)
                elif self.casting_ability.name == "Kneecapper":
                    self.damage(self.attacking[0], self.get_damage(dmg_per_bonus=20))
                    add_status(self.attacking[0].statuses, self.casting_ability.applies)
                    self.labels.add_label("Slowed", self.attacking[0].pos[0], self.attacking[0].pos[1], delay=0.5)
                    self.casting_projectile = False
                elif self.casting_ability.name == "Lead Ammo":
                    self.damage(self.attacking[0], self.get_damage(dmg_per_bonus=-20))
                    self.attacking[0].knocked = True
                    add_status(self.attacking[0].statuses, self.casting_ability.applies)
                    self.labels.add_label("Knocked", self.attacking[0].pos[0], self.attacking[0].pos[1], delay=0.5)
                    self.casting_projectile = False
                elif self.casting_ability.name == "Dance Off":
                    for u in in_combat:
                        if u == self:
                            continue
                        add_status(u.statuses, self.casting_ability.applies)
                        u.labels.add_label("Blinded", u.pos[0], u.pos[1])

                elif self.casting_ability.name == "Try To Leave":
                    self.dashing = False
                    self.set_pos(self.dashing_to)

                elif self.casting_ability.name == "Flash Bang":
                    for u in self.attacking:
                        add_status(u.statuses, self.casting_ability.applies)
                        add_status(u.statuses, self.casting_ability.also_applies)
                        u.labels.add_label("Slowed", u.pos[0], u.pos[1])
                        u.labels.add_label("Blinded", u.pos[0], u.pos[1], delay=0.5)

                    self.sound.play_sound_now("bomb explode")
                    self.casting_projectile = False

                elif self.casting_ability.name == "Molotov":
                    for u in self.attacking:
                        dmg = self.get_damage(dmg_per_bonus=-20)
                        self.damage(u, dmg, weapon_used=self.equipment.hand_one)
                        add_status(u.statuses, self.casting_ability.applies)
                        u.labels.add_label("Burning", u.pos[0], u.pos[1], delay=0.5)

                    self.sound.play_sound_now("bomb explode")
                    self.casting_projectile = False

                elif self.casting_ability.name == "Rocket Ride":
                    self.dashing = False
                    self.set_pos(self.dashing_to)

                    for u in self.attacking:
                        add_status(u.statuses, self.casting_ability.applies)
                        self.labels.add_label("Knocked", u.pos[0], u.pos[1])

                elif self.casting_ability.name == "Vaccine":
                    self.labels.add_label("Statuses cleared", self.pos[0], self.pos[1])
                    self.statuses = []

                elif self.casting_ability.name == "Holy Hand Grenade":
                    for u in self.attacking:
                        dmg = self.get_damage(must_crit=1)
                        self.damage(u, dmg, weapon_used=self.equipment.hand_one)
                        u.knocked = True
                        add_status(u.statuses, self.casting_ability.applies)
                        u.labels.add_label("Knocked", u.pos[0], u.pos[1], delay=0.5)

                    self.sound.play_sound_now("bomb explode")
                    self.casting_projectile = False

                elif self.casting_ability.ability_type == "buff - self":
                    add_status(self.statuses, self.casting_ability.applies, tick=True)
                    self.labels.add_label(self.casting_ability.name, self.pos[0], self.pos[1])
                elif self.casting_ability.ability_type == "heal - self":
                    #self.labels.add_label(self.casting_ability.name, self.pos[0], self.pos[1])
                    self.heal(self.casting_ability.heal_type, self.casting_ability.heal_by)
                    

                if self.casting_ability.any_sounds != False:
                    for snd_name in self.casting_ability.sound_names:
                        self.sound.play_sound_now(snd_name)

                elif self.casting_ability.name == "Teleport Anywhere":
                    self.dashing = False
                    self.set_pos(self.dashing_to)

                elif self.casting_ability.name == "Destroy Anything":
                    self.damage(self.attacking[0], self.get_damage(dmg_per_bonus=1000000))
                    self.casting_projectile = False
                    self.attack_weapon.projectile_type = self.old_proj
                    self.attack_weapon.projectile_speed = self.old_speed

        elif self.state == "attacking":
            self.anim_state = "Attack"
            if not self.timers["attack_timer"].ticked:
                if self.attack_weapon.attack_type == "bomb":
                    i = self.timers["attack_timer"].get_progress()
                    df_pheight = 3
                    pheight = math.sin(i * math.pi) * df_pheight
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX - X), (NY - Y)
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_pos = AX, AY - pheight
                elif self.attack_weapon.attack_type == "shot":
                    i = self.timers["attack_timer"].get_progress()
                    df_pheight = 3
                    pheight = math.sin(i * math.pi) * df_pheight
                    pheight = 0
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX - X), (NY - Y)
                    self.projectile_angle = math.degrees(math.atan2(VY, VX))
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_pos = AX, AY - pheight
                elif self.attack_weapon.attack_type == "melee":
                    i = self.timers["attack_timer"].get_progress()
                    df_pheight = 5
                    pheight = math.sin(i * math.pi) * df_pheight
                    X, Y = self.pos
                    NX, NY = self.attack_to
                    VX, VY = (NX - X), (NY - Y)
                    AX, AY = i * VX + X, i * VY + Y
                    self.projectile_angle = (math.atan2(VY, VX))
                    T = 48
                    qx, qy = math.cos(self.projectile_angle) * T, math.sin(self.projectile_angle) * T  # - pheight
                    self.projectile_pos = qx, qy
            else:
                self.state = "idle"
                for u in self.attacking:
                    self.damage(u, self.get_damage(), weapon_used=self.attack_weapon)

                if self.attack_weapon.attack_type == "bomb":
                    self.sound.play_sound_now("bomb explode")

        elif self.state == "knocked":
            pass

        elif self.state == "resting":
            self.anim_state = "Idle"
            if self.current_bed != None and self.current_bed.done_resting:
                self.state = "idle"

        elif self.state == "dying":
            self.anim_state = "Dies"
            if not (self.unit_name in ("Jon Vegg", "Stella")):
                self.sound.play_sound_with_delay("monster dying", 0.1)
            else:
                self.sound.play_sound_with_delay("MC dying", 0.1)
            if self.death_timer_reset == False:
                self.death_timer_reset = True
                self.death_timer.reset()
            elif self.death_timer.ticked:
                self.state = "dead"

        
    def update(self, mpos, mpress, at_mouse, yourturn, ui, in_combat, lootmgr):
        if yourturn:
            self.update_turn(mpos, mpress, at_mouse, ui, in_combat, lootmgr)
        self.update_general(mpos, mpress, at_mouse, ui)

    def start_turn(self):
        remove = []
        i = 0
        for s in self.statuses:
            s.tick()
            if not s.is_active():
                remove.append(i)
            else:
                if s.name == "poisoned":
                    self.damage(self, s.damage, can_dodge=False, lab_delay=0.5)
                    self.labels.add_label("Poison", self.pos[0], self.pos[1])
                elif s.name == "irradiated":
                    pass
                elif s.name == "burning":
                    dmg_per = 2.5
                    dmg_f = dmg_per / 100
                    hp = self.get_health()
                    dmg = hp * dmg_f
                    self.damage(self, dmg, can_dodge=False, lab_delay=0.5)
                    self.labels.add_label("Burn", self.pos[0], self.pos[1])
                elif s.name == "bleeding":
                    dmg_per = 1
                    dmg_f = dmg_per / 100
                    hp = self.get_health()
                    dmg = hp * dmg_f
                    self.damage(self, dmg, can_dodge=False, lab_delay=0.5)
                    self.labels.add_label("Bleed", self.pos[0], self.pos[1])

            i += 1

        for r in reversed(remove):
            self.statuses.pop(r)

        self.memory.lower_cds()

    def current_animation(self):
        return self.animations[self.anim_state]


# Units

class MC(Unit):
    def init_attributes(self):
        self.unit_name = "Jon Vegg"
        self.anim_name = "Jon Vegg"

    def init_health_and_base_ap(self):
        self.health = 100

class Zombie(Unit):
    def init_attributes(self):
        self.unit_name = "Zombie"
        self.anim_name = "Medium Green Troll2"


class Sneak(Unit):
    def init_attributes(self):
        self.unit_name = "Sneak"
        self.anim_name = "Hooded Guy"


class Mage(Unit):
    def init_attributes(self):
        self.unit_name = "Mage"
        self.anim_name = "Skull Mask Troll"


class RedDevil(Unit):
    def init_attributes(self):
        self.unit_name = "Devil"
        self.anim_name = "Medium Red Devil"


class Tiny(Unit):
    def init_attributes(self):
        self.unit_name = "Tiny"
        self.anim_name = "Small Green Troll"


class Gramps(Unit):
    def init_attributes(self):
        self.unit_name = "Gramps"
        self.anim_name = "Gramps"