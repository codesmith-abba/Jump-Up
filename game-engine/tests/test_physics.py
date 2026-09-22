from jumpup.geometry import Bounds, HouseGeometry, Point
from jumpup.physics import (
    PhysicsConfig,
    StoneInitialState,
    ThrowStatus,
    point_inside_strict,
    simulate_throw,
)


def square_house(size: float = 10) -> HouseGeometry:
    return HouseGeometry(
        boundary=(Point(0, 0), Point(size, 0), Point(size, size), Point(0, size), Point(0, 0)),
        bounds=Bounds(0, 0, size, size),
    )


VALID_AREA = Bounds(-20, -20, 20, 20)
TARGET = square_house()


def initial_for_contact(x: float, y: float) -> StoneInitialState:
    return StoneInitialState(
        position=Point(x, y), height=1.0,
        velocity_x=0.0, velocity_y=0.0, velocity_z=0.0,
    )


def test_point_inside_strict_rejects_boundary_and_accepts_interior() -> None:
    assert point_inside_strict(Point(5, 5), TARGET)
    assert not point_inside_strict(Point(0, 5), TARGET)
    assert not point_inside_strict(Point(10, 5), TARGET)
    assert not point_inside_strict(Point(0, 0), TARGET)


def test_successful_throw_lands_inside_target() -> None:
    result = simulate_throw(
        initial_for_contact(5, 5), target_house_id="h1",
        target_house=TARGET, valid_area=VALID_AREA,
    )
    assert result.status is ThrowStatus.SUCCEEDED
    assert result.throw_succeeded
    assert result.throw_complete
    assert result.landed_house_id == "h1"
    assert result.state.position == Point(5, 5)
    assert result.state.height == 0
    assert result.collision_count == 1


def test_target_boundary_touch_is_failure() -> None:
    result = simulate_throw(
        initial_for_contact(0, 5), target_house_id="h1",
        target_house=TARGET, valid_area=VALID_AREA,
    )
    assert result.status is ThrowStatus.FAILED_BOUNDARY
    assert result.boundary_touched
    assert not result.throw_succeeded


def test_outer_valid_area_boundary_touch_is_failure() -> None:
    result = simulate_throw(
        StoneInitialState(
            position=Point(20, 5), height=0.5,
            velocity_x=0.0, velocity_y=0.0, velocity_z=0.0,
        ),
        target_house_id="h1", target_house=TARGET, valid_area=VALID_AREA,
    )
    assert result.status is ThrowStatus.FAILED_BOUNDARY
    assert result.boundary_touched


def test_stone_leaving_valid_area_is_detected_before_board_contact() -> None:
    result = simulate_throw(
        StoneInitialState(
            position=Point(0, 0), height=2,
            velocity_x=100, velocity_y=0, velocity_z=0,
        ),
        target_house_id="h1", target_house=TARGET, valid_area=VALID_AREA,
        config=PhysicsConfig(time_step=0.01),
    )
    assert result.status is ThrowStatus.FAILED_OUTSIDE_VALID_AREA
    assert result.left_valid_area


def test_bounce_is_deterministic_and_configurable() -> None:
    initial = StoneInitialState(
        position=Point(15, 15), height=2,
        velocity_x=0, velocity_y=0, velocity_z=0,
    )
    config = PhysicsConfig(
        gravity=10, restitution=0.5, horizontal_damping=0.9,
        time_step=0.01, max_bounces=2,
    )
    first = simulate_throw(
        initial, target_house_id="h1", target_house=TARGET,
        valid_area=VALID_AREA, config=config,
    )
    second = simulate_throw(
        initial, target_house_id="h1", target_house=TARGET,
        valid_area=VALID_AREA, config=config,
    )
    assert first == second
    assert first.state.bounces == 2
    assert first.collision_count == 3
    assert first.status is ThrowStatus.FAILED_RESTING_OUTSIDE_TARGET


def test_target_hit_after_vertical_trajectory_is_deterministic() -> None:
    initial = StoneInitialState(
        position=Point(5, 5), height=2,
        velocity_x=0, velocity_y=0, velocity_z=0,
    )
    result = simulate_throw(
        initial, target_house_id="h1", target_house=TARGET,
        valid_area=VALID_AREA, config=PhysicsConfig(gravity=10, time_step=0.01),
    )
    assert result.status is ThrowStatus.SUCCEEDED
    assert result.state.position == Point(5, 5)
    assert result.state.height == 0


def test_timeout_is_deterministic_when_bounces_do_not_rest() -> None:
    config = PhysicsConfig(
        gravity=10, restitution=1, horizontal_damping=1,
        time_step=0.1, max_time=0.2, max_bounces=100,
    )
    result = simulate_throw(
        StoneInitialState(
            position=Point(15, 15), height=1,
            velocity_x=0, velocity_y=0, velocity_z=0,
        ),
        target_house_id="h1", target_house=TARGET,
        valid_area=VALID_AREA, config=config,
    )
    assert result.status is ThrowStatus.FAILED_TIMEOUT
    assert not result.throw_complete


def test_physics_config_rejects_invalid_parameters() -> None:
    for kwargs in (
        {"gravity": 0},
        {"restitution": 1.1},
        {"horizontal_damping": 0},
        {"time_step": 0},
        {"max_bounces": -1},
    ):
        try:
            PhysicsConfig(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kwargs}")
