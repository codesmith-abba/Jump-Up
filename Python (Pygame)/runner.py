from jumpup import JumpUp
# pygame.init()

# # Screen setup
# WIDTH, HEIGHT = 600, 400
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
# clock = pygame.time.Clock()

# # Ball setup
# x, y = 100, 100
# dy = 0
# dx = 0
# gravity = 0.4
# bounce = 0.75
# radius = 20
# ground = HEIGHT - radius

# # Main loop
# running = True
# while running:
#     screen.fill((240, 240, 240))  # Light background

#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False

#     # Apply gravity
#     dy += gravity
#     y += dy

#     # Bounce when hitting the ground
#     if y > ground:
#         y = ground
#         dy = -dy * bounce

#         # Stop bouncing when very small
#         if abs(dy) < 1:
#             dy = 0

#     # Draw the ball (like a diamond)
#     pygame.draw.polygon(screen, (0, 120, 255), [
#         (x, y - radius),  # Top
#         (x + radius, y),  # Right
#         (x, y + radius),  # Bottom
#         (x - radius, y)   # Left
#     ])

#     pygame.display.flip()
#     clock.tick(60)

# pygame.quit()
if __name__ == "__main__":
    game = JumpUp()
    game.run()

# import pygame

# pygame.init()
# screen = pygame.display.set_mode((600, 400))
# clock = pygame.time.Clock()

# class Person:
#     def __init__(self, x, y):
#         self.x = x
#         self.y = y
#         self.state = "idle"
#         self.states = ["idle", "throw", "pick", "raise_leg", "clap"]
#         self.state_index = 0
#         self.frame_counter = 0

#     def set_state(self, state):
#         if state in self.states:
#             self.state = state

#     def draw(self, surface):
#         # Body
#         pygame.draw.circle(surface, (255, 224, 189), (self.x, self.y - 40), 20)  # head
#         pygame.draw.line(surface, (0, 0, 0), (self.x, self.y - 20), (self.x, self.y + 40), 4)  # body

#         if self.state == "idle":
#             # Arms down, smile
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y - 10), (self.x - 20, self.y + 10), 3)
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y - 10), (self.x + 20, self.y + 10), 3)
#             pygame.draw.arc(surface, (0, 0, 0), (self.x - 10, self.y - 50, 20, 10), 0, 3.14, 2)

#         elif self.state == "throw":
#             # One arm up, one forward
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y - 10), (self.x - 20, self.y - 30), 3)
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y - 10), (self.x + 25, self.y), 3)

#         elif self.state == "pick":
#             # Both arms down (picking)
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y + 10), (self.x - 15, self.y + 40), 3)
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y + 10), (self.x + 15, self.y + 40), 3)

#         elif self.state == "raise_leg":
#             # One leg up
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y + 40), (self.x - 20, self.y + 60), 3)
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y + 40), (self.x + 10, self.y + 20), 3)  # raised

#         elif self.state == "clap":
#             # Arms together in front
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y - 10), (self.x - 10, self.y + 10), 3)
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y - 10), (self.x + 10, self.y + 10), 3)
#             pygame.draw.circle(surface, (255, 0, 0), (self.x, self.y + 10), 5)  # hands touching

#         # Legs (default unless overridden)
#         if self.state != "raise_leg":
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y + 40), (self.x - 20, self.y + 60), 3)
#             pygame.draw.line(surface, (0, 0, 0), (self.x, self.y + 40), (self.x + 20, self.y + 60), 3)

#     def next_state(self):
#         self.state_index = (self.state_index + 1) % len(self.states)
#         self.set_state(self.states[self.state_index])


# person = Person(300, 200)
# running = True

# while running:
#     screen.fill((200, 220, 255))

#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False
#         # Press SPACE to change pose
#         if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
#             person.next_state()

#     person.draw(screen)
#     pygame.display.flip()
#     clock.tick(30)

# pygame.quit()





