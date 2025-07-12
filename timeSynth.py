import numpy as np
import sounddevice as sd
import time
import threading

sample_rate = 44100
blocksize = 512

active_notes = []
lock = threading.Lock()

attack = 0.1
decay = 0.2
sustain_level = 0.5
release = 0.3
max_amplitude = 0.8

NOTE_FREQ = {
    'a': 220.0,
    's': 246.9,
    'd': 261.6,
    'f': 293.7,
    'g': 329.6,
    'h': 349.2,
    'j': 392.0,
}

class Note:
    def __init__(self, freq):
        self.freq = freq
        self.phase = 0
        self.start_time = time.time()
        self.release_start = None
        self.released = False

    def envelope(self, t):
        if self.released:
            if self.release_start is None:
                self.release_start = t
            t_release = t - self.release_start
            if t_release > release:
                return 0
            return sustain_level * (1 - t_release / release)

        t_since_start = t - self.start_time
        if t_since_start < attack:
            return (t_since_start / attack) * max_amplitude
        elif t_since_start < attack + decay:
            decay_time = t_since_start - attack
            return max_amplitude - (decay_time / decay) * (max_amplitude - sustain_level)
        else:
            return sustain_level

    def generate(self, frames, t_start):
        t = (np.arange(frames) + self.phase) / sample_rate
        abs_t = t_start + np.arange(frames) / sample_rate
        amp = np.array([self.envelope(ti) for ti in abs_t])
        signal = amp * np.sin(2 * np.pi * self.freq * t)
        self.phase += frames
        return signal

def audio_callback(outdata, frames, time_info, status):
    if status:
        print(f"Status: {status}")
    
    buffer = np.zeros(frames, dtype=np.float32)
    t_start = time.time()

    with lock:
        for note in active_notes[:]:
            wave = note.generate(frames, t_start)
            buffer += wave

        # Remove notes whose envelope is done
        active_notes[:] = [n for n in active_notes if not (n.released and n.envelope(time.time()) <= 0.001)]

    # Prevent clipping
    buffer = np.clip(buffer, -1.0, 1.0)
    outdata[:] = buffer.reshape(-1, 1)

def play_note(key):
    freq = NOTE_FREQ.get(key)
    if not freq:
        return
    with lock:
        active_notes.append(Note(freq))

def release_note(key):
    with lock:
        for note in active_notes:
            if note.freq == NOTE_FREQ.get(key) and not note.released:
                note.released = True

# 🧪 Test with simple keyboard loop
if __name__ == "__main__":
    import keyboard  # pip install keyboard

    stream = sd.OutputStream(callback=audio_callback,
                             samplerate=sample_rate,
                             blocksize=blocksize,
                             channels=1)
    stream.start()

    print("Press keys (a - j) to play notes, ESC to quit")

    try:
        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == "esc":
                    break
                play_note(event.name)
            elif event.event_type == keyboard.KEY_UP:
                release_note(event.name)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
        stream.close()
