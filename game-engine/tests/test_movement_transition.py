import pytest

from jumpup import (
    Bounds,
    GameAction,
    GameConfig,
    GameState,
    GamePhase,
    House,
    Layout,
    LayoutType,
    Player,
    Point,
    Stone,
    transition,
)
from jumpup.geometry import HouseGeometry


def make_state() -> GameState:
    geometry = HouseGeometry(
        boundary=(Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10), Point(0, 0)),
        bounds=Bounds(0, 0, 10, 10),
    )
    layout = Layout(
        id="movement-transition",
        type=LayoutType.HEART,
        houses=tuple(
            House(id=f"h{i}", number=i, sequence_index=i - 1, geometry=geometry)
            for i in range(1, 4)
        ),
    )
    players = (
        Player(id="p1", name="Player 1", stone_id="s1", order=0),
        Player(id="p2", name="Player 2", stone_id="s2", order=1),
    )
    stones = (
        Stone(id="s1", owner_id="p1"),
        Stone(id="s2", owner_id="p2"),
    )
    return GameState.initial(layout, players, stones, GameConfig())


def start_hopping() -> GameState:
    state = make_state()
    for action in (
        GameAction.start_game(),
        GameAction.begin_turn("p1"),
        GameAction.throw("h1"),
        GameAction.resolve_throw(True),
    ):
        state = transition(state, action).state
    return state


def test_transition_requires_explicit_layout_path() -> None:
    state = start_hopping()
    with pytest.raises(ValueError, match="explicit layout-specific movement path"):
        transition(state, GameAction.begin_hopping_out())


def test_transition_accepts_explicit_path_and_valid_hops() -> None:
    state = start_hopping()
    state = transition(state, GameAction.begin_hopping_out(("h2", "h3"))).state
    state = transition(state, GameAction.hop("h2", Point(5, 5))).state
    state = transition(state, GameAction.hop("h3", Point(5, 5))).state
    state = transition(state, GameAction.begin_hopping_back()).state
    state = transition(state, GameAction.hop("h2", Point(5, 5))).state
    state = transition(state, GameAction.hop("h1", Point(5, 5))).state

    assert state.phase is GamePhase.HOPPING_BACK
    assert state.turn is not None
    assert state.turn.movement is not None
    assert state.turn.movement.current_house_id == "h1"


def test_transition_movement_violation_fails_turn() -> None:
    state = start_hopping()
    state = transition(state, GameAction.begin_hopping_out(("h2", "h3"))).state
    state = transition(state, GameAction.hop("h3", Point(5, 5))).state

    assert state.phase is GamePhase.TURN_END
    assert state.turn is not None
    assert state.turn.failed is True
    assert "expected house h2" in (state.turn.failure_reason or "")
