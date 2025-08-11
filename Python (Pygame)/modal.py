import pygame

class Modal:
    def __init__(self):
        self.width = 0
        self.height = 0

        self.ovr_color = (0, 0, 0, 128)
        self.WHITE = (255, 255, 255)
        self.headerFont = pygame.font.SysFont("Times new roman", 20)

    def open(self, surface, title, body, bg_color=(0, 0, 255), actions=None):
        # Overlay
        self.draw_overlay(surface) 

        w, h = surface.get_size()
        start_x = w * 0.2
        start_y = h * 0.2

        # Title height
        title_height = 50

        # Measure body height
        if isinstance(body, str):
            body_font = pygame.font.SysFont("Arial", 16)
            body_txt = body_font.render(body, True, self.WHITE)
            body_height = body_txt.get_height() + 20  # + padding
        elif isinstance(body, pygame.Surface):
            body_height = body.get_height() + 20
        elif callable(body):
            # Callables are tricky — you can pass expected height
            body_height = 200  # default/fallback height
        else:
            body_height = 50  # safety

        # Total height = title + body + padding
        content_height = title_height + body_height + 20  # +20 = top/bottom padding

        # Content Rect (centered vertically based on content)
        content_rect = pygame.Rect(
            start_x,
            start_y,
            w - 2 * start_x,
            content_height
        )
        pygame.draw.rect(surface, bg_color, content_rect, border_radius=20)

        # Title Rect
        title_rect = pygame.Rect(start_x, start_y, w - 2 * start_x, title_height)
        title_txt = self.headerFont.render(title, True, self.WHITE)
        title_txt_rect = title_txt.get_rect(center=title_rect.center, left=title_rect.left + 5)
        pygame.draw.rect(surface, self.WHITE, title_rect, 1, border_radius=20)
        surface.blit(title_txt, title_txt_rect)

        # Body Rect
        body_rect = pygame.Rect(start_x, start_y + title_height, w - 2 * start_x, body_height)

        # Render body
        if isinstance(body, str):
            body_txt_rect = body_txt.get_rect(center=body_rect.center) # type: ignore
            surface.blit(body_txt, body_txt_rect) # type: ignore
        elif isinstance(body, pygame.Surface):
            body_img_rect = body.get_rect(center=body_rect.center)
            surface.blit(body, body_img_rect)
        elif callable(body):
            body(surface, body_rect)

        # Optional: handle actions here if needed


    def update(self):
        """
        Update the modal state and handle user interactions.
        This method should be called in the main game loop when the modal is active.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'close'
                elif event.key == pygame.K_RETURN:
                    return 'confirm'
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Here you could check if buttons were clicked
                    # For now, just return close when clicking outside
                    return 'close'
        
        return None

    def draw_overlay(self, surface, color=(0, 0, 0), alpha=128):
        """
        Draws a semi-transparent overlay on top of the given surface.

        Args:
            surface (pygame.Surface): The surface to draw on (e.g., your game screen).
            color (tuple): RGB color of the overlay (default = black).
            alpha (int): Transparency level (0 = fully transparent, 255 = fully opaque).
        """
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*color, alpha))  # Unpack RGB and add alpha
        surface.blit(overlay, (0, 0))

