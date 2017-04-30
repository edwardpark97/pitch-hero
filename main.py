#pset7.py

import sys
from common.core import *
from common.audio import *
from common.mixer import *
from common.wavegen import *
from common.wavesrc import *
from common.gfxutil import *

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.core.image import Image
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock

import random
import numpy as np
import bisect
from math import sqrt

GEMS_FILEPATH = "data/fake_gems.txt"
BARLINES_FILEPATH = "data/fake_barlines.txt"

VELOCITY = 200
GRAVITY = -300
GEM_SIZE = 40
NOW_BAR_POS = 100

MAX_PITCH = 70 # preferably exclusive?
MIN_PITCH = 60

def pitch_to_height(pitch): # center of each gem
    return 1. * (pitch - MIN_PITCH) / (MAX_PITCH - MIN_PITCH) * Window.height

def height_to_vel(height, new_height):
    top_height = max(height, new_height) + 50
    return sqrt(abs(2 * GRAVITY * (top_height - height)))

class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        self.info = topleft_label()
        self.add_widget(self.info)

        # Get data
        self.songdata = SongData(GEMS_FILEPATH, BARLINES_FILEPATH)
        self.gem_data = self.songdata.get_gems()
        self.barline_data = self.songdata.get_barlines()

        # Create beat_match
        self.beat_match = BeatMatchDisplay(self.gem_data, self.barline_data)
        self.canvas.add(self.beat_match)

        self.beat_match.toggle()

        # Create Player
        self.player = Player(self.beat_match)

        self.pitch = (MAX_PITCH + MIN_PITCH) / 2

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            self.beat_match.toggle()

        if keycode[1] == 'up':
            self.pitch += .5
        if keycode[1] == 'down':
            self.pitch -= .5

        # button down
        button_idx = lookup(keycode[1], '12345', (0,1,2,3,4))
        if button_idx != None:
            print 'down', button_idx

    def on_key_up(self, keycode):
        # button up
        button_idx = lookup(keycode[1], '12345', (0,1,2,3,4))
        if button_idx != None:
            print 'up', button_idx

    def on_update(self) :
        self.beat_match.on_update()
        self.info.text = 'score:%d' % self.player.get_score()
        self.beat_match.on_pitch(self.pitch)


# creates the Audio driver
# creates a song and loads it with solo and bg audio tracks
# creates snippets for audio sound fx
class AudioController(object):
    def __init__(self, song_path):
        super(AudioController, self).__init__()
        self.audio = Audio(2)

    # start / stop the song
    def toggle(self):
        pass

    # mute / unmute the solo track
    def set_mute(self, mute):
        pass

    # play a sound-fx (miss sound)
    def play_sfx(self):
        pass

    # needed to update audio
    def on_update(self):
        self.audio.on_update()


# holds data for gems and barlines.
class SongData(object):
    def __init__(self, filepath, barline_filepath):
        super(SongData, self).__init__()
        self.gems = []
        self.barlines = []

        for line in open(filepath).readlines():
            tokens = line.strip().split("\t")
            time = float(tokens[0])
            pitch = int(float(tokens[1]))
            if pitch < MIN_PITCH or pitch > MAX_PITCH:
                # haven't processed this yet TODO
                pitch = random.randint(MIN_PITCH + 1, MAX_PITCH - 1)
            self.gems.append((time, pitch))

        for line in open(barline_filepath).readlines():
            tokens = line.strip().split("\t")
            time = float(tokens[0])
            self.barlines.append(time)

    def get_gems(self):
        return self.gems

    def get_barlines(self):
        return self.barlines


# display for a single gem at a position with a color (if desired)
class GemDisplay(InstructionGroup):
    def __init__(self, pos, color):
        super(GemDisplay, self).__init__()

        new_pos = (pos[0] - GEM_SIZE / 2, pos[1] - GEM_SIZE / 2)

        self.border_color = Color(0, 0, 0)
        self.add(self.border_color)

        self.border = Line(rounded_rectangle=(new_pos[0], new_pos[1], GEM_SIZE, GEM_SIZE, 10))
        self.add(self.border)

        self.rect_color = Color(color[0], color[1], color[2], 0.8)
        self.add(self.rect_color)

        self.rect = RoundedRectangle(pos=new_pos, size=(GEM_SIZE, GEM_SIZE))
        self.add(self.rect)

    # change to display this gem being hit
    def on_hit(self):
        self.rect_color.r = 0
        self.rect_color.g = 1

    # change to display a passed gem
    def on_pass(self):
        self.rect_color.r = 1
        self.rect_color.g = 0

    # useful if gem is to animate
    def on_update(self, dt):
        pass


