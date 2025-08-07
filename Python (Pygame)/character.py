class Character:
    def __init__(self, x, y, animations):
        self.x = x; self.y = y
        self.anim = animations
        self.state = "idle"
        self.frame = 0
        self.counter = 0
        self.delay = 8

    def set_state(self, state):
        if state != self.state:
            self.state = state
            self.frame = 0
            self.counter = 0

    def update(self):
        self.counter += 1
        if self.counter >= self.delay:
            self.counter = 0
            self.frame = (self.frame + 1) % len(self.anim[self.state])

    def draw(self, surface):
        frame_surface = self.anim[self.state][self.frame]
        surface.blit(frame_surface, (self.x, self.y))
