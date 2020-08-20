'''
melody.py

This module contains the definition and relevant helper methods for the Melody
object and it's primary derivative, the Voice object. This module also  contains
the Song object which is used as a container to combine multiple melodies
'''

from instruments import *
from notes import *
import simpleaudio as sa
import wave
import struct


class Melody:
    '''
    Class representing a short musical phrase.
    '''
    # Sample rate in Hz
    sample_rate = 44100

    def __init__(self, num_beats, tempo):
        '''
        args:
            - num_beats (int): number of beats in the melody
            - tempo (float): the tempo of the melody (in beats-per-minute)
        '''
        self.len_beats = num_beats
        self.len_sec = num_beats / tempo * 60

        self.tempo = tempo # In beats per minute
        self.seconds_per_beat = 60 / tempo

        self.samples_per_beat = round(self.sample_rate * self.seconds_per_beat)

        self.voices = []

        self.waveform = np.array([])
        self.time = np.linspace(0, self.len_sec, self.len_sec * self.sample_rate, False)


    def new_voice(self, name, instr=sine):
        '''
        Creates a new Voice for the melody
        '''
        return Voice(self, name, instr)

    def add_voice(self, voice):
        '''
        Adds the voice to the melody
        '''
        self.voices.append(voice)

    def clear_voices(self):
        '''
        Clears the voices currently in the melody
        '''
        self.voices = []

    def pop_voice(self, name):
        '''
        Removes a voice in the melody with given name
        args:
            - name (str): the name of the voice (property) to be removed
        '''
        keep = []
        popped = None
        for voice in self.voices:
            if voice.name == name:
                popped = voice
            else:
                keep.append(voice)
        self.voices = keep
        return popped


    def compile_waveform(self):
        '''
        Generates the waveform for the melody
        '''
        waveform = np.zeros(len(self.time))
        for voice in self.voices:
            voice_wave = voice.compile_waveform()
            waveform = waveform + voice_wave
        self.waveform = waveform
        return waveform

    def play(self):
        '''
        Plays the melody with 16-bit audio
        '''
        waveform = self.compile_waveform()
        audio = waveform * (2**15 - 1) / np.max(np.abs(waveform))
        audio = audio.astype(np.int16)
        play_obj = sa.play_buffer(audio, 1, 2, self.sample_rate)
        play_obj.wait_done()

'''
The Song object
'''
class Song:
    '''
    Class representing a complete song (composed linearly of multiple melodies)
    '''
    # Sample rate in Hz
    sample_rate = 44100

    def __init__(self, melodies):
        '''
        args:
            - melodies (list): a list of Melody objects
        '''
        self.waveforms = []
        self.times = []
        end_of_prev = 0
        for melody in melodies:
            self.waveforms.append(melody.waveform)
            self.times.append(melody.time + end_of_prev)
            end_of_prev = end_of_prev + melody.time[-1] + 1/44100
        self.waveform = np.concatenate(tuple(self.waveforms), axis=None)
        self.time = np.concatenate(tuple(self.times), axis=None)
        self.duration = len(self.waveform) / self.sample_rate
        self.channels = 1
        self.sample_width = 2


    def write_to_wav(self, name):
        '''
        Writes the song to a .wav file

        args:
            - name (str): name of the .wav file as 'name'.wav
        '''
        name = name + '.wav'
        audio = self.waveform * (2**15 - 1) / np.max(np.abs(self.waveform))
        with wave.open(name, 'w') as f:
            f.setnchannels(self.channels)
            f.setsampwidth(self.sample_width)
            f.setframerate(self.sample_rate)
            for sample in audio:
                data = struct.pack('<h', int(sample))
                f.writeframesraw(data)

    def play(self):
        '''
        Plays the song with 16-bit audio
        '''
        audio = self.waveform * (2**15 - 1) / np.max(np.abs(self.waveform))
        audio = audio.astype(np.int16)
        play_obj = sa.play_buffer(audio, 1, 2, self.sample_rate)
        play_obj.wait_done()

