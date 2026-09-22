import json

import pytest

from jumpup import (
    GameAction,
    GameConfig,
    GamePhase,
    GameState,
    House,
    InvalidTransitionError,
    Layout,
    LayoutType,
    Player,
    Point,
    Stone,
    transition,
)
from jumpup.geometry import Bounds, HouseGeometry


def make_state(player_count: int = 2) -> GameState:
    geometry = HouseGeometry(
        boundary=(Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10), Point(0, 0)),
        bounds=Bounds(0, 0, 10, 10),
    )
    houses = tuple(
        House(id=f"h{i}", number=i, sequence_index=i - 1, geometry=geometry)
        for i in range(1, 4)
    )
    layout = Layout(id="test-layout", type=LayoutType.HEART, houses=houses)
    players = tuple(
        Player(
            id=f"p{i}",
            name=f"Player {i}",
            stone_id=f"s{i}",
            order=i - 1,
        )
        for i in range(1, player_count + 1)
    )
    stones = tuple(Stone(id=f"s{i}", owner_id=f"p{i}") for i in range(1, player_count + 1))
    return GameState.initial(layout, players, stones, GameConfig())


def advance_to_claim_selection(state: GameState) -> GameState:
    actions = (
        GameAction.start_game(),
        GameAction.begin_turn("p1"),
        GameAction.throw("h1"),
        GameAction.resolve_throw(True),
        GameAction.begin_hopping_out(),
        GameAction.hop("h2", Point(5, 5)),
        GameAction.hop("h3", Point(5, 5)),
        GameAction.begin_hopping_back(),
        GameAction.hop("h2", Point(5, 5)),
        GameAction.hop("h1", Point(5, 5)),
        GameAction.pickup_stone(),
        GameAction.complete_house(),
    )
    for action in actions:
        state = transition(state, action).state
    return state


def test_initial_state() -> None:
    state = make_state()
    assert state.phase is GamePhase.SETUP
    assert state.current_player_id is None
    assert state.turn is None
    assert state.round.number == 1
    assert state.ownership == {}
    assert state.winner.is_final is False


def test_player_creation() -> None:
    state = make_state()
    assert [player.id for player in state.players] == ["p1", "p2"]
    assert [player.name for player in state.players] == ["Player 1", "Player 2"]


def test_each_player_has_a_stone() -> None:
    state = make_state()
    assert [player.stone_id for player in state.players] == ["s1", "s2"]
    assert [stone.owner_id for stone in state.stones] == ["p1", "p2"]


def test_turn_initialization() -> None:
    state = transition(make_state(), GameAction.start_game()).state
    state = transition(state, GameAction.begin_turn("p1")).state

    assert state.phase is GamePhase.THROW
    assert state.current_player_id == "p1"
    assert state.turn is not None
    assert state.turn.current_house_id == "h1"
    assert state.turn.target_house_id == "h1"
    assert state.turn.stone_id == "s1"
    assert state.turn.movement is None


def test_explicit_lifecycle_transitions() -> None:
    state = transition(make_state(), GameAction.start_game()).state
    state = transition(state, GameAction.begin_turn("p1")).state
    state = transition(state, GameAction.throw("h1")).state
    assert state.phase is GamePhase.THROW_RESOLUTION

    state = transition(state, GameAction.resolve_throw(True)).state
    assert state.phase is GamePhase.HOPPING_OUT
    assert state.stones[0].in_hand is False
    assert state.stones[0].location_house_id == "h1"

    state = transition(state, GameAction.begin_hopping_out()).state
    assert state.phase is GamePhase.HOPPING_OUT
    assert state.turn is not None
    assert state.turn.movement is not None
    assert state.turn.movement.hopping is True
    assert state.turn.movement.current_house_id is None

    state = transition(state, GameAction.hop("h2", Point(5, 5))).state
    state = transition(state, GameAction.hop("h3", Point(5, 5))).state
    assert state.turn.movement is not None
    assert state.turn.movement.current_house_id == "h3"

    state = transition(state, GameAction.begin_hopping_back()).state
    assert state.phase is GamePhase.HOPPING_BACK
    state = transition(state, GameAction.hop("h2", Point(5, 5))).state
    state = transition(state, GameAction.hop("h1", Point(5, 5))).state

    state = transition(state, GameAction.pickup_stone()).state
    assert state.phase is GamePhase.HOUSE_COMPLETED
    assert state.stones[0].in_hand is True
    assert state.stones[0].location_house_id is None

    state = transition(state, GameAction.complete_house()).state
    assert state.phase is GamePhase.CLAIM_SELECTION


def test_successful_claim_is_authoritatively_recorded() -> None:
    state = advance_to_claim_selection(make_state())
    state = transition(state, GameAction.select_claim("h1", "facing")).state

    assert state.phase is GamePhase.CLAIM_RESOLUTION
    assert state.claim.selected_house_id == "h1"
    assert state.claim.selected_player_id == "p1"
    assert state.claim.selection_mode == "facing"

    state = transition(state, GameAction.resolve_claim(True)).state
    assert state.ownership == {"h1": "p1"}
    assert state.claim.resolved is True
    assert state.claim.successful is True
    assert state.phase is GamePhase.NEXT_HOUSE


