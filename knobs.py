import tkinter as tk
import os
os.system('xset r off')




class Knobs:
    def __init__(self, arc):
        self.arc = arc
        self.mouse_x: int = 0
        self.mouse_y: int = 0
        self.activeDial: str | None = None
        self.clickOrigin: tuple = None
    
    def mouseMotion(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        
        if not self.activeDial:
            return
        
        difference = self.mouse_y - self.clickOrigin[1]
        difference = max(-50, difference)
        difference = min(50, difference)

        print(f"moved {self.activeDial} by {difference}")
        self.adjustArc(difference)

    def adjustArc(self, difference):

        canvas.itemconfig(attack, extent=((difference - 50) / 100.01) * 360)


    def dialClicked(self, event, stage):
        self.activeDial = "attack"
        self.clickOrigin = (self.mouse_x, self.mouse_y)
        print(f"{stage} dial clicked")

    def mouseReleased(self, event):
        self.activeDial = None
        print("mouse released")



root = tk.Tk()
root.title("simplesine")
root.geometry("800x600+100+50")
canvas = tk.Canvas(root, width=800,height=600, bg="gray")
canvas.pack()
attackBg = canvas.create_oval(49, 49, 101, 101, fill="white", outline="black", width=1.5, tags="attack_tag")
attack = canvas.create_arc(50, 50, 100, 100, fill="lightblue", start= 270, extent=-135)
attackFg = canvas.create_oval(65, 65, 85, 85, fill="black", tags="attack_tag")

knob = Knobs(attack)
root.bind("<Motion>", knob.mouseMotion)
root.bind("<ButtonRelease-1>", knob.mouseReleased)
canvas.tag_bind("attack_tag", "<Button-1>", lambda event: knob.dialClicked(event, "attack"))






root.mainloop()

os.system('xset r on')
