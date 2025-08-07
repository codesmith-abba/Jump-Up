import os
from pathlib import Path
from constants import HouseStartEndStr, HouseType
from player import Player

PLAYER1 = 'X'
PLAYER2 = 'Y'

HOUSES = {}
HOUSES_PATH = Path('houses/')

WON_HOUSES = [1, 4, 2]

def load_house(fname: str, path: Path) -> list[str]:
        with open(os.path.join(path, fname), 'r') as f:
            return [line.rstrip("\n") for line in f if line.strip()]

def load_all_houses(path, name_case="lower"):
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
        HOUSES[name] = load_house(fname, path)

load_all_houses(HOUSES_PATH)

def is_valid_house(house_shape_key):

    if isinstance(house_shape_key, HouseType):
        key = house_shape_key.value
    
    else:
        key = house_shape_key
    
    if key not in HOUSES:
        return False
    
    return True
    
def get_selected_house(house_shape_key):

    if not is_valid_house(house_shape_key):
        raise ValueError(f"Unknown House: {house_shape_key}")
    
    return HOUSES[house_shape_key]

def normalize_house_shape_key(house_shape_key):
    if isinstance(house_shape_key, HouseType):
        key = house_shape_key.value
    else:
        key = house_shape_key
    
    return key

def extract_each_shape(house_shape_key, *markars):
        
        if not is_valid_house(house_shape_key):
            raise ValueError(f"Unknown House: {house_shape_key}")

        # Reference patterns
        key = house_shape_key.value if isinstance(house_shape_key, HouseType) else house_shape_key
        
        shape_lines = HOUSES[key]
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

def shapes(house_shape_key: str | HouseType):
    if not is_valid_house(house_shape_key):
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
    result = extract_each_shape(house_shape_key, *shape_start_end)
    return result

def get_shape_boundary(shape):
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

def terminal(house_shape_key: str):
    """
    Determine if The house is a terminal state
    """
    house = HOUSES[house_shape_key]
    if winner(house_shape_key) is not None:
        return True
    
    return False

def get_players(house_shape_key):
    pass

def player(house_shape_key):
    """
    Determine Which players turn
    """
    if terminal(house_shape_key):
        return None
    
    player = Player()
    next_player = player.next_player()

    return next_player


def actions(house_shape_key, thrown_house):
    """
    Returns a set of available shape indexes for the given house type.
    Excludes any index in WON_HOUSES and the current thrown house.
    """
    key = normalize_house_shape_key(house_shape_key)
    shapes_ = shapes(key)

    return {
        i for i in range(len(shapes_))
        if i not in WON_HOUSES and i != thrown_house
    }

def transition_model(state, action):
    raise NotImplementedError

def check_winner(state):
    raise NotImplementedError

def winner(state):
    raise NotImplementedError


# dy, dx = 5, 10

# if dx < bounds["left"] or dx > bounds["right"] or dy < bounds["top"] or dy > bounds["bottom"]: # type: ignore
#     print("💥 Fail! Diamond is outside the shape boundary.")
# else:
#     print(f"Thrown at {dx} X {dy}")






