import params, time
import numpy as np
from simplesine import dialValues

class Note:
    def __init__(self, freq):
        self.start = time.time()
        self.freq = freq
        self.phase = 0
        self.released = False
        self.releaseStart = None
        self.volumeAtReleaseStart = 0
        self.dead = False
        self.prevAmplitude = 0
        self.amp = 0

    def getAmp(self, startVolume, endVolume, ratio):
        self.amp = startVolume + ((endVolume - startVolume) * ratio**params.ratioCurve)
        return self.amp

    def envelope(self, t) -> float:
        #assert all([attack, decay, release]) # remove later
        attack = dialValues['attack']['curr']
        decay = dialValues['decay']['curr']
        sustain = dialValues['sustain']['curr']
        release = dialValues['release']['curr']

        ''' Returns correct amplitude of note based on time in envelope '''
        lifetime = t - self.start
        if not self.released:
            # attack phase
            if lifetime < attack:
                #print("attack", lifetime)
                ratio = lifetime / attack
                return self.getAmp(0, params.defaultMaxVolume, ratio)
            # decay phase
            elif lifetime < (attack + decay):
                #print("decay", lifetime)
                ratio = (lifetime - attack) / decay
                return self.getAmp(params.defaultMaxVolume, sustain, ratio)
            # sustain phase
            else:
                #print("sustain", lifetime)
                self.amp = sustain
                return sustain
        # release phase
        else:
            #print(f'in release: {self.amp=}')
            if not self.releaseStart:
                self.releaseStart = lifetime
                self.volumeAtReleaseStart = self.amp
                #print(f'set volume at release start to {self.volumeAtReleaseStart}')

            ratio = (lifetime - self.releaseStart) / release
            if ratio > 1:
                self.dead = True
                #print("note dead", lifetime)
                return 0
            

            return self.getAmp(self.volumeAtReleaseStart, 0, ratio)

    def generate(self, frames, startTimeOfBlock):

        timesBySample = startTimeOfBlock + np.arange(frames) / params.samplerate #startTimeOfBlock + np.arange(frames) / sampleRate


        amplitudes = np.array([self.envelope(t) for t in timesBySample])

        # smooth amplitudes between each bus of frames
        amplitudes = np.linspace(self.prevAmplitude, amplitudes[-1], frames)
        self.prevAmplitude = amplitudes[-1]

        phaseIncrement = 2 * np.pi * self.freq / params.samplerate # radians per sample travelled
        phases = np.arange(frames) * phaseIncrement + self.phase
        signal = amplitudes * np.sin(phases)

        self.phase = (self.phase + frames * phaseIncrement) % (2 * np.pi)

        return signal