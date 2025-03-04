import numpy as np

# handles all of the mathy bits of turning numbers into soundwaves
fs = 44100                  # sample rate in Hz
inter_note_interval = 0.5   # time between notes
ramp_time = 0.05            # ramp time between note/silence in seconds

#def fs():
#    return fs

def silence(duration):
    return np.zeros(int(duration * fs))

# values to feed into sin to get base frequency waveform for smooth slides
def slide(startFreq, endFreq, duration):
    #startFreq = 80
    #endFreq = 450
    #duration = 3
    #newfs = 44100

    # this gets the relative spacing right, but not the absolute spacing.
    # need to normalize by desired start frequency
    spacing = np.diff(10 ** (np.linspace(np.log10(startFreq), np.log10(endFreq), int(duration * fs) + 1)))

    # normalize start frequency so it'll give the correct startFreq
    desiredSpacing = startFreq * 2 * np.pi / fs
    spacing = desiredSpacing * spacing / spacing[0]

    # for ramps, stay at full volume for the whole duration
    ramp = np.ones_like(spacing)

    return(spacing, ramp)


# values for sin to get steady tone at base frequency
def note(frequency, duration, ramp_on, ramp_off):
    #startFreq = 150
    #duration = 1
    #newfs = 44100
    #rampOn = True
    #rampOff = True

    #TODO: Ensure duration is never shorter than ramp on/off times
    spacing = (2 * np.pi * frequency / fs) * np.ones(int(duration * fs))

    # For stable notes, pass ramping up/down as arguments
    ramp = np.ones_like(spacing)
    if ramp_on:
        ramp[:int(ramp_time * fs)] = (np.cos(np.linspace(np.pi, 0, int(ramp_time * fs))) + 1) / 2
    if ramp_off:
        ramp[-int(ramp_time * fs):] = (np.cos(np.linspace(0, np.pi, int(ramp_time * fs))) + 1) / 2

    return(spacing, ramp)


# turn spacing into soundwave with the formant structre of a trombone
def to_waveform(spacing, ramp):
    formant_amplitude = np.array([
        0.00338228234061383,
        0.00226922129759024,
        0.00871263427834780,
        0.00793701307097099,
        0.00884670768767992,
        0.0141776629957550,
        0.0130699547346117,
        0.00532919247754215,
        0.00281525320614360,
        0.00275592890049937,
        0.00259025915149248,
        0.00195870812579687,
        0.00108603438964854,
        0.00109042043074750,
        0.00112494823472505
    ])

    n_formants = len(formant_amplitude)
    formant_scaling = np.arange(1, n_formants + 1)

    # generate sin wave of soundLength seconds at base frequency
    timepoints = np.cumsum(spacing)
    print(f"timepoints: {len(timepoints)}. ramp: {len(ramp)}")
    all_freq = formant_amplitude[:, np.newaxis] * np.sin(formant_scaling[:, np.newaxis] * timepoints)

    stimulus = np.sum(all_freq, axis=0)
    # ramp = np.ones(len(stimulus))
    # ramp[:int(rampTime * newfs)] = np.linspace(0, 1, int(rampTime * newfs))
    # ramp[-int(rampTime * newfs):] = np.linspace(1, 0, int(rampTime * newfs))
    stimulus = stimulus * ramp

    return(stimulus)


def build_user_song(frequency, duration, slide_dur):
    #frequency = [80, 100, 150, 80]
    #duration = [1, 2, 1, 3]
    #slide_dur = [0, 2, 3, 0]
    allSpacing = []
    allRamps = []
    silence = np.zeros(int(inter_note_interval * fs))

    for i in range(min(len(frequency), len(duration), len(slide_dur))):
        # lead-up to the note
        if i == 0 or slide_dur[i] == 0:  # if no slide
            allSpacing.append(silence)
            allRamps.append(silence)
        else:  # if slide into this note
            spacing, ramp = slide(frequency[i-1], frequency[i], slide_dur[i])
            allSpacing.append(spacing)
            allRamps.append(ramp)
    
        # the note itself
        if frequency[i] == 0: # if the note is silence
            spacing = silence(duration[i])
            ramp = spacing
        else: # if the note is an actual note
            ramp_on = slide_dur[i] == 0 # ramp on only if you don't slide into current note
            ramp_off = i >= len(slide_dur) - 1 or slide_dur[i + 1] == 0 # ramp off only if last note, or if next note is not a slide
            spacing, ramp = note(frequency[i], duration[i], ramp_on, ramp_off)
        allSpacing.append(spacing)
        allRamps.append(ramp)

    # add brief silence to the end
    allSpacing.append(silence)
    allRamps.append(silence)

    # concatenate all spacings and ramps
    catSpacing = np.concatenate(allSpacing)
    catRamp = np.concatenate(allRamps)

    # turn base frequency and ramps to waveform
    stimulus = to_waveform(catSpacing, catRamp)

    return stimulus












"""
def wf(base_frequency, sound_duration):
    # base_frequency = Hz
    # sound_duration = seconds
    # ramp_time = seconds (ramp ~50 ms)
    # fs = sampling rate in Hz
    formant_amplitude = np.array([
        0.00338228234061383,
        0.00226922129759024,
        0.00871263427834780,
        0.00793701307097099,
        0.00884670768767992,
        0.0141776629957550,
        0.0130699547346117,
        0.00532919247754215,
        0.00281525320614360,
        0.00275592890049937,
        0.00259025915149248,
        0.00195870812579687,
        0.00108603438964854,
        0.00109042043074750,
        0.00112494823472505
    ])

    n_formants = len(formant_amplitude)
    formant_frequency = base_frequency * np.arange(1, n_formants + 1)

    # generate sin wave of sound_duration seconds at base frequency
    timepoints = np.arange(1/fs, sound_duration + 1/fs, 1/fs)
    all_freq = formant_amplitude[:, np.newaxis] * np.sin(formant_frequency[:, np.newaxis] * timepoints * 2 * np.pi)

    stimulus = np.sum(all_freq, axis=0)
    ramp = np.ones(len(stimulus))
    ramp[:int(ramp_time * fs)] = np.linspace(0, 1, int(ramp_time * fs))
    ramp[-int(ramp_time * fs):] = np.linspace(1, 0, int(ramp_time * fs))
    stimulus *= ramp


    
    return stimulus
"""