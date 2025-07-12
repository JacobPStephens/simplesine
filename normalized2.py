signals = {

    "note1": [0, 0.5, 1, 0.5, 0, -0.5, 1, -0.5, 0],
    "note2": [0, 0.25, 0.5, 0.25, 0, -0.25, -0.5, -0.25, 0]
}
    # raw : 0, 0.75, 1.5, 0.75, 0, -0.75, -1.5, -0.75, 0
    # ratio: 
rawSignal = [signals["note1"][i] + signals["note2"][i] for i in range(len(signals["note1"]))]
brute = [amp/2 for amp in rawSignal]
print(f'{rawSignal=}')
print(f'{brute=}')


ratio = [0] * len(rawSignal)
for note in signals:
    noteSignal = signals[note]
    maxAmp = max(noteSignal)
    i = 0
    while i < len(noteSignal):
        ratio[i] += (noteSignal[i] / (rawSignal[i] + 1e-9))

        i += 1
        
print(f'{ratio=}')
    



