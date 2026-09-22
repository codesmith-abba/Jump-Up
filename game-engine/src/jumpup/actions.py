"""Explicit actions accepted by the authoritative Jump-Up engine."""

from dataclasses import dataclass
from enum import Enum

from .geometry import Point


class GameActionType(str, Enum):
    START_GAME = "start_game"
    BEGIN_TURN = "begin_turn"
    THROW = "throw"
    RESOLVE_THROW = "resolve_throw"
    BEGIN_HOPPING_OUT = "begin_hopping_out"
    HOP = "hop"
    BEGIN_HOPPING_BACK = "begin_hopping_back"
    PICKUP_STONE = "pickup_stone"
    COMPLETE_HOUSE = "complete_house"
    SELECT_CLAIM = "select_claim"
    RESOLVE_CLAIM = "resolve_claim"
    NEXT_HOUSE = "next_house"
    END_TURN = "end_turn"
    NEXT_PLAYER = "next_player"
    END_GAME = "end_game"


@dataclass(frozen=True)
class GameAction:
    type: GameActionType
    player_id: str | None = None
    house_id: str | None = None
    selection_mode: str | None = None
    success: bool | None = None
    failure_reason: str | None = None
    position: Point | None = None
    feet: int = 1
    movement_path: tuple[str, ...] | None = None

    @classmethod
    def start_game(cls) -> "GameAction":
        return cls(GameActionType.START_GAME)

    @classmethod
    def begin_turn(cls, player_id: str) -> "GameAction":
        return cls(GameActionType.BEGIN_TURN, player_id=player_id)

    @classmethod
    def throw(cls, house_id: str) -> "GameAction":
        return cls(GameActionType.THROW, house_id=house_id)

    @classmethod
    def resolve_throw(cls, success: bool, failure_reason: str | None = None) -> "GameAction":
        return cls(GameActionType.RESOLVE_THROW, success=success, failure_reason=failure_reason)

    @classmethod
    def begin_hopping_out(cls, movement_path: tuple[str, ...]) -> "GameAction":
        return cls(GameActionType.BEGIN_HOPPING_OUT, movement_path=movement_path)

    @classmethod
    def hop(cls, house_id: str, position: Point, feet: int = 1) -> "GameAction":
        return cls(
            GameActionType.HOP,
            house_id=house_id,
            position=position,
            feet=feet,
        )

    @classmethod
    def begin_hopping_back(cls) -> "GameAction":
        return cls(GameActionType.BEGIN_HOPPING_BACK)

    @classmethod
    def pickup_stone(cls) -> "GameAction":
        return cls(GameActionType.PICKUP_STONE)

    @classmethod
    def complete_house(cls) -> "GameAction":
        return cls(GameActionType.COMPLETE_HOUSE)

    @classmethod
    def select_claim(cls, house_id: str, selection_mode: str) -> "GameAction":
        return cls(GameActionType.SELECT_CLAIM, house_id=house_id, selection_mode=selection_mode)

    @classmethod
    def resolve_claim(cls, success: bool) -> "GameAction":
        return cls(GameActionType.RESOLVE_CLAIM, success=success)

    @classmethod
    def next_house(cls) -> "GameAction":
        return cls(GameActionType.NEXT_HOUSE)

    @classmethod
    def end_turn(cls) -> "GameAction":
        return cls(GameActionType.END_TURN)

    @classmethod
    def next_player(cls) -> "GameAction":
        return cls(GameActionType.NEXT_PLAYER)

    @classmethod
    def end_game(cls, player_id: str | None = None) -> "GameAction":
        return cls(GameActionType.END_GAME, player_id=player_id)
