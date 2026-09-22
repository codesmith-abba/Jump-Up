"""Authoritative, UI-independent Jump-Up game state package."""

from .actions import GameAction, GameActionType
from .model import (
    ClaimState,
    GameConfig,
    GamePhase,
    GameState,
    House,
    Layout,
    LayoutType,
    Player,
    RoundState,
    Stone,
    TurnState,
    WinnerState,
)
from .transition import InvalidTransitionError, TransitionResult, transition

__all__ = [
    "ClaimState", "GameAction", "GameActionType", "GameConfig", "GamePhase",
    "GameState", "House", "InvalidTransitionError", "Layout", "LayoutType",
    "Player", "RoundState", "Stone", "TransitionResult", "TurnState", "WinnerState",
]
