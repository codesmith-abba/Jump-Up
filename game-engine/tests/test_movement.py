import pytest

from jumpup import (
    Bounds,
    House,
    Layout,
    LayoutType,
    MovementDirection,
    MovementMode,
    MovementValidationError,
    Point,
    begin_hopping,
    begin_return,
    can_pickup_stone,
    hop,
    validate_movement_path,
)
from jumpup.geometry import HouseGeometry


def make_layout(count: int = 4) -> Layout:
    geometry = HouseGeometry(
        boundary=(Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10), Point(0, 0)),
        bounds=Bounds(0, 0, 10, 10),
    )
    return Layout(
        id="movement-test",
        type=LayoutType.HEART,
        houses=tuple(
            House(id=f"h{i}", number=i, sequence_index=i - 1, geometry=geometry)
            for i in range(1, count + 1)
        ),
    )


PATH = ("h1", "h3", "h4")


def test_explicit_path_is_required_and_validated() -> None:
    layout = make_layout()
    validate_movement_path(layout, "h2", PATH)

    with pytest.raises(MovementValidationError, match="skip"):
        validate_movement_path(layout, "h2", ("h1", "h2", "h3"))

    with pytest.raises(MovementValidationError, match="unknown"):
        validate_movement_path(layout, "h2", ("h1", "h9"))


def test_begin_hopping_starts_on_one_leg_without_inventing_start_position() -> None:
    state = begin_hopping(make_layout(), "h2", PATH)
    assert state.direction is MovementDirection.OUTBOUND
    assert state.mode is MovementMode.HOPPING
    assert state.one_leg is True
    assert state.current_house_id is None
    assert state.position is None
    assert state.required_outbound_house_ids == PATH
    assert state.return_house_ids == ("h4", "h3", "h1", "h2")


def test_hop_follows_explicit_outbound_sequence() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)
    for house_id in PATH:
        state = hop(state, layout, house_id, Point(5, 5))

    assert state.current_house_id == "h4"
    assert state.visited_house_ids == PATH
    assert state.hopping is True
    assert state.one_leg is True


def test_stone_house_cannot_be_landed_on_outbound() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)
    state = hop(state, layout, "h1", Point(5, 5))

    with pytest.raises(MovementValidationError):
        hop(state, layout, "h2", Point(5, 5))


def test_wrong_house_order_is_rejected() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)

    with pytest.raises(MovementValidationError, match="expected house h1"):
        hop(state, layout, "h3", Point(5, 5))


def test_boundary_touch_is_rejected() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)

    with pytest.raises(MovementValidationError, match="boundary"):
        hop(state, layout, "h1", Point(0, 5))


def test_outside_house_is_rejected() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)

    with pytest.raises(MovementValidationError, match="outside"):
        hop(state, layout, "h1", Point(11, 5))


def test_both_feet_are_rejected_in_unowned_house() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)

    with pytest.raises(MovementValidationError, match="owned house"):
        hop(
            state,
            layout,
            "h1",
            Point(5, 5),
            feet=2,
            ownership={"h3": "p1"},
            player_id="p1",
        )


def test_both_feet_are_allowed_in_owned_house() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)
    state = hop(
        state,
        layout,
        "h1",
        Point(5, 5),
        feet=2,
        ownership={"h1": "p1"},
        player_id="p1",
    )

    assert state.mode is MovementMode.RESTING
    assert state.both_feet is True
    assert state.one_leg is False


def test_owned_house_rest_does_not_break_sequence() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)
    state = hop(
        state,
        layout,
        "h1",
        Point(5, 5),
        feet=2,
        ownership={"h1": "p1"},
        player_id="p1",
    )
    state = hop(state, layout, "h3", Point(5, 5))

    assert state.current_house_id == "h3"
    assert state.mode is MovementMode.HOPPING
    assert state.one_leg is True


def test_return_sequence_ends_at_stone_house() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)
    for house_id in PATH:
        state = hop(state, layout, house_id, Point(5, 5))
    state = begin_return(state)

    for house_id in ("h4", "h3", "h1", "h2"):
        state = hop(state, layout, house_id, Point(5, 5))

    assert state.direction is MovementDirection.RETURN
    assert state.current_house_id == "h2"
    assert can_pickup_stone(state)


def test_return_cannot_begin_before_outbound_is_complete() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)
    state = hop(state, layout, "h1", Point(5, 5))

    with pytest.raises(MovementValidationError, match="not complete"):
        begin_return(state)


def test_pickup_requires_return_one_leg_at_target() -> None:
    layout = make_layout()
    state = begin_hopping(layout, "h2", PATH)
    for house_id in PATH:
        state = hop(state, layout, house_id, Point(5, 5))
    state = begin_return(state)

    assert can_pickup_stone(state) is False
    state = hop(state, layout, "h4", Point(5, 5))
    state = hop(state, layout, "h3", Point(5, 5))
    state = hop(state, layout, "h1", Point(5, 5))
    state = hop(state, layout, "h2", Point(5, 5))
    assert can_pickup_stone(state) is True