'''
The Voice object
'''
class Voice(Melody):
    '''
    Class representing a single string of notes.

    Multiple notes can be added at the same beat position, however it becomes
    difficult to track during progamming of the voice.

    Note: Voice objets should be instantiated from the Melody method add_voice()

    args:
        - parent (Melody): melody object for which the Voice belongs
        - name (str): name of the voice to be referred too
        - instr (function): a periodic (2*pi) function of only phase.
            (see instruments.py)
    '''
    def __init__(self, parent, name, instr=sine):
        # Gets parent melody's tempo parameters
        self.len_beats = parent.len_beats
        self.len_sec = parent.len_sec
        self.tempo = parent.tempo
        self.seconds_per_beat = parent.seconds_per_beat
        self.samples_per_beat = parent.samples_per_beat
        self.time = parent.time

        self.waveform = np.array([])

        # Assign name and instrument
        self.name = name
        self.instr = instr

        self.notes = []

    def compile_waveform(self):
        waveform = np.zeros(len(self.time))
        for note in self.notes:
            note_wave = note.get_waveform()

            start_index = round((note.beat - 1) * self.samples_per_beat)
            end_padding = len(self.time) - len(note_wave) - start_index

            wave_in_cntx = np.pad(note_wave, (start_index, end_padding), 'constant')

            waveform = waveform + wave_in_cntx

        self.waveform = waveform
        return waveform


    def change_instr(self, instr):
        self.instr = instr

    def clear_notes(self):
        self.notes = []

    def pop_note(self, beat):
        keep = []
        popped = []
        for note in self.notes:
            if note.beat == beat:
                popped.append(note)
            else:
                keep.append(note)
        self.notes = keep
        return popped

    '''
    The following methods are used to add notes to the voice, see the relevant objects
    in notes.py for argument details.
    '''
    def add_note(self, beat, length, pitch, volume=1, profile=long_exp):
        self.notes.append(Note(self, beat, length, pitch, volume, profile))

    def add_vib_note(self, beat, length, pitch, volume=1, profile=long_exp,  start=0.5, rate=6, width=80):
        self.notes.append(Vibrato(self, beat, length, pitch, volume,
                                  profile, start, rate, width))

    def add_drop_note(self, beat, length, pitch, volume=1, profile=long_exp, drop_time=1, width=-1200):
        self.notes.append(Fall(self, beat, length, pitch, volume,
                               profile, drop_time, width))

    def add_grc_note(self, beat, length, pitch, grc_note_pitch, volume=1, profile=long_exp):
        self.notes.append(Grace(self, beat, length, pitch, grc_note_pitch, volume, profile))

    '''
    Easier creation of common 16th note rhythms

    Rhythmic figures labeled using Ta-Ka-Di-Mi subdivisions
    '''
    # Two notes
    def add_TaKa(self, beat, length, pitches, volumes=[1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(2)]
        lengths = [0.25, 0.75]
        for i in range(2):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]

    def add_TaDi(self, beat, length, pitches, volumes=[1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(2)]
        lengths = [0.5, 0.5]
        for i in range(2):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]

    def add_TaMi(self, beat, length, pitches, volumes=[1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(2)]
        lengths = [0.75, 0.25]
        for i in range(2):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]

    def add_DiMi(self, beat, length, pitches, volumes=[1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(2)]
        beat = beat + 0.5 * length
        lengths = [0.25, 0.25]
        for i in range(2):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]

    # Three notes
    def add_TaKaDi(self, beat, length, pitches, volumes=[1,1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(3)]
        lengths = [0.25, 0.25, 0.5]
        for i in range(3):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]

    def add_TaDiMi(self, beat, length, pitches, volumes=[1,1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(3)]
        lengths = [0.5, 0.25, 0.25]
        for i in range(3):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]

    def add_TaKaMi(self, beat, length, pitches, volumes=[1,1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(3)]
        lengths = [0.25, 0.5, 0.25]
        for i in range(3):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]

    def add_KaDiMi(self, beat, length, pitches, volumes=[1,1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(3)]
        lengths = [0.25, 0.25, 0.25]
        beat = beat + 0.25*length
        for i in range(3):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]

    # Four sixteenth notes
    def add_TaKaDiMi(self, beat, length, pitches, volumes=[1,1,1,1], profile=long_exp):
        if isinstance(pitches, str):
            pitches = [pitches for i in range(4)]
        lengths = [0.25, 0.25, 0.25, 0.25]
        for i in range(4):
            self.notes.append(Note(self, beat, length*lengths[i], pitches[i], volumes[i], profile))
            beat = beat + length*lengths[i]
