from time import clock


# Used in Animation, and used with states to time actions
class ActionTimer:
    def __init__(self, name=None, dt=None):
        self.name = ""
        if name != None:
            self.name = name
        self.dt = 0
        if dt != None:
            self.dt = dt
        self.clock = clock()

        self.ticked = False

    def get_progress(self):
        # returns progress until it ticks
        progress = (clock() - self.clock) / self.dt
        if progress > 1:
            progress = 1
        return progress

    def update(self):
        if self.ticked:
            return

        if clock() - self.clock > self.dt:
            self.ticked = True

    def reset(self):
        # reset timer
        self.clock = clock()
        self.ticked = False

    def set_tick(self):
        # override
        self.ticked = True


# animation class
# loops a series of frames with frame_timer.dt delay

class Animation:
    def __init__(self, frames):
        self.frames = frames
        self.nframe = 0

        self.frame_timer = ActionTimer()
        self.frame_timer.dt = 0.1

    def update(self):
        if self.frame_timer.ticked:
            self.nframe += 1
            if self.nframe == len(self.frames):
                self.nframe = 0
            self.frame_timer.reset()

        self.frame_timer.update()

    def restart(self):
        self.nframe = 0

    def get_frame(self):
        return self.frames[self.nframe]


class AnimationSetInitializer:
    def __init__(self, d=None):
        self.animations = {}
        if d != None:
            self.animations = d

    def new_animation_set_instance(self, name):
        aset = self.animations[name]

        d = {}
        for k in aset.keys():
            frames = aset[k]["frames"]
            anim = Animation(frames)
            anim.dt = aset[k]["dt"]

            d[k] = anim

        return d


class Label:
    def __init__(self, name, text, ypos, dt=None, color=None):
        self.timer = ActionTimer()
        if dt is None:
            self.timer.dt = 0.5
        else:
            self.timer.dt = dt
        self.timer.reset()

        self.name = name
        self.text = text
        self.ypos = ypos

        if color is None:
            self.color = (255, 255, 255)
        else:
            self.color = color

        self.xpos = 0
        self.alpha = 1

    def update(self):
        self.timer.update()
        self.xpos = 0.5 * (self.timer.get_progress() ** 0.4)
        self.alpha = 1 - self.timer.get_progress()
