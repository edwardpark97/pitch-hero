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
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.core.image import Image
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from common.kivyparticle import ParticleSystem
from kivy.uix.popup import Popup
from kivy.uix.image import Image as Image2

import random
import numpy as np
from math import sqrt

GEMS_FILEPATH = "notes_guide.txt"
BARLINES_FILEPATH = "data/fake_barlines.txt"

VELOCITY = 200
GRAVITY = -300
GEM_SIZE = 40
NOW_BAR_POS = 200

AUDIO_DELAY = 0.0

MAX_PITCH = 49 # preferably exclusive?
MIN_PITCH = 32
PITCHES = [(36, 'C'), (40, 'E'), (43, 'G'), (48, 'C')] # tonic, third, and fifth for c major
TEMPO = 120

def pitch_to_height(pitch): # center of each gem
    return 1. * (pitch - MIN_PITCH) / (MAX_PITCH - MIN_PITCH) * Window.height

def height_to_vel(height, new_height):
    top_height = max(height, new_height) + 50
    return sqrt(abs(2 * GRAVITY * (top_height - height)))

def clip(x, min, max):
    if x < min:
        return min
    if x > max:
        return max
    return x

class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        # popup = Popup(title='Test popup',
        # content=Label(text='Hello world'),
        # size_hint=(None, None), size=(400, 400))
        # popup.open()

        self.channel_select = 0
        self.audio_ctrl = AudioController("ims_proj_song1.wav", self.receive_audio)
        self.pitch_detect = PitchDetector()
        self.cur_pitch = 0
        self.current_note_idx = 0
        self.time = 0
        self.score = 0
        self.note_score = 0

        self.canvas.add(BackgroundDisplay())

        self.score_label = Label(font_size='25sp', pos=(Window.width * 1.28, Window.height * 0.4),
            text_size=(Window.width, Window.height), color=(0,0,0,1))
        self.add_widget(self.score_label)
        self.mult_label = Label(font_size='25sp', pos=(Window.width * 0.48, Window.height * 0.4),
            text_size=(Window.width, Window.height), color=(0,0,0,1))
        self.add_widget(self.mult_label)

        # Get data
        self.songdata = SongData(GEMS_FILEPATH, BARLINES_FILEPATH)
        self.gem_data = self.songdata.get_gems()
        self.barline_data = self.songdata.get_barlines()

        # Create beat_match
        self.beat_match = BeatMatchDisplay(self.gem_data, self.barline_data, self)
        self.canvas.add(self.beat_match)

        self.octave = 12
        self.streak = 0
        self.multiplier = 1
        self.hit_all_notes_in_phrase = True

        self.beat_match.toggle()

        self.fireworks = []

        wimg = Image2(source='data/fireworks4.gif', anim_delay=.05, size=(100,100))
        self.add_widget(wimg)

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            self.beat_match.toggle()
            self.audio_ctrl.toggle()

        if keycode[1] == 'up':
            self.octave += 12
        if keycode[1] == 'down':
            self.octave -= 12
        if keycode[1] == 'k':
            self.fireworks.append(Fireworks((Window.width * 0.25 - self.beat_match.translate.x, Window.height * 0.06), True, self))

    def on_update(self) :
        self.beat_match.on_update()
        self.beat_match.arrow.on_pitch(self.cur_pitch - self.octave)
        self.audio_ctrl.on_update()

        keep_list = []
        for firework in self.fireworks:
            if firework.on_update():
                keep_list.append(firework)
        self.fireworks = keep_list

        self.time = self.audio_ctrl.wave_file_gen.frame/44100.
        if self.gem_data[self.current_note_idx + 1][0] + AUDIO_DELAY < self.time:
            # figure out hit_all_notes_in_phrase
            if self.beat_match.gems[self.current_note_idx].role:
                if not self.beat_match.gems[self.current_note_idx].was_sung:
                    self.multiplier = 1
                    self.beat_match.ball.update_multiplier(self.multiplier)
                    self.hit_all_notes_in_phrase = False
                if self.beat_match.gems[self.current_note_idx + 1].role == 0:
                    self.hit_all_notes_in_phrase = True

            # go to next note
            self.current_note_idx += 1

        self.score_label.text = 'Score:%d\n' % self.score
        self.mult_label.text = 'Multiplier:%d\n' % self.multiplier

    def receive_audio(self, frames, num_channels) :
        # handle 1 or 2 channel input.
        # if input is stereo, mono will pick left or right channel. This is used
        # for input processing that must receive only one channel of audio (RMS, pitch, onset)
        if num_channels == 2:
            mono = frames[self.channel_select::2] # pick left or right channel
        else:
            mono = frames

        # Get the pitch correctly
        self.cur_pitch = self.pitch_detect.write(mono)
        rms = np.sqrt(np.mean(mono ** 2))
        rms = np.clip(rms, 1e-10, 1) # don't want log(0)
        db = 20 * np.log10(rms)      # convert from amplitude to decibels 
        db += 60
        if db < 15:
            self.cur_pitch = 0

        # Deal with scoring
        cur_note = self.gem_data[self.current_note_idx][1]
        role = self.gem_data[self.current_note_idx][2]
        # if role and (cur_note == round(self.cur_pitch) or cur_note + 12 == round(self.cur_pitch) or cur_note + 24 == round(self.cur_pitch)):
        if role: 
            if self.beat_match.gems[self.current_note_idx].on_sing():
                self.score += self.multiplier
                self.fireworks.append(Fireworks(self.beat_match.gems[self.current_note_idx].pos, False, self))
                if self.beat_match.gems[self.current_note_idx + 1].role == 0 and self.hit_all_notes_in_phrase:
                    self.multiplier += 1
                    self.beat_match.ball.update_multiplier(self.multiplier)
                    self.fireworks.append(Fireworks((Window.width * 0.25 - self.beat_match.translate.x, Window.height * 0.06), True, self))


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

        self.paused = True

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
            role = int(tokens[2])
            if pitch < MIN_PITCH or pitch > MAX_PITCH:
                # haven't processed this yet TODO
                pitch = random.randint(MIN_PITCH + 1, MAX_PITCH - 1)
            self.gems.append((time, pitch, role))

        time = 0
        while time < self.gems[-1][0]:
            self.barlines.append(time)
            time += 4 * 60. / TEMPO

    def get_gems(self):
        return self.gems

    def get_barlines(self):
        return self.barlines


