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


def make_state(player_count: int = 2) -> GameState:
    geometry = HouseGeometry(
        boundary=(Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10), Point(0, 0)),
        bounds=Bounds(0, 0, 10, 10),
    )
    houses = tuple(
        House(id=f"h{i}", number=i, sequence_index=i - 1, geometry=geometry) for i in range(1, 4)
    )
    layout = Layout(id="full-loop", type=LayoutType.HEART, houses=houses)
    players = tuple(
        Player(id=f"p{i}", name=f"Player {i}", stone_id=f"s{i}", order=i - 1)
        for i in range(1, player_count + 1)
    )
    stones = tuple(Stone(id=f"s{i}", owner_id=f"p{i}") for i in range(1, player_count + 1))
    return GameState.initial(layout, players, stones, GameConfig())


def complete_house(
    state: GameState,
    target: str,
    path: tuple[str, ...],
    claim_success: bool = True,
) -> GameState:
    state = transition(state, GameAction.begin_turn(state.current_player_id or "p1")).state
    state = transition(state, GameAction.throw(target)).state
    state = transition(state, GameAction.resolve_throw(True)).state
    state = transition(state, GameAction.begin_hopping_out(path)).state

    for house_id in path:
        state = transition(state, GameAction.hop(house_id, Point(5, 5))).state

    state = transition(state, GameAction.begin_hopping_back()).state
    for house_id in reversed(path):
        state = transition(state, GameAction.hop(house_id, Point(5, 5))).state
    state = transition(state, GameAction.hop(target, Point(5, 5))).state
    state = transition(state, GameAction.pickup_stone()).state
    state = transition(state, GameAction.complete_house()).state
    state = transition(state, GameAction.select_claim(target, "facing")).state
    return transition(state, GameAction.resolve_claim(claim_success)).state


def test_complete_game_reaches_game_over_and_calculates_winner() -> None:
    state = transition(make_state(), GameAction.start_game()).state

    state = complete_house(state, "h1", ("h2", "h3"))
    assert state.phase is GamePhase.NEXT_HOUSE
    assert state.ownership == {"h1": "p1"}
    assert state.scores == {"p1": 1, "p2": 0}

    state = transition(state, GameAction.next_house()).state
    assert state.phase is GamePhase.TURN_START
    assert state.turn is not None
    assert state.turn.target_house_id == "h2"

    state = complete_house(state, "h2", ("h1", "h3"))
    state = transition(state, GameAction.next_house()).state
    state = complete_house(state, "h3", ("h1", "h2"))

    assert state.phase is GamePhase.GAME_OVER
    assert state.ownership == {"h1": "p1", "h2": "p1", "h3": "p1"}
    assert state.scores == {"p1": 3, "p2": 0}
    assert state.winner.is_final is True
    assert state.winner.player_id == "p1"
    assert state.winner.tied_player_ids == ()


def test_failed_turn_moves_to_next_player_and_preserves_progress() -> None:
    state = transition(make_state(), GameAction.start_game()).state
    state = transition(state, GameAction.begin_turn("p1")).state
    state = transition(state, GameAction.throw("h1")).state
    state = transition(state, GameAction.resolve_throw(False, "stone_touched_boundary")).state

    assert state.phase is GamePhase.TURN_END
    assert state.turn is not None
    assert state.turn.failed is True
    assert state.ownership == {}

    state = transition(state, GameAction.end_turn()).state
    assert state.phase is GamePhase.NEXT_PLAYER
    assert state.round.completed_turns == 1

    state = transition(state, GameAction.next_player()).state
    assert state.phase is GamePhase.TURN_START
    assert state.current_player_id == "p2"
    assert state.round.number == 1

    state = transition(state, GameAction.begin_turn("p2")).state
    assert state.turn is not None
    assert state.turn.target_house_id == "h1"


def test_completed_turns_advance_round_after_last_player() -> None:
    state = transition(make_state(), GameAction.start_game()).state

    for player_id in ("p1", "p2"):
        state = transition(state, GameAction.begin_turn(player_id)).state
        state = transition(state, GameAction.throw("h1")).state
        state = transition(state, GameAction.resolve_throw(False, "missed_target")).state
        state = transition(state, GameAction.end_turn()).state
        state = transition(state, GameAction.next_player()).state

    assert state.round.number == 2
    assert state.current_player_id == "p1"
    assert state.phase is GamePhase.TURN_START
