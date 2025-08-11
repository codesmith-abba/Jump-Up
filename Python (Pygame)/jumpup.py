from pathlib import Path
import pygame
from random import randrange
import os

from constants import HouseStartEndStr, HouseType
from color_generator import ColorGenerator
from modal import Modal
from player import Player


class JumpUp:
    def __init__(self, bg_color=(240, 240, 240), border_color=(0, 0, 0), cell_bg=(200, 200, 200)):
        self.house_name = None
        self.bg_color = bg_color
        self.border_color = border_color
        self.cell_bg = cell_bg

        # Houses Setup
        self.HOUSES_PATH = Path('houses/')
        self.IMAGES_PATH = Path('static/images/')
        self.HOUSES = {}

        self.load_all_houses(self.HOUSES_PATH)

        # Setup Pygame
        pygame.init()
        self.WIDTH, self.HEIGHT = self.size = 600, 400
        self.screen = pygame.display.set_mode(self.size)
        self.smallFont = pygame.font.SysFont('calibri', 15)
        self.mediumFont = pygame.font.SysFont('Times New Roman', 20)
        self.largeFont = pygame.font.SysFont('Times New Roman', 30)
        pygame.display.set_caption("JumpUp - Let's Bounce!")
        self.clock = pygame.time.Clock()

        # Colors
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0, 0)
        self.BLUE = (0, 0, 255)
        self.GREEN = (0, 255, 0)

        # Game variables
        self.running = True
        self.MODES = ['Single Player (With AI)', 'Multi Player (Select Below)']
        self.PLAYERS = [2, 3, 4]
        self.game_state = 'welcome'
        self.color_gen = ColorGenerator()
        self.player = Player()
        self.modal = Modal()
        self.scroll_y = 0
        self.scroll_x = 0
        self.selected_mode = None
        self.selected_house = None
        self.selected_players = 0
        self.ai_active = False
        self.ai_turn = False
        self.house_selected = False
        self.mode_selected = False
        self.players_selected = False
        self.continue_btn_clicked = False
        self.how_to_clicked = False
        self.radio_btns = []
        self.WON_HOUSES = {}

    def load_house(self, fname: str, path: Path) -> list[str]:
        with open(os.path.join(path, fname), 'r') as f:
            return [line.rstrip("\n") for line in f if line.strip()]

    def load_all_houses(self, path, name_case="lower"):
        """
        Load all house .txt files from a directory into HOUSES dict.
        name_case: "lower", "upper", or None for original casing.
        """
        for fname in os.listdir(path):
            if fname.startswith("."):
                continue  # skip hidden/system files
            
            name, ext = os.path.splitext(fname)
            if ext.lower() != ".txt":
                continue  # skip non-txt files

            # Normalize case
            if name_case == "lower":
                name = name.lower()
            elif name_case == "upper":
                name = name.upper()

            # Load the house into the dictionary
            self.HOUSES[name] = self.load_house(fname, path)

    def is_valid_house(self, house_shape_key):

        if isinstance(house_shape_key, HouseType):
            key = house_shape_key.value
        
        else:
            key = house_shape_key
        
        if key not in self.HOUSES:
            return False
        
        return True

    def get_selected_house(self, house_shape_key):

        if not self.is_valid_house(house_shape_key):
            raise ValueError(f"Unknown House: {house_shape_key}")
        
        return self.HOUSES[house_shape_key]

    def normalize_house_shape_key(self, house_shape_key):
        if isinstance(house_shape_key, HouseType):
            key = house_shape_key.value
        else:
            key = house_shape_key
        
        return key

    def shapes(self, house_shape_key: str | HouseType):
        if not self.is_valid_house(house_shape_key):
            raise ValueError(f"Unknown House: {house_shape_key}")

        # Normalize to string key
        s_key = house_shape_key.name if isinstance(house_shape_key, HouseType) else house_shape_key.upper()

        # Collect all start/end markers for this house
        shape_start_end = []
        for house_s_e in HouseStartEndStr:
            prefixes = house_s_e.name.split("_")
            if s_key in prefixes:
                shape_start_end.append(house_s_e.value)

        # Make sure we have at least start and end
        if len(shape_start_end) < 2:
            raise ValueError(f"No start/end markers found for {s_key}")

        # Pass to extract_each_shape dynamically
        result = self.extract_each_shape(house_shape_key, *shape_start_end)
        return result

    def get_shape_boundary(self, shape):
        """Find the bounding box of the '#' symbols in a shape."""
        top = None
        bottom = None
        left = None
        right = None

        for row_index, row in enumerate(shape):
            if row == ' ##    ##' or row == '##  ##  ##':
                continue
            for col_index, char in enumerate(row):
                if char == "#":
                    if top is None or row_index < top:
                        top = row_index
                    if bottom is None or row_index > bottom:
                        bottom = row_index
                    if left is None or col_index < left:
                        left = col_index
                    if right is None or col_index > right:
                        right = col_index

        if top is None:
            return None  # No '#' found

        width = right - left + 1 if right is not None and left is not None else None
        height = bottom - top + 1 if bottom is not None else None

        return {
            "top": top,
            "bottom": bottom,
            "left": left,
            "right": right,
            "width": width,
            "height": height
        }

    def run(self):
        while self.running:
            self.screen.fill(self.bg_color)
            self.handle_events()
            self.update()
            self.render()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    self.scroll_y = max(0, self.scroll_y - 20)
                elif event.button == 5:  # Scroll down
                    self.scroll_y += 20
                elif event.button == 1:
                    mouse_pos = event.pos
                    if self.game_state == 'welcome':
                        if self.continue_btn.collidepoint(mouse_pos):
                            self.continue_btn_clicked = True
                        elif self.how_to_rect.collidepoint(mouse_pos):
                            self.how_to_clicked = True
                    elif self.game_state == 'choose_house':
                        for hname, rect in self.houses_rect.items():
                            if rect.collidepoint(mouse_pos):
                                self.selected_house = hname
                                self.house_selected = True 
                                break
                    elif self.game_state == 'choose_mode':
                        for mode, mode_rect in self.mode_rects:
                            if mode_rect.collidepoint(mouse_pos):
                                self.selected_mode = mode
                                self.mode_selected = True
                                break
                        for radio_num, radio_btn in self.radio_btns:
                            if radio_btn.collidepoint(mouse_pos):
                                self.selected_players = radio_num
                                self.players_selected = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.house_selected:
                    self.house_selected = True

    def update(self):
        self.color_gen.update_color()
        if self.game_state == 'welcome':
            if self.continue_btn_clicked:
                self.game_state = 'choose_house'
                self.continue_btn_clicked = False
            elif self.how_to_clicked:
                self.game_state = 'how_to'
                self.how_to_clicked = False
        elif self.game_state == 'choose_house':
            if self.house_selected:
                self.game_state = 'choose_mode'
                self.house_selected = False
        elif self.game_state == 'choose_mode':
            if self.mode_selected:
                self.game_mode = 'next_state'
                self.mode_selected = False
            elif self.players_selected:
                pass
                # print(f"Players chosen: {self.selected_players}")

    def render(self):
        if self.game_state == 'welcome':
            self.welcome(self.screen)
        elif self.game_state == 'choose_house':
            self._render_houses(self.screen)
        elif self.game_state == 'how_to':
            pass
        elif self.game_state == 'choose_mode':
            self.modal.open(self.screen, "Choose Mode", self.render_modes)
    
            # self.render_selected_house(self.screen)
    
    def welcome(self, surface):
        # Welcome Bg
        self.put_background(surface, self.IMAGES_PATH / 'welcomeBg.jpg')

        # Draw Title Text
        self.txt_rect = pygame.Rect(self.WIDTH // 2 * .1, self.HEIGHT // 2 * .20, (self.WIDTH // 2), 50)
        self._draw_text(surface=surface, text="Welcome to JumpUp Game", 
                        font=self.largeFont, box_rect=self.txt_rect,
                        color=self.color_gen.get_color()
                        )

        # Continue Button
        self.continue_btn = pygame.Rect(self.WIDTH * .50, self.HEIGHT // 2, 200, 50)
        continue_txt = self.mediumFont.render("Continue", True, self.WHITE)
        continue_txt_rect = continue_txt.get_rect(center=self.continue_btn.center)
        pygame.draw.rect(surface, self.BLUE, self.continue_btn, border_radius=30)
        surface.blit(continue_txt, continue_txt_rect)

        # How to Play Button
        self.how_to_rect = pygame.Rect(self.WIDTH * .85, self.HEIGHT * .95, 100, 20)
        self._draw_text(surface=surface, text="How to Play ?", 
                        font=self.smallFont, box_rect=self.how_to_rect,
                        color=self.RED
                        )

        return None

    def draw_house(self, surface, shape_lines, start_x, start_y, block_size=20, color=(255, 0, 0), margin=2):
        for row_index, row in enumerate(shape_lines):
            for col_index, char in enumerate(row):
                if char == "#":
                    x = start_x + col_index * block_size
                    y = start_y + row_index * block_size
                    pygame.draw.rect(surface, color, ((x + margin),(y + margin), block_size, block_size), 2)

    def _render_houses(self, surface, block_size=10, color=(255, 0, 0), margin=20):
        # Background and title
        self.put_background(surface, self.IMAGES_PATH / 'chooseHouseBg.jpg')
        screen_size = surface.get_size()
        cutout_rect = self._get_cutout_rect(screen_size)
        self._draw_text(surface=surface, 
                                 text= "Choose Your Fav House", 
                                 font=self.mediumFont, box_rect=cutout_rect)

        img_rect = self._get_start_image_rect(screen_size)

        # Set scrollable area
        surface.set_clip(img_rect)

        # Grid setup
        box_width, box_height = 200, 200
        shapes_per_row = img_rect.width * .01 // 2
        total_shapes = len(self.HOUSES)

        max_rows = (total_shapes + shapes_per_row - 1) // shapes_per_row
        total_content_height = max_rows * (box_height + margin)
        max_scroll = max(0, total_content_height - img_rect.height)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))  # clamp scroll

        self.houses_rect = {}

        for i, (hname, hshape) in enumerate(self.HOUSES.items()):
            row = i // shapes_per_row
            col = i % shapes_per_row

            x = img_rect.x + col * (box_width + margin)
            y = img_rect.y + row * (box_height + margin) - self.scroll_y

            # Skip drawing if off-screen (for performance)
            if y + box_height < img_rect.top or y > img_rect.bottom:
                continue

            # Compute house dimensions
            rows = len(hshape)
            cols = max(len(line) for line in hshape)
            max_block_w = box_width // cols
            max_block_h = box_height // rows
            scaled_block_size = min(block_size, max_block_w, max_block_h)

            shape_width = cols * scaled_block_size
            shape_height = rows * scaled_block_size

            shape_x = x + (box_width - shape_width) // 2
            shape_y = y + (box_height - shape_height) // 2

            # Draw background box
            shape_rect = pygame.draw.rect(surface, (40, 40, 40), (x, y, box_width, box_height), border_radius=10)

            # Draw the house inside the box
            self.draw_house(surface, hshape, shape_x, shape_y + 2, scaled_block_size, color)

            self.houses_rect[hname] = shape_rect
        # Reset clipping
        surface.set_clip(None)

    def render_modes(self, surface, body_rect):
        """
        Render the game modes as clickable options within the modal body.
        This function is designed to be used as the 'body' parameter in modal.open()
        
        Args:
            surface: The pygame surface to draw on
            body_rect: The rectangle defining the area for the body content
        """
        # Background for the modes area
        bg = pygame.draw.rect(surface, self.BLUE, body_rect, border_radius=10)
        
        # Calculate positions for each mode
        mode_height = 40
        start_y = body_rect.top + 10
        spacing = 10

        self.mode_rects = []
        
        # Draw each mode as a button-like option
        for i, mode in enumerate(self.MODES):
            y_pos = start_y + i * (mode_height + spacing)
            mode_rect = pygame.Rect(body_rect.left + 20, y_pos, body_rect.width - 40, mode_height)
            
            # Button background
            button_color = (70, 130, 180) if i == 1 else (220, 20, 60)  # Different colors for each mode
            pygame.draw.rect(surface, button_color, mode_rect, border_radius=8)
            
            # Button text
            mode_text = self.mediumFont.render(f"{i+1}. {mode}", True, (255, 255, 255))
            text_rect = mode_text.get_rect(center=mode_rect.center, left=mode_rect.left + 5)
            surface.blit(mode_text, text_rect)

            if self.selected_mode == 'Multi Player (Select Below)':
                self.choose_multi_player_num(surface, mode_rect)
                if self.selected_players:
                    self.draw_start_btn(surface, mode_rect.left, bg.height + mode_rect.height * 2 + 10, mode_rect.width)

            if self.selected_mode == 'Single Player (With AI)':
                self.ai_active = True
                self.draw_start_btn(surface, mode_rect.left, bg.height + mode_rect.height * 2 + 10, mode_rect.width)
            
            # Add visual feedback (hover effect would be handled by modal system)
            pygame.draw.rect(surface, (255, 255, 255), mode_rect, 2, border_radius=8)

            self.mode_rects.append((mode, mode_rect))

    def draw_start_btn(self, surface, start_x, start_y, width, height=40):
        play_btn = pygame.Rect(start_x, start_y, width, height)
        play_txt = self.mediumFont.render("Start Game", True, self.BLUE)
        play_txt_rect = play_txt.get_rect(center=play_btn.center)
        pygame.draw.rect(surface, self.WHITE, play_btn, border_radius=15)
        surface.blit(play_txt, play_txt_rect)

    def choose_multi_player_num(self, surface, rect):
        
        # Radio Btn rect
        start_x = rect.x + 5
        start_y = rect.top + 50
        margin = 50

        for i in range(len(self.PLAYERS)):
            radio_btn = pygame.Rect(start_x, start_y, 20, 20)
            num = self.mediumFont.render(str(self.PLAYERS[i]), True, self.WHITE)
            num_rect = num.get_rect(left=start_x + 22, top=radio_btn.top -2)
            pygame.draw.rect(surface, self.GREEN, radio_btn, 2, 50)
            surface.blit(num, num_rect)

            if self.selected_players == self.PLAYERS[i]:
                pygame.draw.circle(surface, self.WHITE, radio_btn.center, 5)

            start_x += + margin + num_rect.width

            self.radio_btns.append((self.PLAYERS[i], radio_btn))

    def render_selected_house(self, surface, block_size=10, color=(255,255,255)):
        self.put_background(surface, self.IMAGES_PATH / 'playBg.jpg')

        w,h = surface.get_size()

        rect_left = w * .15
        rect_top = h * .2

        house_rect = pygame.Rect(rect_left, rect_top, w -2* rect_left, h - rect_top - rect_top)

        start_x = house_rect.x
        start_y = house_rect.y

        for hname, hsape in self.HOUSES.items():
            if self.selected_house == hname:
                self.draw_house(surface, hsape, start_x, start_y, block_size, self.color_gen.get_color())

    def _get_cutout_rect(self, screen_size):
        width, height = screen_size
        # Approximate cutout size
        margin_w = width * 0.09
        margin_h_top = height * -0.48 # Just to scale with the cutout rect -48%
        margin_h_bottom = height * 0.13
        return pygame.Rect(margin_w, margin_h_top, width - 2 * margin_w, height - margin_h_top - margin_h_bottom)
    
    def _get_start_image_rect(self, screen_size):
        width, height = screen_size
        # Approximate cutout size
        margin_w = width * 0.15
        margin_h_top = height * 0.23 # Just to scale with the cutout rect 23%
        return pygame.Rect(margin_w, margin_h_top, width - 2 * margin_w, height - margin_h_top - margin_h_top)
    
    def _draw_text(self, surface, text, font, box_rect, color=(255, 255, 255)):
        """Draw text centered within a given rect box."""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=box_rect.center)
        surface.blit(text_surface, text_rect)
    
    def put_background(self, surface, bg_img, width=0, height=0, full_screen=True):
        bg_image = pygame.image.load(bg_img).convert()

        if full_screen:
            bg_image = pygame.transform.scale(bg_image, surface.get_size())
        
        else:
            if width <= 0 and height <= 0:
                raise ValueError("Width and Hieght must be > Zero, Or set full_screen=True")

        surface.blit(bg_image, (width, height))
    
    def extract_each_shape(self, house_shape_key, *markars):
        
        if not self.is_valid_house(house_shape_key):
            raise ValueError(f"Unknown House: {house_shape_key}")

        # Reference patterns
        key = house_shape_key.value if isinstance(house_shape_key, HouseType) else house_shape_key
        
        shape_lines = self.HOUSES[key]
        shapes = []

        capturing = False
        current_shape = []

        for line in shape_lines:
            if line in markars[:2]:
                # Start of a new shape
                if current_shape:
                    shapes.append(current_shape)
                    current_shape = []
                capturing = True
                current_shape.append(line)
            elif line in markars[2:]:
                if capturing:
                    current_shape.append(line)
                    shapes.append(current_shape)
                    current_shape = []
                    capturing = False
            elif capturing:
                current_shape.append(line)

        # In case one shape reaches EOF without bottom marker
        if current_shape:
            shapes.append(current_shape)

        # Debug print
        # print(shapes[0])
        # for i, shape in enumerate(shapes):
        #     print(f"\n--- Shape {i+1} ---")
        #     for line in shape:
        #         print(line)

        return shapes

    def actions(self, house_shape_key, thrown_house):
        """
        Returns a set of available shape indexes for the given house type.
        Excludes any index in WON_HOUSES and the current thrown house.
        """
        key = self.normalize_house_shape_key(house_shape_key)
        shapes_ = self.shapes(key)

        return {
            i for i in range(len(shapes_))
            if i not in self.WON_HOUSES and i != thrown_house
        }




