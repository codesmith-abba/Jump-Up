"""Authoritative serializable domain state for Jump-Up.

This module deliberately models state only. Geometry, physics, and complete
rule resolution are introduced by later engine phases.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LayoutType(str, Enum):
    HEART = "heart"
    SQUARE = "square"
    RECTANGLE = "rectangle"


class GamePhase(str, Enum):
    SETUP = "setup"
    TURN_START = "turn_start"
    THROW = "throw"
    THROW_RESOLUTION = "throw_resolution"
    HOPPING_OUT = "hopping_out"
    HOPPING_BACK = "hopping_back"
    STONE_PICKUP = "stone_pickup"
    HOUSE_COMPLETED = "house_completed"
    CLAIM_SELECTION = "claim_selection"
    CLAIM_RESOLUTION = "claim_resolution"
    NEXT_HOUSE = "next_house"
    TURN_END = "turn_end"
    NEXT_PLAYER = "next_player"
    GAME_OVER = "game_over"


@dataclass(frozen=True)
class House:
    id: str
    number: int
    sequence_index: int

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("house id must not be empty")
        if self.number < 1:
            raise ValueError("house number must be positive")
        if self.sequence_index < 0:
            raise ValueError("house sequence_index must be non-negative")


@dataclass(frozen=True)
class Layout:
    id: str
    type: LayoutType
    houses: tuple[House, ...]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("layout id must not be empty")
        if not self.houses:
            raise ValueError("layout must contain at least one house")
        indexes = [house.sequence_index for house in self.houses]
        if indexes != list(range(len(self.houses))):
            raise ValueError("house sequence_index values must be contiguous and ordered")
        numbers = [house.number for house in self.houses]
        if numbers != list(range(1, len(self.houses) + 1)):
            raise ValueError("house numbers must be sequential starting at 1")

    @property
    def first_house_id(self) -> str:
        return self.houses[0].id

    def contains(self, house_id: str) -> bool:
        return any(house.id == house_id for house in self.houses)

    def next_house_id(self, house_id: str) -> str | None:
        for index, house in enumerate(self.houses):
            if house.id == house_id:
                return self.houses[index + 1].id if index + 1 < len(self.houses) else None
        raise ValueError(f"unknown house id: {house_id}")


@dataclass(frozen=True)
class Stone:
    id: str
    owner_id: str
    location_house_id: str | None = None
    in_hand: bool = True


@dataclass(frozen=True)
class Player:
    id: str
    name: str
    stone_id: str
    order: int

    def __post_init__(self) -> None:
        if not self.id or not self.name or not self.stone_id:
            raise ValueError("player id, name, and stone_id must not be empty")
        if self.order < 0:
            raise ValueError("player order must be non-negative")


@dataclass(frozen=True)
class TurnState:
    player_id: str
    current_house_id: str
    target_house_id: str
    stone_id: str
    completed_house_id: str | None = None
    failed: bool = False
    failure_reason: str | None = None


@dataclass(frozen=True)
class RoundState:
    number: int
    completed_turns: int = 0

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("round number must be positive")
        if self.completed_turns < 0:
            raise ValueError("completed_turns must be non-negative")


@dataclass(frozen=True)
class ClaimState:
    selected_house_id: str | None = None
    selected_player_id: str | None = None
    selection_mode: str | None = None
    resolved: bool = False
    successful: bool | None = None


@dataclass(frozen=True)
class WinnerState:
    player_id: str | None = None
    is_final: bool = False
    tied_player_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GameConfig:
    min_players: int = 2
    max_players: int = 4

    def __post_init__(self) -> None:
        if self.min_players < 1 or self.max_players < self.min_players:
            raise ValueError("invalid player limits")


@dataclass(frozen=True)
class GameState:
    """Complete authoritative snapshot of the game at one deterministic point."""

    layout: Layout
    players: tuple[Player, ...]
    stones: tuple[Stone, ...]
    current_player_id: str | None
    turn: TurnState | None
    round: RoundState
    phase: GamePhase
    ownership: dict[str, str] = field(default_factory=dict)
    claim: ClaimState = field(default_factory=ClaimState)
    winner: WinnerState = field(default_factory=WinnerState)
    config: GameConfig = field(default_factory=GameConfig)

    def __post_init__(self) -> None:
        player_ids = [player.id for player in self.players]
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("player ids must be unique")
        if len(self.players) > self.config.max_players:
            raise ValueError("player count exceeds configured maximum")
        stone_ids = [stone.id for stone in self.stones]
        if len(stone_ids) != len(set(stone_ids)):
            raise ValueError("stone ids must be unique")
        if {stone.owner_id for stone in self.stones} - set(player_ids):
            raise ValueError("every stone owner must be a player")
        if set(self.ownership) - self.layout_ids:
            raise ValueError("ownership contains an unknown house")
        if set(self.ownership.values()) - set(player_ids):
            raise ValueError("ownership contains an unknown player")
        if self.current_player_id is not None and self.current_player_id not in player_ids:
            raise ValueError("current_player_id must reference a player")
        if self.turn is not None:
            if self.turn.player_id not in player_ids:
                raise ValueError("turn player must reference a player")
            if self.turn.current_house_id not in self.layout_ids:
                raise ValueError("turn current house must exist in layout")
            if self.turn.target_house_id not in self.layout_ids:
                raise ValueError("turn target house must exist in layout")
            if self.turn.stone_id not in stone_ids:
                raise ValueError("turn stone must exist")
        if self.claim.selected_house_id is not None and self.claim.selected_house_id not in self.layout_ids:
            raise ValueError("claim house must exist in layout")
        if self.claim.selected_player_id is not None and self.claim.selected_player_id not in player_ids:
            raise ValueError("claim player must exist")

    @property
    def layout_ids(self) -> set[str]:
        return {house.id for house in self.layout.houses}

    @classmethod
    def initial(
        cls,
        layout: Layout,
        players: tuple[Player, ...],
        stones: tuple[Stone, ...],
        config: GameConfig | None = None,
    ) -> "GameState":
        return cls(
            layout=layout,
            players=players,
            stones=stones,
            current_player_id=None,
            turn=None,
            round=RoundState(number=1),
            phase=GamePhase.SETUP,
            config=config or GameConfig(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "layout": {
                "id": self.layout.id,
                "type": self.layout.type.value,
                "houses": [
                    {
                        "id": house.id,
                        "number": house.number,
                        "sequence_index": house.sequence_index,
                    }
                    for house in self.layout.houses
                ],
            },
            "players": [player.__dict__ for player in self.players],
            "stones": [stone.__dict__ for stone in self.stones],
            "current_player_id": self.current_player_id,
            "turn": None if self.turn is None else self.turn.__dict__,
            "round": self.round.__dict__,
            "phase": self.phase.value,
            "ownership": dict(self.ownership),
            "claim": self.claim.__dict__,
            "winner": {
                "player_id": self.winner.player_id,
                "is_final": self.winner.is_final,
                "tied_player_ids": list(self.winner.tied_player_ids),
            },
            "config": self.config.__dict__,
        }
