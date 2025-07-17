import tkinter as tk
import numpy as np
import sounddevice as sd

import time, os, threading, params, utils
#from midi import midiListener
import Dial
import MouseInfo
#from GUI import GUI 
# 
# # THIS FILE CANNOT IMPORT GUI or MAIN

class SimpleSine:

#import time, threading, os, utils, params
#import Dial, MouseInfo, Note, params

# def main():
#     global lock, stream, activeNotes
#     os.system('xset r off')
    
#     gui = GUI()

#     # builds widgets to GUI and stores them in widgets dict
#     widgets = gui.buildWidgets() # widgets key = name of widget: val = widget obj


#     for tag in allTags:
#         canvas.tag_bind(tag, "<Button-1>", lambda event: HandleInput.mouseClicked(event, tag))


# class HandleInput():
#     def __init__(self, dials):
#         self.mousePoint: tuple[int, int] = None
#         self.clickPoint: tuple[int, int] = None
#         self.dials = dials
#         self.activeComponent = None

#     def mouseClicked(self, event, tagClicked):

#         if tagClicked in ["attack_tag", "decay_tag", "sustain_tag", "release_tag"]:
#             envelopeName = tagClicked[:-4]
#             self.activeComponent = self.dials[envelopeName]

#         self.activeComponent = self.dials[stage]
#         self.clickPoint = self.mousePoint

#         return self.activeDial

#     def mouseReleased(self, event):
#         self.activeDial = None

#     def mouseMotion(self, event):
#         self.mousePoint = (event.x, event.y)
#         if self.activeDial:
#             self.dials[self.activeDial.name].update(self.clickPoint, self.mousePoint)
    






#     dialValues = {
#         'attack': {
#             'curr': params.defaultAttack,
#             'min': params.minAttack,
#             'max': params.maxAttack,
#             'center': 260
#         },
#         'decay': {
#             'curr': params.defaultDecay,
#             'min': params.minDecay,
#             'max': params.maxDecay,
#             'center': 353.33
#         },
#         'sustain': {
#             'curr': params.defaultSustain,
#             'min': params.minSustain,
#             'max': params.maxSustain,
#             'center': 446.66
#         },
#         'release': {
#             'curr': params.defaultRelease,
#             'min': params.minRelease,
#             'max': params.maxRelease,
#             'center': 540
#         }
#     }
#     stream = sd.OutputStream(samplerate=params.samplerate, channels=2, callback=audioCallback, blocksize=params.blocksize)
#     stream.start()
#     activeNotes = []
#     signals = []
#     lock = threading.Lock()

#     blackIDs = [1, 3, 6, 8 ,10, 13, 15, 18, 20, 22]
#     whiteIDs = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24]

#     LOWEST_NOTE = 48

#     buildGUI()


    
#     os.system('xset r on') 






def audioCallback(outdata, frames, time_info, status):
    if status: 
        print(f'{status=}')
    
    if (stream.cpu_load > 0.2):
        print(f'cpu {stream.cpu_load}')
    signal = np.zeros(frames, dtype=np.float32)
    with lock:
        startTime = time.time()
        for note in activeNotes[:]:
            if note.dead:
                activeNotes.remove(note)
                continue
            signal = signal + note.generate(frames, startTime)
            #signal = normalize(signal, note.generate(frames, startTime)) 

    peak = np.max(np.abs(signal)) + 1e-10
    #print(f'rawPeak={peak}')
    if peak > 1:
        targetGain = 1 / peak
    else:
        targetGain = 1     

    if targetGain < params.smoothedGain:
        params.smoothedGain = params.smoothedGain * (1 - params.alphaAttack) + targetGain * params.alphaAttack 
    else:
        params.smoothedGain = params.smoothedGain * (1 - params.alphaRelease) + targetGain * params.alphaRelease 

    #print(f'{targetGain=}')
    signal *= params.smoothedGain * 0.5
    peak = np.max(np.abs(signal))

    
    if peak > 1:
        print(f"clip {peak}")


    outdata[:] = np.repeat(signal.reshape(-1, 1), 2, axis=1)






#print("highlighting note s", noteID)
    
def highlightNote(noteID, msgType):
    
    localID = noteID - LOWEST_NOTE # where note 48 is the lowest element in current 8ve
    if not (0 <= localID <= 25):
        return

    #print(f'{localID=}')
    
    if msgType == "note_on":
        canvas.itemconfig(keysGUI[localID], fill="white")

    elif msgType == "note_off": 

        if localID in whiteIDs:
            canvas.itemconfig(keysGUI[localID], fill=params.primaryToneDark)

        elif localID in blackIDs:
            canvas.itemconfig(keysGUI[localID], fill=params.primaryToneLight)




def notePlayed(globalNoteID):
    with lock:
        freq = utils.NOTE_TO_FREQ[globalNoteID]
        activeNotes.append(Note(freq))
        highlightNote(globalNoteID, "note_on")

def noteReleased(globalNoteID):
    with lock:
        freq = utils.NOTE_TO_FREQ[globalNoteID]
        for note in activeNotes:
            if note.freq == freq and not note.released:
                note.released = True
        highlightNote(globalNoteID, "note_off")

main()
