import numpy as np
from numpy import pi

'''
FM Signal helper functions
'''
def integrate(signal, time, dt):
    integral = [0]
    s = 0
    for i in range(len(time)-1):
        ds = signal[i+1] * dt
        s = s + ds
        integral.append(s)
    return np.array(integral)

def fm_modulator(instr, carrier_freq, time, sample_rate, mod_signal, mod_amp=1):
    return instr( 2* pi * (carrier_freq * time + mod_amp * integrate(mod_signal, time, 1/sample_rate)) )

def delay_time(delay, total_duration, sample_rate):
    signal_start = delay * total_duration
    signal_duration = (1 - delay) * total_duration

    signal_time = np.linspace(0, signal_duration, round(signal_duration * sample_rate), False)
    start_index = round(signal_start * sample_rate)
    return np.pad(signal_time, (start_index, 0), 'constant')


'''
Frequency modulation profiles
'''

def const_mod(time, val=0):
    return np.zeros(len(time)) + val


def linear_ramp_mod(time, start_time, duration, end_value=1):
    '''
    Creates piecewise-linear interpolation between 0 and [end_value] in [duration] time
    '''
    mask_bot = np.where(time > start_time , 1, 0)
    mask_top = np.where(time <= start_time + duration , 1, 0)
    mask = np.multiply(mask_bot, mask_top)
    ramp = (end_value / duration) * ( time - start_time )

    return np.where(time > start_time + duration, end_value, 0) + np.multiply(mask, ramp)


def vibrato_mod(time, freq):
    return np.sin(2 * pi * freq * time)



'''
For amplitude control
'''

def freq_rel_amp(carrier_freq, width):
    '''
    Carrier frequency in Hz, width is in cents.
    '''
    return carrier_freq * (2 ** (width / 1200) - 1)