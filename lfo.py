class LFO:
    def __init__(self, rate, depth):
        self.rate = rate
        self.depth = depth

    def tick(self):
        