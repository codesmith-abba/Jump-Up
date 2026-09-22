"""Authoritative, UI-independent Jump-Up game state package."""

from .actions import GameAction, GameActionType
from .geometry import Bounds, HouseGeometry, Point
from .layouts import LayoutDataError, load_legacy_layout, load_repository_layouts
from .physics import PhysicsConfig, StoneInitialState, StonePhysicsState, ThrowResult, ThrowStatus, simulate_throw
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
    "Bounds",
    "ClaimState",
    "GameAction",
    "GameActionType",
    "GameConfig",
    "GamePhase",
    "GameState",
    "House",
    "HouseGeometry",
    "InvalidTransitionError",
    "Layout",
    "LayoutDataError",
    "LayoutType",
    "Player",
    "Point",
    "PhysicsConfig",
    "RoundState",
    "Stone",
    "StoneInitialState",
    "StonePhysicsState",
    "ThrowResult",
    "ThrowStatus",
    "TransitionResult",
    "TurnState",
    "WinnerState",
    "load_legacy_layout",
    "load_repository_layouts",
    "simulate_throw",
    "transition",
]