# Stolen pretty blatantly from gfxutil.py
class CRectangle(Rectangle):
    def __init__(self, **kwargs):
        super(CRectangle, self).__init__(**kwargs)
        if kwargs.has_key('cpos'):
            self.cpos = kwargs['cpos']
        if kwargs.has_key('csize'):
            self.csize = kwargs['csize']
    def get_cpos(self):
        return (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1]/2)
    def set_cpos(self, p):
        self.pos = (p[0] - self.size[0]/2 , p[1] - self.size[1]/2)
    def get_csize(self) :
        return self.size
    def set_csize(self, p) :
        cpos = self.get_cpos()
        self.size = p
        self.set_cpos(cpos)
    cpos = property(get_cpos, set_cpos)
    csize = property(get_csize, set_csize)


# Creates the background
class BackgroundDisplay(InstructionGroup):
    def __init__(self):
        super(BackgroundDisplay, self).__init__()
        Window.clearcolor = (1, 1, 1, 1)
        self.add(Color(1, 1, 1, .5))
        self.add(Rectangle(pos=(0,0), size=(Window.width, Window.height), texture=Image('data/background.jpg').texture))
        self.add(Color(1, 1, 1, .8))
        self.add(Rectangle(pos=(0,380), size=(Window.width, Window.height - 300), texture=Image('data/logo.png').texture))


# Displays the arrow that indicates what pitch you're currently singing
class ArrowDisplay(InstructionGroup):
    def __init__(self):
        super(ArrowDisplay, self).__init__()

        height = Window.height / 2

        self.image = CRectangle(cpos=(NOW_BAR_POS - GEM_SIZE/2 - 20, height), csize=(40,30), texture=Image('data/arrow.png').texture)
        self.add(self.image)

        self.add(Color(0, 0, 0, .3))    # is black
        self.line = Line(points=(NOW_BAR_POS - GEM_SIZE/2, height, Window.width, height))
        self.add(self.line)

    # displays when you update the pitch of the arrow
    def on_height(self, height):
        self.image.set_cpos((NOW_BAR_POS - GEM_SIZE/2 - 20, height))
        self.line.points = (NOW_BAR_POS - GEM_SIZE/2, height, Window.width, height)


# display for a bar line
class BarLineDisplay(InstructionGroup):
    def __init__(self, width):
        super(BarLineDisplay, self).__init__()
        self.add(Color(0,0,0,.3))          # is black
        self.add(Line(points=(width, 0, width, Window.height)))


# display for the now bar
class NowBarDisplay(InstructionGroup):
    def __init__(self):
        super(NowBarDisplay, self).__init__()
        self.add(Color(0,0,0,1))
        self.add(Line(points=(NOW_BAR_POS, 0, NOW_BAR_POS, Window.height), width=3))


