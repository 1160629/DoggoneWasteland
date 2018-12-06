import pygame
from control import ActionTimer
from random import choice, randint


class Music:
    # plays music according to stage.
    # doesn't always play something;
    # think Minecraft - it only plays
    # a song occasionally
    def __init__(self):
        self.songs = {}

        self.song_playing = False

        self.intermezzo = False
        self.intermezzo_range = (10, 60)

        self.timer = ActionTimer("silence timer", 10)

        self.fade_timer = ActionTimer("fade", 10)

        self.current_stage = None

        self.stage_conversion = {
            0: "farm",
            1: "bubbas",
            2: "cave",
            3: "park"
        }

        self.rel = None

        self.fade_type = None

        self.muted = False

    def play_new_song(self):
        stage_actual = self.stage_conversion[self.current_stage]
        song = choice(self.songs[stage_actual])
        pygame.mixer.music.load(self.rel+song)
        pygame.mixer.music.play()

    def update(self):
        self.timer.update()
        self.fade_timer.update()
        if self.intermezzo:
            if self.timer.ticked:
                self.intermezzo = False
        else:
            if self.song_playing == False:
                self.play_new_song()        
                self.song_playing = True
                pygame.mixer.music.set_volume(0)
                self.fade_timer.reset()
                self.fade_type = 1
            else:
                if not pygame.mixer.music.get_busy():
                    self.song_playing = False
                    self.intermezzo = True
                    intermezzo_time = randint(*self.intermezzo_range)
                    self.timer.dt = intermezzo_time
                    self.timer.reset()
                else:
                    if not self.fade_timer.ticked:
                        if self.fade_type == 1:
                            volume = self.fade_timer.get_progress()
                        elif self.fade_type == -1:
                            volume = 1 - self.fade_timer.get_progress()
                        pygame.mixer.music.set_volume(volume)
                    else:
                        if pygame.mixer.music.get_volume() != 1:
                            pygame.mixer.music.set_volume(1)
                        song_pos_secs = pygame.mixer.music.get_pos() / 1000
                        if 90 - self.fade_timer.dt <= song_pos_secs:
                            self.fade_timer.reset()
                            self.fade_type = -1

                    if self.muted:
                        pygame.mixer.music.set_volume(0)

class SoundManager:
    def __init__(self):
        self.to_play = []

        self.sounds = {}

    def play_sound(self, sound_name):
        sound = choice(self.sounds[sound_name])
        sound.play()

    def play_sound_now(self, sound_name):
        ele = sound_name, None
        self.to_play.append(ele)

    def play_sound_with_delay(self, sound_name, delay):
        ele = sound_name, ActionTimer("delay", delay)
        self.to_play.append(ele)

    def update(self):
        new_to_play = []
        for snd, timer in self.to_play:
            if timer == None or timer.ticked:
                self.play_sound(snd)
            else:
                timer.update()
                new_to_play.append((snd, timer))

        self.to_play = new_to_play

    def setup_sounds(self, snd_rel, ds):
        sounds = {}
        for k, l in ds.items():
            sounds[k] = []
            for i in l:
                path, volume = i
                new_i = pygame.mixer.Sound(snd_rel+path)
                new_i.set_volume(volume)
                sounds[k].append(new_i)

        self.sounds = sounds