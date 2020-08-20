from fmodulation import *
from instruments import *
import simpleaudio as sa

from notes_dict import note_to_freq
from notes_dict import key_to_freq
from notes_dict import note_to_key

'''
notes.py

This module contains the Note module and its derivatives such as the FmNote
which is a frequency modulated note.
'''

class Note:
    '''
    Class representing a single musical note.
    '''
    def __init__(self, voice, beat, length, pitch, volume=1, profile=long_exp):
        '''
        args:
            - voice (Voice): a Voice object that the note belongs to
            - beat (float):the starting beat for the note (uses musical indexing
                notation -- first beat is labeled 1)
            - length (float): the number of beats that the note lasts
            - pitch (str): pitch of the note in scientific notation (A4 = 440 Hz)
                notes are tuned using equal temperment.
            - volume (float): the volume (amplitude) of the note
            - profile (function): a function of a time vector and he duration of the
                note only. See instruments.py module
        '''
        self.sample_rate = voice.sample_rate

        self.instr = voice.instr
        self.beat = beat
        self.length = length # in beats
        self.pitch = pitch
        self.volume = volume
        self.profile = profile

        # Duration in time
        self.duration = voice.seconds_per_beat * length
        self.time = np.linspace(0, self.duration, round(self.duration * self.sample_rate), False)

        self.freq = note_to_freq[pitch]


    def get_waveform(self):
        '''
        Generates the waveform of the note as a numpy array
        '''
        amplitude = self.volume * self.profile(self.time, self.duration)

        ang_freq = 2 * pi * self.freq
        wave = self.instr(ang_freq * self.time)

        return np.multiply(amplitude, wave)

    def play(self):
        '''
        Plays the note using 16-bit audio
        '''
        waveform = self.get_waveform()
        audio = waveform * (2**15 - 1) / np.max(np.abs(waveform))
        audio = audio.astype(np.int16)
        play_obj = sa.play_buffer(audio, 1, 2, self.sample_rate)

        play_obj.wait_done()


class FmNote(Note):
    '''
    Class representing notes with tunable instantaneous frequency
    '''
    def __init__(self, voice, beat, length, pitch, volume=1, profile=long_exp):
        '''
        args:
            - voice (Voice): a Voice object that the note belongs to
            - beat (float):the starting beat for the note (uses musical indexing
                notation -- first beat is labeled 1)
            - length (float): the number of beats that the note lasts
            - pitch (str): pitch of the note in scientific notation (A4 = 440 Hz)
                notes are tuned using equal temperment.
            - volume (float): the volume (amplitude) of the note
            - profile (function): a function of a time vector and he duration of the
                note only. See instruments.py module
        '''
        super().__init__(voice, beat, length, pitch, volume, profile)
        self.mod_signal = const_mod(self.time) # None, these must have max_value = 1
        self.mod_amp = 1

    def get_waveform(self):
        '''
        Generates waveform of the note as an fm signal
        '''
        amplitude = self.volume * self.profile(self.time, self.duration)
        wave = fm_modulator(self.instr, self.freq, self.time, self.sample_rate, self.mod_signal, self.mod_amp)

        return np.multiply(amplitude, wave)


class Vibrato(FmNote):
    '''
    Built in FmNote class for a vibrato
    '''
    def __init__(self, voice, beat, length, pitch, volume=1, profile=long_exp, start=0.5, rate=6, width=80):
        '''
        args (other than inherited from FmNote):
            - start (float): a number in [0,1] indicating the proportional start time of the vibrato
                (eg. start=0.25 -> a vibrato starting after the first quarter of the note's duration)
            - rate (float): the vibrato rate in Hz (must be < 30 Hz to be explicitly perceptible)
            - width (float): the width of the vibrato in cents (relative to the pitch below)
                Common values:
                    - less than 5 cents is imperceptible
                    - 5-60 cents is the range of most instruments
                    - 60-100 cents is an opera soloist
                    - 100 cents is a minor second
                    - 700 cents is a major fifth
                    - 1200 cents is an octave
        '''
        super().__init__(voice, beat, length, pitch, volume, profile)
        mod_time = delay_time(start, self.duration, self.sample_rate)
        self.mod_signal = vibrato_mod(mod_time, rate)
        self.mod_amp = freq_rel_amp(self.freq, width)

class Fall(FmNote):
    '''
    Built in FmNote class for a fall (or rip up)
    '''
    def __init__(self, voice, beat, length, pitch, volume=1, profile=long_exp, drop_time=1, width=-1200):
        '''
        args (other than inherited from FmNote):
            - drop_time (float): time in seconds that the drop will take. If longer than its duration,
                the fall lasts the entire note.
            - width (float): size of the drop in cents:
                Relative values:
                    - 100 cents: minor second
                    - 200 cents: major second
                    - 300 cents: minor third
                    - 400 cents: major third
                    - 500 cents: perfect fourth
                    - 700 cents: perfect fifth
                    - 800 cents: minor sixth
                    - 900 cents: major sixth
                    - 1000 cents: minor seventh
                    - 1100 cents: major seventh
                    - 1200 cents: octave
        '''
        super().__init__(voice, beat, length, pitch, volume, profile)
        if drop_time > self.duration:
            start_time = 0
        else:
            start_time = self.duration - drop_time
        self.mod_signal = linear_ramp_mod(self.time, start_time, drop_time)
        self.mod_amp = freq_rel_amp(self.freq, width)

class Grace(FmNote):
    '''
    Built in FmNote class for a single grace note
    '''
    def __init__(self, voice, beat, length, pitch, grc_note_pitch, volume=1, profile=long_exp):
        '''
        args (other than inherited from FmNote):
            - grc_note_pitch (str): pitch of the grace note in scientific notation
        '''
        super().__init__(voice, beat, length, pitch, volume, profile)
        if self.duration < 1:
            grc_length = 0.125 * self.duration
        else:
            grc_length = 0.125
        self.mod_signal = 1 - linear_ramp_mod(self.time, grc_length, 0.05 * self.duration)
        self.mod_amp = note_to_freq[grc_note_pitch] - note_to_freq[pitch]