# Displays the ball
class BallDisplay(InstructionGroup):
    def __init__(self, gem_data, callback):
        super(BallDisplay, self).__init__()

        self.pos = (NOW_BAR_POS, self.pitch_to_ball_height(gem_data[0][1]))
        self.vel = 0

        self.border_color = Color(0, 0, 0)
        self.add(self.border_color)

        self.border = Line(circle=(self.pos[0], self.pos[1], GEM_SIZE/2))
        self.add(self.border)

        self.ball_color = Color(1, 1, 1, .5)
        self.add(self.ball_color)

        self.ball = CEllipse(cpos=self.pos, csize=(GEM_SIZE, GEM_SIZE))
        self.add(self.ball)

        self.gem_data = gem_data
        self.callback = callback
        self.idx = 0    # the index of the next gem we're looking to hit

        self.time = 0

    def pitch_to_ball_height(self, pitch):
        return pitch_to_height(pitch) + GEM_SIZE

    def on_update(self, dt):
        # TODO: beginning stuff, ending stuff

        # stay there if all notes are done
        if self.idx >= len(self.gem_data):
            return

        # update time and idx
        # TODO: change if to a while?
        self.time += dt
        if self.time > self.gem_data[self.idx][0]:  # bounced
            self.vel = -self.vel
            self.pos = (self.pos[0], self.pitch_to_ball_height(self.gem_data[self.idx][1]))
            self.callback(self.idx)
            self.idx += 1

        if self.idx == 0:
            return

        old_time = self.gem_data[self.idx - 1][0]
        new_time = self.gem_data[self.idx][0]
        old_height = self.pitch_to_ball_height(self.gem_data[self.idx - 1][1])
        new_height = self.pitch_to_ball_height(self.gem_data[self.idx][1])
        old_vel = height_to_vel(old_height, new_height)
        
        time_from_old_time = (-old_vel - sqrt(old_vel * old_vel + 2 * GRAVITY * (new_height - old_height))) / GRAVITY
        time_accel = time_from_old_time / (new_time - old_time)

        new_time_diff = time_accel * (self.time - old_time)
        new_pos = old_vel * new_time_diff + .5 * GRAVITY * new_time_diff * new_time_diff + old_height

        # calculate the desired position
        self.pos = (self.pos[0], new_pos)
        self.border.circle = (self.pos[0], self.pos[1], GEM_SIZE/2)
        self.ball.cpos = self.pos


# Displays and controls all game elements: Nowbar, Buttons, BarLines, Gems.
class BeatMatchDisplay(InstructionGroup):
    def __init__(self, gem_data, barline_data):
        super(BeatMatchDisplay, self).__init__()

        self.gem_data = gem_data
        self.barline_data = barline_data

        # Set up background and nowbar
        self.add(NowBarDisplay())
        self.add(BackgroundDisplay())

        # Set up arrow and ball
        self.arrow = ArrowDisplay()
        self.ball = BallDisplay(self.gem_data, self.gem_hit)
        self.add(self.arrow)
        self.add(self.ball)

        # Set up translate
        self.translate = Translate(0, 0)
        self.add(self.translate)

        # Set up all gems and barlines
        self.gems = []
        for time, pitch in self.gem_data:
            pos = (NOW_BAR_POS + VELOCITY * time, pitch_to_height(pitch))
            self.gems.append(GemDisplay(pos, (1,1,0)))  # TODO: they're all green rn
            self.add(self.gems[-1])
        self.barlines = []
        for time in self.barline_data:
            self.barlines.append(BarLineDisplay(NOW_BAR_POS + VELOCITY * time))
            self.add(self.barlines[-1])
        print self.barlines

        self.playing = True
        self.needs_update = []

    def add(self, obj):
        super(BeatMatchDisplay, self).add(obj)

    def toggle(self):
        self.playing = (not self.playing)

    # called by Player. Causes the right thing to happen
    def gem_hit(self, gem_idx):
        self.gems[gem_idx].on_hit()

    # called by Player. Causes the right thing to happen
    def gem_pass(self, gem_idx):
        self.gems[gem_idx].on_pass()

    # called by Player. Causes the right thing to happen
    def on_pitch(self, pitch):
        self.arrow.on_height(pitch_to_height(pitch))

    # call every frame to make gems and barlines flow down the screen
    def on_update(self) :
        if self.playing:
            dt = kivyClock.frametime
            self.translate.x -= VELOCITY * dt

            self.ball.on_update(dt)

            keep = []
            for obj in self.needs_update:
                if obj.on_update(dt):
                    keep.append(obj)
            self.needs_update = keep


# Handles game logic and keeps score.
# Controls the display and the audio
class Player(object):
    def __init__(self, display):
        super(Player, self).__init__()
        self.display = display
        # self.gems = display.get_gems()

        self.idx = 0

        self.score = 0

    # called by MainWidget
    def on_pitch(self, pitch):
        self.display.on_pitch(pitch)

    # needed to check if for pass gems (ie, went past the slop window)
    def on_update(self):
        pass

    # returns the score
    def get_score(self):
        return self.score

run(MainWidget)