def test_failed_claim_ends_turn_without_assigning_ownership() -> None:
    state = advance_to_claim_selection(make_state())
    state = transition(state, GameAction.select_claim("h1", "back_facing")).state
    state = transition(state, GameAction.resolve_claim(False)).state

    assert state.ownership == {}
    assert state.claim.successful is False
    assert state.phase is GamePhase.TURN_END


def test_failed_throw_ends_turn_and_records_reason() -> None:
    state = transition(make_state(), GameAction.start_game()).state
    state = transition(state, GameAction.begin_turn("p1")).state
    state = transition(state, GameAction.throw("h1")).state
    state = transition(
        state,
        GameAction.resolve_throw(False, "stone_outside_target"),
    ).state

    assert state.phase is GamePhase.TURN_END
    assert state.turn is not None
    assert state.turn.failed is True
    assert state.turn.failure_reason == "stone_outside_target"


def test_next_house_and_next_player_are_deterministic() -> None:
    state = advance_to_claim_selection(make_state())
    state = transition(state, GameAction.select_claim("h1", "facing")).state
    state = transition(state, GameAction.resolve_claim(True)).state
    state = transition(state, GameAction.next_house()).state

    assert state.phase is GamePhase.TURN_START
    assert state.turn is not None
    assert state.turn.current_house_id == "h2"
    assert state.turn.target_house_id == "h2"
    assert state.turn.movement is None

    state = transition(state, GameAction.end_game("p1")).state
    assert state.phase is GamePhase.GAME_OVER
    assert state.winner.player_id == "p1"
    assert state.winner.is_final is True


def test_invalid_transition_is_rejected() -> None:
    state = make_state()
    with pytest.raises(InvalidTransitionError):
        transition(state, GameAction.throw("h1"))


def test_wrong_current_player_cannot_begin_turn() -> None:
    state = transition(make_state(), GameAction.start_game()).state
    with pytest.raises(InvalidTransitionError):
        transition(state, GameAction.begin_turn("p2"))


def test_wrong_target_house_is_rejected() -> None:
    state = transition(make_state(), GameAction.start_game()).state
    state = transition(state, GameAction.begin_turn("p1")).state

    with pytest.raises(InvalidTransitionError):
        transition(state, GameAction.throw("h2"))


def test_owned_house_cannot_be_selected_for_claim() -> None:
    state = GameState(
        **{
            **make_state().__dict__,
            "phase": GamePhase.CLAIM_SELECTION,
            "current_player_id": "p1",
            "ownership": {"h1": "p2"},
        }
    )
    with pytest.raises(InvalidTransitionError):
        transition(state, GameAction.select_claim("h1", "facing"))


def test_claim_cannot_be_resolved_before_selection() -> None:
    state = GameState(
        **{
            **make_state().__dict__,
            "phase": GamePhase.CLAIM_RESOLUTION,
            "current_player_id": "p1",
        }
    )
    with pytest.raises(InvalidTransitionError):
        transition(state, GameAction.resolve_claim(True))


def test_invalid_model_references_are_rejected() -> None:
    houses = (
        House(
            id="h1",
            number=1,
            sequence_index=0,
            geometry=HouseGeometry(
                boundary=(Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1), Point(0, 0)),
                bounds=Bounds(0, 0, 1, 1),
            ),
        ),
    )
    layout = Layout(id="layout", type=LayoutType.SQUARE, houses=houses)
    player = Player(id="p1", name="Player 1", stone_id="missing", order=0)

    with pytest.raises(ValueError):
        GameState.initial(
            layout,
            (player,),
            (Stone(id="s1", owner_id="p1"),),
        )


def test_player_limit_is_enforced() -> None:
    houses = (
        House(
            id="h1",
            number=1,
            sequence_index=0,
            geometry=HouseGeometry(
                boundary=(Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1), Point(0, 0)),
                bounds=Bounds(0, 0, 1, 1),
            ),
        ),
    )
    layout = Layout(id="layout", type=LayoutType.SQUARE, houses=houses)
    players = tuple(Player(id=f"p{i}", name=f"P{i}", stone_id=f"s{i}", order=i) for i in range(5))
    stones = tuple(Stone(id=f"s{i}", owner_id=f"p{i}") for i in range(5))

    with pytest.raises(ValueError):
        GameState.initial(layout, players, stones)


def test_state_is_json_serializable() -> None:
    state = make_state()
    encoded = json.dumps(state.to_dict())

    assert '"phase": "setup"' in encoded
    assert '"layout":' in encoded
    assert '"players":' in encoded


def test_transition_does_not_mutate_previous_state() -> None:
    initial = make_state()
    started = transition(initial, GameAction.start_game()).state

    assert initial.phase is GamePhase.SETUP
    assert initial.current_player_id is None
    assert started.phase is GamePhase.TURN_START
    assert started.current_player_id == "p1"
