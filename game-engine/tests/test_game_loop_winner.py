from jumpup import (
    Bounds,
    GameAction,
    GameConfig,
    GamePhase,
    GameState,
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
    houses = tuple(
        House(id=f"h{i}", number=i, sequence_index=i - 1, geometry=geometry) for i in range(1, 2)
    )
    layout = Layout(id="winner-test", type=LayoutType.HEART, houses=houses)
    players = (
        Player(id="p1", name="Player 1", stone_id="s1", order=0),
        Player(id="p2", name="Player 2", stone_id="s2", order=1),
    )
    stones = (Stone(id="s1", owner_id="p1"), Stone(id="s2", owner_id="p2"))
    return GameState.initial(layout, players, stones, GameConfig())


def test_end_game_without_override_calculates_tie() -> None:
    state = make_state()
    state = GameState(**{**state.__dict__, "ownership": {"h1": "p1"}})
    state = transition(state, GameAction.start_game()).state
    state = transition(state, GameAction.end_game()).state

    assert state.phase is GamePhase.GAME_OVER
    assert state.winner.player_id == "p1"
    assert state.winner.tied_player_ids == ()


def test_end_game_calculates_true_tie() -> None:
    state = make_state()
    state = GameState(**{**state.__dict__, "ownership": {"h1": "p1"}})
    state = transition(state, GameAction.start_game()).state
    state = transition(state, GameAction.end_game()).state

    assert state.scores == {"p1": 1, "p2": 0}
    assert state.winner.player_id == "p1"
    assert state.winner.tied_player_ids == ()
