"""Deterministic, renderer-independent stone throw physics for Jump-Up."""

import math
from dataclasses import dataclass
from enum import Enum

from .geometry import Bounds, HouseGeometry, Point


class ThrowStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED_BOUNDARY = "failed_boundary"
    FAILED_OUTSIDE_VALID_AREA = "failed_outside_valid_area"
    FAILED_RESTING_OUTSIDE_TARGET = "failed_resting_outside_target"
    FAILED_TIMEOUT = "failed_timeout"


@dataclass(frozen=True)
class PhysicsConfig:
    """Explicit engineering parameters; these are not claims of historical physics."""

    gravity: float = 9.81
    restitution: float = 0.35
    horizontal_damping: float = 0.85
    time_step: float = 1.0 / 120.0
    max_time: float = 10.0
    max_bounces: int = 4
    rest_vertical_speed: float = 0.25
    boundary_epsilon: float = 1e-9

    def __post_init__(self) -> None:
        if self.gravity <= 0:
            raise ValueError("gravity must be positive")
        if not 0 <= self.restitution <= 1:
            raise ValueError("restitution must be between 0 and 1")
        if not 0 < self.horizontal_damping <= 1:
            raise ValueError("horizontal_damping must be in (0, 1]")
        if self.time_step <= 0 or self.max_time <= 0:
            raise ValueError("time_step and max_time must be positive")
        if self.max_bounces < 0:
            raise ValueError("max_bounces must be non-negative")
        if self.rest_vertical_speed < 0 or self.boundary_epsilon < 0:
            raise ValueError("rest_vertical_speed and boundary_epsilon must be non-negative")


