#pset7.py

import sys
from common.core import *
from common.audio import *
from common.mixer import *
from common.wavegen import *
from common.wavesrc import *
from common.gfxutil import *

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.clock import Clock as kivyClock

import random
import numpy as np
import bisect


class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            pass

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
        pass


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
    def __init__(self):
        super(SongData, self).__init__()

    # read the gems and song data. You may want to add a secondary filepath
    # argument if your barline data is stored in a different txt file.
    def read_data(self, filepath):
        pass

    # TODO: figure out how gem and barline data should be accessed...



# display for a single gem at a position with a color (if desired)
class GemDisplay(InstructionGroup):
    def __init__(self, pos, color):
        super(GemDisplay, self).__init__()

    # change to display this gem being hit
    def on_hit(self):
        pass

    # change to display a passed gem
    def on_pass(self):
        pass

    # useful if gem is to animate
    def on_update(self, dt):
        pass

# Displays the arrow that indicates what pitch you're currently singing
class ArrowDisplay(InstructionGroup):
    def __init__(self, pos):
        super(ArrowDisplay, self).__init__()

    # displays when you update the pitch of the arrow
    def on_pitch(self, pitch):
        pass


# Displays and controls all game elements: Nowbar, Buttons, BarLines, Gems.
class BeatMatchDisplay(InstructionGroup):
    def __init__(self, gem_data):
        super(BeatMatchDisplay, self).__init__()

    # called by Player. Causes the right thing to happen
    def gem_hit(self, gem_idx):
        pass

    # called by Player. Causes the right thing to happen
    def gem_pass(self, gem_idx):
        pass

    # called by Player. Causes the right thing to happen
    def on_pitch(self, pitch):
        pass

    # call every frame to make gems and barlines flow down the screen
    def on_update(self) :
        pass



# Handles game logic and keeps score.
# Controls the display and the audio
class Player(object):
    def __init__(self, gem_data, display, audio_ctrl):
        super(Player, self).__init__()

    # called by MainWidget
    def on_pitch(self, pitch):
        pass

    # needed to check if for pass gems (ie, went past the slop window)
    def on_update(self):
        pass

    # returns the score
    def get_score(self):
        pass

run(MainWidget)
