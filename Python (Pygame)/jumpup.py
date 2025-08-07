from pathlib import Path
import pygame
import os

from constants import HouseStartEndStr, HouseType


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
        self.smallFont = pygame.font.SysFont('calibri', 10)
        self.mediumFont = pygame.font.SysFont('Times New Roman', 20)
        self.largeFont = pygame.font.SysFont('Times New Roman', 30)
        pygame.display.set_caption("JumpUp - Let's Bounce!")
        self.clock = pygame.time.Clock()

        # Colors
        self.WHITE = (255, 255, 255)

        # Game variables
        self.running = True
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

    def update(self):
        # Game logic here (update objects, collisions, etc.)
        pass

    def render(self):
        self._render_houses(self.screen, 10)
    
    def draw_house(self, surface, shape_lines, start_x, start_y, block_size=20, color=(255, 0, 0), margin=1):
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
        self._draw_centered_text(surface, "Choose Your Fav House", cutout_rect)

        img_rect = self._get_start_image_rect(screen_size)

        
        # Each house container is 200x200
        box_width, box_height = 200, 200
        start_x = img_rect.x
        start_y = img_rect.y

        for i, (hname, hshape) in enumerate(self.HOUSES.items()):
            # Compute shape size
            rows = len(hshape)
            cols = max(len(line) for line in hshape)

            # Calculate block_size that fits inside 200x200
            max_block_w = box_width // cols
            max_block_h = box_height // rows
            scaled_block_size = min(block_size, max_block_w, max_block_h)

            # Compute actual size in pixels
            shape_width = cols * scaled_block_size
            shape_height = rows * scaled_block_size

            # Center the house inside the 200x200 box
            box_x = start_x
            box_y = start_y
            shape_x = box_x + (box_width - shape_width) // 2
            shape_y = box_y + (box_height - shape_height) // 2

            # Draw background box
            pygame.draw.rect(surface, (40, 40, 40), (box_x, box_y, box_width, box_height), border_radius=10)

            # Draw the house inside the box
            self.draw_house(surface, hshape, shape_x, shape_y, block_size=scaled_block_size, color=color)

            # Update x for next house
            start_x += box_height + margin

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
    
    def _draw_centered_text(self, surface, text, box_rect, color=(255, 255, 255)):
        """Draw text centered within a given rect box."""
        text_surface = self.mediumFont.render(text, True, color)
        text_rect = text_surface.get_rect(center=box_rect.center)
        surface.blit(text_surface, text_rect)
    
    def put_background(self, surface, bg_img, width=0, height=0, full_screen=True):
        bg_image = pygame.image.load(bg_img).convert()

        if full_screen:
            bg_image = pygame.transform.scale(bg_image, surface.get_size())
        
        else:
            if width == 0 and height == 0:
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
