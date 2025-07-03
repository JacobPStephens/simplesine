import threading, os, time
import tkinter as tk
os.system('xset r off') # disable continuous keyboard presses

KEY_RELEASED = False
def main():
    root = tk.Tk()
    root.title("My tkinter window")
    root.geometry("400x300+100+50")

    root.bind("<KeyPress>", onKeyPressed)
    root.bind("<KeyRelease>", onKeyReleased)

    root.mainloop()

def attack():
    i=0
    while i < 4 and not KEY_RELEASED:
        print(i)
        i += 1
        time.sleep(1)
    print(f"Attack completed. Expected=4 {i=}")

    if not KEY_RELEASED:
        t2.start()

def decay():
    i=10
    while i > 2 and not KEY_RELEASED:
        print(i)
        i -= 1
        time.sleep(1)
    print(f"Decay completed. Expected=2 {i=}")

def sustain():
    print("Starting sustain")
    i = 2
    while i > 0:
        print(i)
        i -= 1
        time.sleep(1)
    print("Sustain completed. At silence")

def onKeyPressed(event):
    print(f'{event.char} pressed')

    #attack()
    t1.start()
    
    #decay()
    #t2.start()



def onKeyReleased(event):
    global KEY_RELEASED
    print(f'{event.keysym} released')
    KEY_RELEASED = True


    sustain()


t1 = threading.Thread(target=attack)
t2 = threading.Thread(target=decay)

main()
os.system('xset r on')