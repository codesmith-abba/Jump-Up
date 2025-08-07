class Diamond:
    def __init__(self, start_x, start_y):
        self.x = start_x
        self.y = start_y
        self.vx = 0
        self.vy = 0
        self.gravity = 0.5
        self.bounce_factor = 0.6
        self.radius = 5
        self.active = False

    def throw(self, angle, speed):
        import math
        self.vx = speed * math.cos(angle)
        self.vy = -speed * math.sin(angle)  # Negative to go upward
        self.active = True

    def update(self, ground_y, left_x=0, right_x=800):
        if not self.active:
            return

        # Apply gravity
        self.vy += self.gravity

        # Move diamond
        self.x += self.vx
        self.y += self.vy

        # Bounce off ground
        if self.y + self.radius >= ground_y:
            self.y = ground_y - self.radius
            self.vy = -self.vy * self.bounce_factor
            # Stop if bounce is too small
            if abs(self.vy) < 1:
                self.active = False

        # Bounce off left/right walls
        if self.x - self.radius <= left_x or self.x + self.radius >= right_x:
            self.vx = -self.vx * self.bounce_factor

diamond = Diamond(100, 300)  # start position
diamond.throw(angle=0.8, speed=12)

while diamond.active:
    diamond.update(ground_y=350)
    print(f"Diamond at ({diamond.x:.1f}, {diamond.y:.1f})")
