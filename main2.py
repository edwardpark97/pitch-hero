#pset7.py

import sys
from common.core import *
from common.audio import *
from common.mixer import *
from common.wavegen import *
from common.wavesrc import *
from common.gfxutil import *
from input.input_demo import *

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
        self.channel_select = 0
        self.song_data = SongData()
        self.audio_ctrl = AudioController("ims_proj_song1.wav", self.receive_audio)
        self.gem_data = self.song_data.read_data("notes_user.txt")
        self.measure_data = self.gem_data
        self.beat_match_display = BeatMatchDisplay(self.gem_data)
        self.player = Player(self.gem_data, self.beat_match_display, self.audio_ctrl)
        self.pitch = PitchDetector()
        self.start_time = kivyClock.get_time()
        self.cur_pitch = 0
        self.current_note_idx = 0
        self.time = 0
        self.score = 0
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        self.info = topleft_label()
        self.info.text = str(self.get_mouse_pos())
        self.color = Color(0,0,0, .5)
        self.rect = Rectangle(pos=(0,0), size=(600,800))
        # self.canvas.add(self.color)
        self.canvas.add(self.color)
        self.canvas.add(self.rect)
        # self.canvas.add(Rectangle(pos=(0,0), size=(800,600)))
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            self.audio_ctrl.toggle()

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
        self.audio_ctrl.on_update()
        self.player.on_update()
        self.time = self.audio_ctrl.wave_file_gen.frame/44100.
        if self.gem_data[0][self.current_note_idx + 1] < self.time:
            self.current_note_idx += 1

    def receive_audio(self, frames, num_channels) :
        # handle 1 or 2 channel input.
        # if input is stereo, mono will pick left or right channel. This is used
        # for input processing that must receive only one channel of audio (RMS, pitch, onset)
        if num_channels == 2:
            mono = frames[self.channel_select::2] # pick left or right channel
        else:
            mono = frames

        self.cur_pitch = self.pitch.write(mono)

        cur_note = self.gem_data[1][self.current_note_idx]
        self.info.text = "Current Note to Sing: " + str(cur_note) + "\n"
        self.info.text += "Current Singing Note: " + str(self.cur_pitch)

        if cur_note == round(self.cur_pitch) or cur_note + 12 == round(self.cur_pitch) or cur_note + 24 == round(self.cur_pitch):
            print True
            self.score += 1
            print self.score
            self.color.rgb = (0,1,0)
        else:
            print False
            self.color.rgb = (0,0,0)






# creates the Audio driver
# creates a song and loads it with solo and bg audio tracks
# creates snippets for audio sound fx
class AudioController(object):
    def __init__(self, song_path, receive_audio_callback):
        super(AudioController, self).__init__()
        self.audio = Audio(2, input_func=receive_audio_callback)
        self.mixer = Mixer()
        self.io_buffer = IOBuffer()
        self.mixer.add(self.io_buffer)
        self.audio.set_generator(self.mixer)

        self.wave_file_gen = WaveGenerator(WaveFile(song_path))
        self.mixer.add(self.wave_file_gen)

        self.paused = False

    # start / stop the song
    def toggle(self):
        if self.paused:
            self.paused = False
        else:
            self.paused = True

    # mute / unmute the solo track
    def set_mute(self, mute):
        if mute:
            self.wave_file_gen_solo.set_gain(0)
        else:
            self.wave_file_gen_solo.set_gain(1)

    # needed to update audio
    def on_update(self):
        if not self.paused:
            self.audio.on_update()
        else:
            pass


# holds data for gems and barlines.
class SongData(object):
    def __init__(self):
        super(SongData, self).__init__()

    # read the gems and song data. You may want to add a secondary filepath
    # argument if your barline data is stored in a different txt file.
    def read_data(self, filepath):
        lines = self.lines_from_file(filepath)
        gem_times = []
        gem_notes = []
        for line in lines:
            tokens = self.tokens_from_line(line)
            gem_times.append(float(tokens[0]))
            gem_notes.append(int(tokens[1]))

        return [gem_times, gem_notes]

    def read_measures(self, filepath):
        lines = self.lines_from_file(filepath)
        measure_times = []
        for line in lines:
            tokens = self.tokens_from_line(line)
            measure_times.append(float(tokens[0]))
        return measure_times

    def lines_from_file(self, filename):
        f = open(filename, 'r')
        return f.readlines()

    # given a line,
    # return its tab-delimited entries as a list of strings (keep out new lines and tabs).
    def tokens_from_line(self, line):
        new_string = line.strip()
        return new_string.split("\t")



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