# display for a single gem at a position with a color (if desired)
class GemDisplay(InstructionGroup):
    def __init__(self, pos, color, role):
        super(GemDisplay, self).__init__()

        self.role = role
        self.pos = pos

        new_pos = (pos[0] - GEM_SIZE / 2, pos[1] - GEM_SIZE / 2)

        self.border_color = Color(0, 0, 0)
        self.add(self.border_color)

        self.border = Line(rounded_rectangle=(new_pos[0], new_pos[1], GEM_SIZE, GEM_SIZE, 10))
        self.add(self.border)

        self.rect_color = Color(color[0], color[1], color[2], 0.8)
        self.add(self.rect_color)

        self.rect = RoundedRectangle(pos=new_pos, size=(GEM_SIZE, GEM_SIZE))
        self.add(self.rect)

        self.time = 0
        self.was_sung = False

    # change to display this gem being hit by the ball
    def on_hit(self):
        if not self.role:
            self.rect_color.rgb = (0,1,0)

    # change to display this gem being sung correctly
    # returns true if this is first time being sung, false otherwise
    def on_sing(self):
        self.rect_color.a = 1
        self.border_color.a = 1
        self.rect_color.rgb = (0,1,0)
        if not self.was_sung:
            self.was_sung = True
            return True
        return False

    # useful if gem is to animate
    def on_update(self, dt):
        if self.role and not self.was_sung:
            self.time += dt
            if self.time > AUDIO_DELAY:
                self.rect_color.a -= 2 * dt
                self.border_color.a -= 2 * dt
            return self.rect_color.a > 0
        return False


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
        Window.clearcolor = (.7, .7, .7, 1)
        self.add(Color(1, 1, 1, .5))
        self.add(Rectangle(pos=(0,0), size=(Window.width, Window.height), texture=Image('data/background.jpg').texture))
        self.add(Color(1, 1, 1, .8))
        self.add(Rectangle(pos=(0,380), size=(Window.width, Window.height - 300), texture=Image('data/logo.png').texture))


# Displays the arrow that indicates what pitch you're currently singing
class ArrowDisplay(InstructionGroup):
    def __init__(self):
        super(ArrowDisplay, self).__init__()

        height = Window.height / 2

        self.add(Color(0, 0, 0, .5))
        self.image = CRectangle(cpos=(NOW_BAR_POS - GEM_SIZE/2 - 20, height), csize=(40,30), texture=Image('data/arrow.png').texture)
        self.add(self.image)

        self.add(Color(0, 0, 0, .3))    # is black
        self.line = Line(points=(NOW_BAR_POS - GEM_SIZE/2, height, Window.width, height))
        self.add(self.line)

    # displays when you update the pitch of the arrow
    def on_pitch(self, pitch):
        height = pitch_to_height(pitch)
        self.image.set_cpos((NOW_BAR_POS - GEM_SIZE/2 - 20, height))
        self.line.points = (NOW_BAR_POS - GEM_SIZE/2, height, Window.width, height)


