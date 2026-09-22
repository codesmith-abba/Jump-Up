"""Authoritative logical player movement and hopping rules for Jump-Up."""

from dataclasses import dataclass
from enum import Enum

from .geometry import Point
from .model import Layout
from .physics import point_inside_strict, point_on_boundary


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
    visited_house_ids: tuple[str, ...] = ()

    @property
    def hopping(self) -> bool:
        return self.mode is MovementMode.HOPPING

    @property
    def both_feet(self) -> bool:
        return self.mode is MovementMode.RESTING


def outbound_sequence(layout: Layout, target_house_id: str) -> tuple[str, ...]:
    """Return the required outbound houses, excluding the stone house."""
    if not layout.contains(target_house_id):
        raise MovementValidationError("target house does not exist in layout")
    return tuple(
        house.id for house in layout.houses if house.id != target_house_id
    )


def return_sequence(layout: Layout, target_house_id: str) -> tuple[str, ...]:
    """Return the required return houses, ending at the stone house."""
    outbound = outbound_sequence(layout, target_house_id)
    return tuple(reversed(outbound)) + (target_house_id,)


def begin_hopping(layout: Layout, target_house_id: str) -> MovementState:
    """Start the one-leg outbound sequence without inventing a physical start point."""
    if not layout.contains(target_house_id):
        raise MovementValidationError("target house does not exist in layout")
    return MovementState(
        direction=MovementDirection.OUTBOUND,
        mode=MovementMode.HOPPING,
        one_leg=True,
        current_house_id=None,
        position=None,
        target_house_id=target_house_id,
    )


def _next_expected_house(state: MovementState, layout: Layout) -> str | None:
    sequence = (
        outbound_sequence(layout, state.target_house_id)
        if state.direction is MovementDirection.OUTBOUND
        else return_sequence(layout, state.target_house_id)
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


def _validate_destination(
    layout: Layout,
    house_id: str,
    position: Point,
) -> None:
    if not layout.contains(house_id):
        raise MovementValidationError("destination house does not exist")
    house = next(house for house in layout.houses if house.id == house_id)
    if point_on_boundary(position, house.geometry):
        raise MovementValidationError("player touched a house boundary")
    if not point_inside_strict(position, house.geometry):
        raise MovementValidationError("player position is outside the destination house")


def hop(
    state: MovementState,
    layout: Layout,
    destination_house_id: str,
    position: Point,
    *,
    feet: int = 1,
    ownership: dict[str, str] | None = None,
    player_id: str | None = None,
) -> MovementState:
    """Validate and apply one logical hop/landing.

    A normal landing uses one foot. Both feet are permitted only when the
    destination house is owned by the active player. The returned state is
    independent of rendering or animation timing.
    """
    if not state.hopping:
        raise MovementValidationError("player is not currently hopping")
    if feet not in (1, 2):
        raise MovementValidationError("feet must be either 1 or 2")
    if feet == 2 and (ownership or {}).get(destination_house_id) != player_id:
        raise MovementValidationError("both feet are only permitted in an owned house")

    expected = _next_expected_house(state, layout)
    if expected is None:
        raise MovementValidationError("no further house is required in this movement direction")
    if destination_house_id != expected:
        raise MovementValidationError(
            f"invalid movement: expected house {expected}, got {destination_house_id}"
        )
    if state.direction is MovementDirection.OUTBOUND and destination_house_id == state.target_house_id:
        raise MovementValidationError("stone house must be skipped on outbound movement")

    _validate_destination(layout, destination_house_id, position)

    visited = state.visited_house_ids + (destination_house_id,)
    return MovementState(
        direction=state.direction,
        mode=MovementMode.RESTING if feet == 2 else MovementMode.HOPPING,
        one_leg=feet == 1,
        current_house_id=destination_house_id,
        position=position,
        target_house_id=state.target_house_id,
        visited_house_ids=visited,
    )


def begin_return(state: MovementState, layout: Layout) -> MovementState:
    """Switch from the completed outbound traversal to the return traversal."""
    if state.direction is not MovementDirection.OUTBOUND:
        raise MovementValidationError("player is not in outbound movement")
    required = outbound_sequence(layout, state.target_house_id)
    if required and state.current_house_id != required[-1]:
        raise MovementValidationError("outbound movement is not complete")
    if not required:
        return MovementState(
            direction=MovementDirection.RETURN,
            mode=MovementMode.HOPPING,
            one_leg=True,
            current_house_id=None,
            position=None,
            target_house_id=state.target_house_id,
            visited_house_ids=state.visited_house_ids,
        )
    return MovementState(
        direction=MovementDirection.RETURN,
        mode=MovementMode.HOPPING,
        one_leg=True,
        current_house_id=state.current_house_id,
        position=state.position,
        target_house_id=state.target_house_id,
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
