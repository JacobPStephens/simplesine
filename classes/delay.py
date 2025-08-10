import params
import numpy as np
from .effect import Effect

class Delay(Effect):
    def __init__(self, slot):
        self.time = 0.5
        self.feedback = 0
        self.mix = 0.5
        self.delaySamples = int(params.samplerate * self.time)
        self.delayBuffer = np.zeros(self.delaySamples)
        self.delayIdx = 0
        super().__init__("delay", slot)

        super().buildDial(
            name = f"delay{self.slot}Time", 
            centerX = self.topLeftX + params.panelWidth / 3,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = 0,
            maxValue = 2,
            sourceObj = self,
            parameter = "time",
            label="time "
        )
        super().buildDial(
            name = f"delay{self.slot}Feedback", 
            centerX = self.topLeftX + params.panelWidth *2/3,
            centerY = self.topLeftY + params.panelHeight / 8,
            diameter = 30,
            minValue = 0,
            maxValue = 1,
            sourceObj = self,
            parameter = "feedback",
            label="feedback "
        )
        super().createDryWetDial()

    def process(self, signal, frames):
        startReadIdx = (self.delayIdx - self.delaySamples) % self.delaySamples
        endReadIdx  = startReadIdx + frames
        startWriteIdx = self.delayIdx
        endWriteIdx = startWriteIdx + frames

        # read delay signal from past point in buffer
        if endReadIdx <= self.delaySamples:
            # block will fit without wrapping
            delaySignal = self.delayBuffer[startReadIdx:endReadIdx]
        else:
            # will wrap; need to split into 2 parts
            endPart = self.delayBuffer[startReadIdx:]
            samplesFromStart = endReadIdx - self.delaySamples
            startPart = self.delayBuffer[:samplesFromStart]
            delaySignal = np.concatenate((endPart, startPart))

        if len(delaySignal) > frames:
            delaySignal = delaySignal[:frames] # force shape to be the same

        writeSignal = signal + (delaySignal * self.feedback)
        signal = signal + (delaySignal * self.mix)

        # write delay signal to current point in buffer
        if endWriteIdx <= self.delaySamples:
            self.delayBuffer[startWriteIdx:endWriteIdx] = writeSignal.copy()
        else:
            samplesToEnd = self.delaySamples - startWriteIdx
            self.delayBuffer[startWriteIdx:] = writeSignal[:samplesToEnd]
            samplesFromStart = frames - samplesToEnd
            self.delayBuffer[:samplesFromStart] = writeSignal[samplesToEnd:]

        self.delayIdx = endWriteIdx % self.delaySamples
        return signal
    
    def delayTimeChanged(self, updatedTime):
        print(f'in delay time changed... {updatedTime=}')
        self.delaySamples = int(params.samplerate * updatedTime)
        self.delayBuffer = np.zeros(self.delaySamples)
        self.delayIdx = 0