# display for a bar line
class BarLineDisplay(InstructionGroup):
    def __init__(self, width):
        super(BarLineDisplay, self).__init__()
        self.add(Color(0,0,0,.2))          # is black
        self.add(Line(points=(width, 0, width, Window.height)))


# display for the now bar
class NowBarDisplay(InstructionGroup):
    def __init__(self):
        super(NowBarDisplay, self).__init__()
        self.add(Color(0,0,0,1))
        self.add(Line(points=(NOW_BAR_POS, 0, NOW_BAR_POS, Window.height), width=3))

# display for the tonic, third, fifth
class PitchBarDisplay(InstructionGroup):
    def __init__(self, pitch, note):
        super(PitchBarDisplay, self).__init__()
        height = pitch_to_height(pitch)
        self.add(Color(0,0,0,.2))
        self.add(Line(points=(0, height, Window.width, height)))
        self.label = Label(font_size="20sp", text_size=(100,100), pos=(10, height - 12), color=(0,0,0,.5), text=note)

    def get_text(self):
        return self.label

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

        # to do with color change
        self.color_time = 0
        self.mult = 1

    def pitch_to_ball_height(self, pitch):
        return pitch_to_height(pitch) + GEM_SIZE

    def update_multiplier(self, mult):
        self.mult = mult

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

        if self.idx == 0 or self.idx >= len(self.gem_data):
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

        # color for multiplier stuff
        if self.mult > 1:
            x = 60. / TEMPO * clip(10 - self.mult, 1, 10)
            self.color_time = (self.color_time + dt / x) % 3
            r = clip(1 - self.color_time if self.color_time < 2 else self.color_time - 2, 0, 1)
            g = clip(1 - abs(self.color_time - 1), 0, 1)
            b = clip(1 - abs(self.color_time - 2), 0, 1)
        else:
            r,g,b = (1,1,1)

        self.ball_color.rgb = (r, g, b)
        self.ball_color.a = 0.5

# Displays and controls all game elements: Nowbar, Buttons, BarLines, Gems.
class BeatMatchDisplay(InstructionGroup):
    def __init__(self, gem_data, barline_data, widget):
        super(BeatMatchDisplay, self).__init__()

        self.gem_data = gem_data
        self.barline_data = barline_data

        # Set up nowbar
        self.add(NowBarDisplay())
        for pitch, note in PITCHES:
            pitchbar = PitchBarDisplay(pitch, note)
            self.add(pitchbar)
            widget.add_widget(pitchbar.get_text())

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
        for time, pitch, role in self.gem_data:
            pos = (NOW_BAR_POS + VELOCITY * time, pitch_to_height(pitch))
            color = (1,1,0)
            if role:
                color = (1,0,1)
            self.gems.append(GemDisplay(pos, color, role))
            self.add(self.gems[-1])
        self.barlines = []
        for time in self.barline_data:
            self.barlines.append(BarLineDisplay(NOW_BAR_POS + VELOCITY * time))
            self.add(self.barlines[-1])

        self.playing = True
        self.needs_update = []

    def add(self, obj):
        super(BeatMatchDisplay, self).add(obj)

    def toggle(self):
        self.playing = (not self.playing)

    # called by Player. Causes the right thing to happen
    def gem_hit(self, gem_idx):
        self.gems[gem_idx].on_hit()
        self.needs_update.append(self.gems[gem_idx])

    # called by Player. Causes the right thing to happen
    def gem_pass(self, gem_idx):
        self.gems[gem_idx].on_pass()

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

class Fireworks(InstructionGroup):
    def __init__(self, pos, is_fast, widget):
        super(Fireworks, self).__init__()
        self.ps = ParticleSystem('data/fireworks.pex')
        self.ps.emitter_x = pos[0]
        self.ps.emitter_y = pos[1]
        self.ps.start()
        self.basewidget = widget
        self.basewidget.add_widget(self.ps)

        if is_fast:
            self.ps.start_color = (1,0,0,1)
            self.ps.end_color = (1,0,0,0)
            self.maxParticles = 200
            self.ps.speed = 150
            self.end_time = 60
        else:
            self.end_time = 30

        self.time = 0

    def on_update(self):
        self.time += 1
        if self.time > self.end_time:
            self.ps.stop()
        if self.time > 120:
            self.basewidget.remove_widget(self.ps)
        return True

run(MainWidget)