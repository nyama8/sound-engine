'''
instruments.py

This module contains functions that are used to generate the waveforms of
different instruments. Note waveforms consist of both an amplitude and wave
profile.
'''

import numpy as np
from numpy import pi
from scipy import signal

'''
Amplitude profiles

These are functions which take a time vector and the duration (in seconds) of
a note and generate the amplitude profile in the time domain.
'''
def long_exp(time, duration):
    r = 0.9
    wave = np.multiply(time ** 0.3, np.exp(-2 * time/duration))
    mute = np.where(time < r*duration, 1, (1-time/duration)/(1-r))
    wave = np.multiply(wave, mute)
    return wave / np.max(np.abs(wave))

def flat(time, duration):
    r = 0.9
    left = np.where(time > (1-r)*duration/2, 1, 2 * time/duration/(1-r))
    right = np.where(time < r*duration + (1-r)*duration/2, 1, 2*(1-time/duration)/(1-r))
    return np.multiply(left,right)


'''
Instruments

These are functions which take an angular phase vector as its single argument.
The functions are defined to be periodic with periods of 2*pi.

Arbitrary functions can be defined using Fourier series reprsentations or by
specifying a functional form (analytically defined) for the period [0,2*pi)
and using the helper function modulo_2pi() on the argument.
'''
def sine(phase):
    '''
    A sine wave; generally pure and round sounding
    '''
    return np.sin(phase)

def saw(phase):
    '''
    A rising saw wave; very bright and sharp sounding
    '''
    return signal.sawtooth(phase, 0)

def triangle(phase):
    '''
    A triangle wave; brighter sound than sine wave but still round sounding
    '''
    return signal.sawtooth(phase, 0.5)

def square(phase):
    '''
    A square wave; very bright with high harmonics but rounder sound than saw
    '''
    return signal.square(phase)


'''
Periodic waveform helper functions
'''
def modulo_2pi(unbd_phase):
    return np.mod(unbd_phase, 2*pi)