
class UserInput():
    def __init__(self, dials):
        self.mousePoint: tuple[int, int] = None
        self.clickPoint: tuple[int, int] = None
        self.dials = dials
        self.activeDial = None

    def mouseClicked(self, event, stage):
        self.activeDial = self.dials[stage]
        self.clickPoint = self.mousePoint

        return self.activeDial

    def mouseReleased(self, event):
        self.activeDial = None

    def mouseMotion(self, event):
        self.mousePoint = (event.x, event.y)
        if self.activeDial:
            self.dials[self.activeDial.name].update(self.clickPoint, self.mousePoint)
    