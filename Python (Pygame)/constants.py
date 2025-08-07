from enum import Enum


class HouseType(Enum):
    HEART = 'heart'
    SQUARE = 'square'

class HouseStartEndStr(Enum):
    # Heart
    HEART_TOP = ' ##    ##'
    HEART_TOP_ALT = '##  ##  ##'
    HEART_BOTTOM = '  #    #'
    HEART_BOTTOM_ALT =  '    ##'

    # Square
    SQUARE_TOP =  '            ########'
    SQUARE_TOP_ALT = '    ########################'
    SQUARE_BOTTOM = '            ########'
    SQUARE_BOTTOM_ALT = '    ########################'
