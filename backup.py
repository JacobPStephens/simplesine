import math, threading, os, time
import tkinter as tk
from pysinewave import SineWave

os.system('xset r off')
NOTE_TO_PITCH = {
    'a': -3,
    'a#': -2,
    'bb': -2,
    'b': -1,
    'c': 0,
    'c#': 1,
    'db': 1,
    'd': 2,
    'd#': 3,
    'eb': 3,
    'e': 4,
    'f': 5,
    'f#': 6,
    'gb': 6,
    'g': 7,
    'g#': 8,
    'ab': 8}


def playChord(notes: str):
    print(f'Pressed letter {notes}')

    sinewaves = []
    for note in notes:
        pitch = NOTE_TO_PITCH.get(note, -12) + 12
        wave = SineWave(pitch=pitch, pitch_per_second=10, channels=3)
        sinewaves.append(wave)
        wave.play()

    time.sleep(2)
    for wave in sinewaves:
        wave.stop()



rawAmps = dict()
normalizedAmps = dict()


def main():
    # start
    normalizeThread = threading.Thread(target=normalize)
    normalizeThread.start()

    # update
    while True:
        normalizeThread
        for sine in rawAmps:
            print(sine.sinewave_generator.amplitude)
        #print(rawAmps)
        time.sleep(1)
    

def normalize():

    while True:
        totalRawAmps = sum(rawAmps.values()) + 0.1

        for s in rawAmps:
            if totalRawAmps <= 1:
                normalizedAmps[s] = rawAmps[s]
                
            else:
                normalizedAmps[s] = (rawAmps[s] / totalRawAmps)  

            s.sinewave_generator.amplitude = normalizedAmps[s]
        #print(f'Raw   ={rawAmps.values()}')
        #print(f'Normal={normalizedAmps.values()}')
        time.sleep(0.005)


def fade(sine: SineWave, note: str, startVolume: float, endVolume:float, duration: float, stage: str):
    start = time.time()
    t = 0
    #sine.sinewave_generator.amplitude = startVolume
    #sine.play()

    while t < duration:

        if (stage == "a" or stage == "d") and ((sine, note) not in sines):
            print(f"Exiting {stage} early.")
            return
        #print(amplitudeToDecibels(sine.sinewave_generator.amplitude))
        #print()
        volume = startVolume + ((endVolume - startVolume) * (t / duration))
        rawAmps[sine] = volume
        #print(rawAmps)
        #normalize(sine)
        #sine.sinewave_generator.amplitude = normalizedAmps.get(sine, volume)
        #sine.sinewave_generator.amplitude = volume
        
        # print(f'total amps = {sum(normalizedAmps.values())}')
        # print(f'{rawAmps=}')
            

        #print(f'Volume of note {note} = {volume}')
        t = time.time() - start
        time.sleep(0.01)

    if (stage == "a") and ((sine, note) in sines):
        print("Attack finished. Initiating Decay")
        decayThread = threading.Thread(target=fade, args=[sine, note, maxVolume, sustainVolume, decay, "d"])
        decayThread.start()
    if (stage == "d"):
        print("Decay finished")
    
    if (stage == "r"):
        #print(f'Release completed. At silence.')   
        del rawAmps[sine]
        del normalizedAmps[sine]  
        sine.stop()

    #sine.stop()

    # t = 0         min volume
    # t = d / 4     min + ((max-min)) / 4        =        5  + 2/4       =  5 1/2
    # t = d / 2     min + ((max - min) / 2)      =        5 + ((7-5) /  2) = 6
    # t = d         max volume


sines = []


def playNote(c: str):

    sine = SineWave(pitch=NOTE_TO_PITCH[c], decibels= amplitudeToDecibels(0), decibels_per_second=0)
    sines.append((sine, c))
    attackThread = threading.Thread(target=fade, args=[sine, c, 0, maxVolume, attack, "a"])
    attackThread.start()

    sine.play()



def onKeyPressed(event):

    print(f'{event.char} pressed')
    c = event.char
    if (c not in NOTE_TO_PITCH):
        return
    
    playNote(c)

def onKeyReleased(event):
    # global KEY_RELEASED
    print(f'{event.keysym} released')
    for (sine, c) in sines:
        if c == event.keysym:
            print("Initiating Release.")
            # KEY_RELEASED = True
            currentVolume = sine.sinewave_generator.amplitude
            releaseThread = threading.Thread(target=fade, args=[sine, c, currentVolume, 0, release, "r"])
            releaseThread.start()
            sines.remove((sine, c))


def decibelsToAmplitude(decibels):
    return 2**(decibels / 10)

def amplitudeToDecibels(amplitude):
    if amplitude == 0:
        return 0
    return 20 * math.log(amplitude, 10)



print("executed")
updateThread = threading.Thread(target=main)
updateThread.start()
#print('normalize thread started')

attack = 2
decay = 2
sustainVolume = decibelsToAmplitude(-10)
maxVolume = decibelsToAmplitude(-5)
release = 2
KEY_RELEASED = False

root = tk.Tk()
root.title("My tkinter window")
root.geometry("400x300+100+50")


root.bind("<KeyPress>", onKeyPressed)
root.bind("<KeyRelease>", onKeyReleased)




button1 = tk.Button(root, text="Play", command=playChord)
button1.pack()

root.mainloop()





#main()

os.system('xset r on')