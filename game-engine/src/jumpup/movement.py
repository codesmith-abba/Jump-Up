"""Authoritative logical player movement and hopping rules for Jump-Up."""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .geometry import Point
from .physics import point_inside_strict, point_on_boundary

if TYPE_CHECKING:
    from .model import Layout


class MovementDirection(str, Enum):
    OUTBOUND = "outbound"
    RETURN = "return"


class MovementMode(str, Enum):
    HOPPING = "hopping"
    RESTING = "resting"


class MovementValidationError(ValueError):
    """Raised when a player movement violates an established game rule."""


@dataclass(frozen=True)
class MovementState:
    """Logical movement snapshot; it contains no animation state."""

    direction: MovementDirection
    mode: MovementMode
    one_leg: bool
    current_house_id: str | None
    position: Point | None
    target_house_id: str
    required_outbound_house_ids: tuple[str, ...]
    visited_house_ids: tuple[str, ...] = ()

    @property
    def hopping(self) -> bool:
        return self.mode is MovementMode.HOPPING

    @property
    def both_feet(self) -> bool:
        return self.mode is MovementMode.RESTING

    @property
    def return_house_ids(self) -> tuple[str, ...]:
        return tuple(reversed(self.required_outbound_house_ids)) + (self.target_house_id,)


def validate_movement_path(
    layout: "Layout",
    target_house_id: str,
    required_outbound_house_ids: tuple[str, ...],
) -> None:
    """Validate an explicit layout-specific movement path without inventing one."""
    if not layout.contains(target_house_id):
        raise MovementValidationError("target house does not exist in layout")
    if target_house_id in required_outbound_house_ids:
        raise MovementValidationError("outbound movement must skip the stone house")
    if len(set(required_outbound_house_ids)) != len(required_outbound_house_ids):
        raise MovementValidationError("movement path cannot contain duplicate houses")
    if any(not layout.contains(house_id) for house_id in required_outbound_house_ids):
        raise MovementValidationError("movement path contains an unknown house")


def begin_hopping(
    layout: "Layout",
    target_house_id: str,
    required_outbound_house_ids: tuple[str, ...],
) -> MovementState:
    """Start one-leg hopping from an explicitly supplied layout-specific path."""
    validate_movement_path(layout, target_house_id, required_outbound_house_ids)
    return MovementState(
        direction=MovementDirection.OUTBOUND,
        mode=MovementMode.HOPPING,
        one_leg=True,
        current_house_id=None,
        position=None,
        target_house_id=target_house_id,
        required_outbound_house_ids=required_outbound_house_ids,
    )


def _next_expected_house(state: MovementState) -> str | None:
    sequence = (
        state.required_outbound_house_ids
        if state.direction is MovementDirection.OUTBOUND
        else state.return_house_ids
    )
    if not sequence:
        return None
    if state.current_house_id is None:
        return sequence[0]
    try:
        index = sequence.index(state.current_house_id)
    except ValueError as exc:
        raise MovementValidationError("current house is not valid for movement direction") from exc
    return sequence[index + 1] if index + 1 < len(sequence) else None


def _validate_destination(layout: "Layout", house_id: str, position: Point) -> None:
    if not layout.contains(house_id):
        raise MovementValidationError("destination house does not exist")
    house = next(house for house in layout.houses if house.id == house_id)
    if point_on_boundary(position, house.geometry):
        raise MovementValidationError("player touched a house boundary")
    if not point_inside_strict(position, house.geometry):
        raise MovementValidationError("player position is outside the destination house")


def hop(
    state: MovementState,
    layout: "Layout",
    destination_house_id: str,
    position: Point,
    *,
    feet: int = 1,
    ownership: dict[str, str] | None = None,
    player_id: str | None = None,
) -> MovementState:
    """Validate and apply one logical hop/landing."""
    if state.mode not in (MovementMode.HOPPING, MovementMode.RESTING):
        raise MovementValidationError("player is not currently moving")
    if feet not in (1, 2):
        raise MovementValidationError("feet must be either 1 or 2")
    if feet == 2 and (ownership or {}).get(destination_house_id) != player_id:
        raise MovementValidationError("both feet are only permitted in an owned house")

    expected = _next_expected_house(state)
    if expected is None:
        raise MovementValidationError("no further house is required in this movement direction")
    if destination_house_id != expected:
        raise MovementValidationError(
            f"invalid movement: expected house {expected}, got {destination_house_id}"
        )

    _validate_destination(layout, destination_house_id, position)

    visited = state.visited_house_ids + (destination_house_id,)
    return MovementState(
        direction=state.direction,
        mode=MovementMode.RESTING if feet == 2 else MovementMode.HOPPING,
        one_leg=feet == 1,
        current_house_id=destination_house_id,
        position=position,
        target_house_id=state.target_house_id,
        required_outbound_house_ids=state.required_outbound_house_ids,
        visited_house_ids=visited,
    )


def begin_return(state: MovementState) -> MovementState:
    """Switch from completed outbound traversal to the explicit return traversal."""
    if state.direction is not MovementDirection.OUTBOUND:
        raise MovementValidationError("player is not in outbound movement")
    required = state.required_outbound_house_ids
    if required and state.current_house_id != required[-1]:
        raise MovementValidationError("outbound movement is not complete")
    return MovementState(
        direction=MovementDirection.RETURN,
        mode=MovementMode.HOPPING,
        one_leg=True,
        current_house_id=state.current_house_id if required else None,
        position=state.position if required else None,
        target_house_id=state.target_house_id,
        required_outbound_house_ids=required,
        visited_house_ids=state.visited_house_ids,
    )


def can_pickup_stone(state: MovementState) -> bool:
    """Return whether the player is legally positioned to retrieve the stone."""
    return (
        state.direction is MovementDirection.RETURN
        and state.hopping
        and state.one_leg
        and state.current_house_id == state.target_house_id
    )