@dataclass(frozen=True)
class StoneInitialState:
    position: Point
    height: float
    velocity_x: float
    velocity_y: float
    velocity_z: float

    def __post_init__(self) -> None:
        values = (
            self.position.x,
            self.position.y,
            self.height,
            self.velocity_x,
            self.velocity_y,
            self.velocity_z,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("initial state values must be finite")
        if self.height < 0:
            raise ValueError("height must be non-negative")


@dataclass(frozen=True)
class StonePhysicsState:
    position: Point
    height: float
    velocity_x: float
    velocity_y: float
    velocity_z: float
    elapsed_time: float
    bounces: int
    resting: bool


@dataclass(frozen=True)
class ThrowResult:
    status: ThrowStatus
    state: StonePhysicsState
    target_house_id: str
    landed_house_id: str | None
    boundary_touched: bool
    left_valid_area: bool
    collision_count: int

    @property
    def throw_succeeded(self) -> bool:
        return self.status is ThrowStatus.SUCCEEDED

    @property
    def throw_complete(self) -> bool:
        return self.state.resting or self.status is not ThrowStatus.FAILED_TIMEOUT


def _distance_to_segment(point: Point, start: Point, end: Point) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return math.hypot(point.x - start.x, point.y - start.y)
    projection = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    projection = max(0.0, min(1.0, projection))
    closest_x = start.x + projection * dx
    closest_y = start.y + projection * dy
    return math.hypot(point.x - closest_x, point.y - closest_y)


def point_on_boundary(point: Point, geometry: HouseGeometry, epsilon: float = 1e-9) -> bool:
    return any(
        _distance_to_segment(point, start, end) <= epsilon
        for start, end in zip(geometry.boundary, geometry.boundary[1:])
    )


def point_inside_strict(point: Point, geometry: HouseGeometry, epsilon: float = 1e-9) -> bool:
    """Point-in-polygon test where boundary points are explicitly outside."""
    if point_on_boundary(point, geometry, epsilon):
        return False
    inside = False
    vertices = geometry.boundary[:-1]
    for index, vertex in enumerate(vertices):
        next_vertex = vertices[(index + 1) % len(vertices)]
        if (vertex.y > point.y) != (next_vertex.y > point.y):
            intersection_x = (next_vertex.x - vertex.x) * (point.y - vertex.y) / (
                next_vertex.y - vertex.y
            ) + vertex.x
            if point.x < intersection_x:
                inside = not inside
    return inside


def _outside_bounds(point: Point, bounds: Bounds, epsilon: float) -> bool:
    return (
        point.x < bounds.min_x - epsilon
        or point.x > bounds.max_x + epsilon
        or point.y < bounds.min_y - epsilon
        or point.y > bounds.max_y + epsilon
    )


def _on_outer_boundary(point: Point, bounds: Bounds, epsilon: float) -> bool:
    return (
        abs(point.x - bounds.min_x) <= epsilon
        or abs(point.x - bounds.max_x) <= epsilon
        or abs(point.y - bounds.min_y) <= epsilon
        or abs(point.y - bounds.max_y) <= epsilon
    )


def _contact_point(
    previous: StonePhysicsState, next_height: float, next_x: float, next_y: float
) -> tuple[float, float, float]:
    denominator = previous.height - next_height
    if denominator <= 0:
        return next_x, next_y, 1.0
    fraction = max(0.0, min(1.0, previous.height / denominator))
    x = previous.position.x + (next_x - previous.position.x) * fraction
    y = previous.position.y + (next_y - previous.position.y) * fraction
    return x, y, fraction


def simulate_throw(
    initial: StoneInitialState,
    *,
    target_house_id: str,
    target_house: HouseGeometry,
    valid_area: Bounds,
    config: PhysicsConfig | None = None,
) -> ThrowResult:
    """Simulate a deterministic throw using fixed-timestep 3D projectile motion.

    x/y are board coordinates, z is height, and the board is z=0. A target
    landing must be strictly inside the target polygon. Target/outer-boundary
    contact fails; other valid-area contacts bounce until rest or bounce limit.
    """
    settings = config or PhysicsConfig()
    state = StonePhysicsState(
        position=initial.position,
        height=initial.height,
        velocity_x=initial.velocity_x,
        velocity_y=initial.velocity_y,
        velocity_z=initial.velocity_z,
        elapsed_time=0.0,
        bounces=0,
        resting=initial.height == 0 and initial.velocity_z <= 0,
    )

    if state.resting:
        inside_target = point_inside_strict(state.position, target_house, settings.boundary_epsilon)
        return ThrowResult(
            status=(
                ThrowStatus.SUCCEEDED
                if inside_target
                else ThrowStatus.FAILED_RESTING_OUTSIDE_TARGET
            ),
            state=state,
            target_house_id=target_house_id,
            landed_house_id=target_house_id if inside_target else None,
            boundary_touched=point_on_boundary(
                state.position, target_house, settings.boundary_epsilon
            ),
            left_valid_area=_outside_bounds(state.position, valid_area, settings.boundary_epsilon),
            collision_count=1,
        )

    max_steps = math.ceil(settings.max_time / settings.time_step)
    collision_count = 0

    for _ in range(max_steps):
        dt = settings.time_step
        next_vz = state.velocity_z - settings.gravity * dt
        next_height = state.height + state.velocity_z * dt - 0.5 * settings.gravity * dt * dt
        next_x = state.position.x + state.velocity_x * dt
        next_y = state.position.y + state.velocity_y * dt
        next_time = state.elapsed_time + dt

        if next_height > 0:
            state = StonePhysicsState(
                position=Point(next_x, next_y),
                height=next_height,
                velocity_x=state.velocity_x,
                velocity_y=state.velocity_y,
                velocity_z=next_vz,
                elapsed_time=next_time,
                bounces=state.bounces,
                resting=False,
            )
            if _outside_bounds(state.position, valid_area, settings.boundary_epsilon):
                return ThrowResult(
                    ThrowStatus.FAILED_OUTSIDE_VALID_AREA,
                    state,
                    target_house_id,
                    None,
                    False,
                    True,
                    collision_count,
                )
            continue

        contact_x, contact_y, fraction = _contact_point(state, next_height, next_x, next_y)
        contact = Point(contact_x, contact_y)
        contact_time = state.elapsed_time + dt * fraction
        contact_vz = state.velocity_z - settings.gravity * dt * fraction
        collision_count += 1

        if _outside_bounds(contact, valid_area, settings.boundary_epsilon):
            contact_state = StonePhysicsState(
                contact,
                0.0,
                state.velocity_x,
                state.velocity_y,
                contact_vz,
                contact_time,
                state.bounces,
                True,
            )
            return ThrowResult(
                ThrowStatus.FAILED_OUTSIDE_VALID_AREA,
                contact_state,
                target_house_id,
                None,
                False,
                True,
                collision_count,
            )

        boundary_touched = point_on_boundary(
            contact, target_house, settings.boundary_epsilon
        ) or _on_outer_boundary(contact, valid_area, settings.boundary_epsilon)
        if boundary_touched:
            contact_state = StonePhysicsState(
                contact,
                0.0,
                state.velocity_x,
                state.velocity_y,
                contact_vz,
                contact_time,
                state.bounces,
                True,
            )
            return ThrowResult(
                ThrowStatus.FAILED_BOUNDARY,
                contact_state,
                target_house_id,
                None,
                True,
                False,
                collision_count,
            )

        if point_inside_strict(contact, target_house, settings.boundary_epsilon):
            contact_state = StonePhysicsState(
                contact,
                0.0,
                state.velocity_x,
                state.velocity_y,
                0.0,
                contact_time,
                state.bounces,
                True,
            )
            return ThrowResult(
                ThrowStatus.SUCCEEDED,
                contact_state,
                target_house_id,
                target_house_id,
                False,
                False,
                collision_count,
            )

        if state.bounces >= settings.max_bounces or abs(contact_vz) <= settings.rest_vertical_speed:
            contact_state = StonePhysicsState(
                contact,
                0.0,
                state.velocity_x * settings.horizontal_damping,
                state.velocity_y * settings.horizontal_damping,
                0.0,
                contact_time,
                state.bounces,
                True,
            )
            return ThrowResult(
                ThrowStatus.FAILED_RESTING_OUTSIDE_TARGET,
                contact_state,
                target_house_id,
                None,
                False,
                False,
                collision_count,
            )

        state = StonePhysicsState(
            contact,
            0.0,
            state.velocity_x * settings.horizontal_damping,
            state.velocity_y * settings.horizontal_damping,
            -contact_vz * settings.restitution,
            contact_time,
            state.bounces + 1,
            False,
        )

    return ThrowResult(
        ThrowStatus.FAILED_TIMEOUT,
        state,
        target_house_id,
        None,
        False,
        _outside_bounds(state.position, valid_area, settings.boundary_epsilon),
        collision_count,
    )
